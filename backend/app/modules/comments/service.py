import json
from typing import List, Optional
from datetime import datetime, timedelta
import markdown
from redis.asyncio import Redis
from tortoise.exceptions import DoesNotExist, IntegrityError

from app.common.exceptions import (
    BusinessException,
    NotFoundException,
    BadRequestException,
    ForbiddenException,
)
from app.core.security import generate_guest_token
from app.modules.comments.models import GuestIdentity, Comment
from app.modules.comments.schemas import CommentCreate, CommentOut, GuestIdentityOut
from app.modules.articles.models import Article
from app.modules.system.models import SensitiveWord, SiteConfig, OperationLog
from app.modules.auth.models import AdminUser


async def get_or_create_guest(
    guest_token: Optional[str], ip: str, user_agent: str
) -> GuestIdentity:
    if guest_token:
        guest = await GuestIdentity.get_or_none(guest_token=guest_token)
        if guest:
            return guest
    
    new_token = generate_guest_token()
    guest = await GuestIdentity.create(
        guest_token=new_token,
        ip_address=ip,
        user_agent=user_agent,
    )
    return guest


async def set_guest_nickname(guest_token: str, nickname: str) -> GuestIdentity:
    guest = await GuestIdentity.get_or_none(guest_token=guest_token)
    if not guest:
        raise NotFoundException("游客身份不存在")
    
    existing = await GuestIdentity.filter(nickname=nickname).exclude(id=guest.id).first()
    if existing:
        raise BadRequestException("昵称已被使用")
    
    guest.nickname = nickname
    await guest.save()
    return guest


async def check_guest_banned(guest: GuestIdentity):
    if guest.is_banned:
        raise ForbiddenException(f"您已被封禁：{guest.ban_reason or '违反社区规范'}")


async def get_sensitive_words_from_cache(redis: Redis) -> List[str]:
    cache_key = "sensitive_words:list"
    cached = await redis.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    words = await SensitiveWord.filter(is_active=True).values_list("word", flat=True)
    word_list = list(words)
    
    await redis.setex(cache_key, 3600, json.dumps(word_list))
    return word_list


async def filter_sensitive_words(content: str, redis: Redis) -> str:
    words = await get_sensitive_words_from_cache(redis)
    
    for word in words:
        if word in content:
            raise BadRequestException(f"内容包含敏感词：{word}")
    
    return content


async def check_comment_rate_limit(guest_token: str, redis: Redis) -> bool:
    key = f"comment_rate_limit:{guest_token}"
    window = 60
    limit = 5
    
    now = datetime.now().timestamp()
    
    await redis.zremrangebyscore(key, 0, now - window)
    
    count = await redis.zcard(key)
    if count >= limit:
        raise BusinessException(429, "评论过于频繁，请稍后再试")
    
    await redis.zadd(key, {str(now): now})
    await redis.expire(key, window)
    
    return True


async def render_markdown_content(content: str) -> str:
    md = markdown.Markdown(
        extensions=[
            'extra',
            'codehilite',
            'nl2br',
            'sane_lists',
        ]
    )
    return md.convert(content)


async def check_comment_auto_approve(redis: Redis) -> bool:
    cache_key = "site_config:comment_auto_approve"
    cached = await redis.get(cache_key)
    
    if cached is not None:
        return cached == "true"
    
    config = await SiteConfig.get_or_none(key="comment_auto_approve")
    auto_approve = config.value == "true" if config else True
    
    await redis.setex(cache_key, 300, "true" if auto_approve else "false")
    return auto_approve


async def create_comment(
    data: CommentCreate, guest: GuestIdentity, redis: Redis
) -> Comment:
    await check_guest_banned(guest)
    
    await check_comment_rate_limit(guest.guest_token, redis)
    
    article = await Article.get_or_none(id=data.article_id)
    if not article:
        raise NotFoundException("文章不存在")
    
    if not article.allow_comment:
        raise BadRequestException("该文章不允许评论")
    
    await filter_sensitive_words(data.content, redis)
    
    reply_to_nickname = None
    if data.parent_id:
        parent = await Comment.get_or_none(id=data.parent_id)
        if not parent:
            raise NotFoundException("父评论不存在")
        if parent.article_id != data.article_id:
            raise BadRequestException("父评论不属于该文章")
        if parent.parent_id is not None:
            raise BadRequestException("不支持多层嵌套回复")
        
        parent_guest = await parent.guest
        reply_to_nickname = parent_guest.nickname or f"游客{parent_guest.id}"
    
    rendered_content = await render_markdown_content(data.content)
    
    auto_approve = await check_comment_auto_approve(redis)
    status = Comment.STATUS_APPROVED if auto_approve else Comment.STATUS_PENDING
    
    comment = await Comment.create(
        article_id=data.article_id,
        guest=guest,
        parent_id=data.parent_id,
        reply_to_nickname=reply_to_nickname,
        content=data.content,
        rendered_content=rendered_content,
        status=status,
        ip_address=guest.ip_address,
    )
    
    return comment


async def list_comments_for_article(
    article_id: int, page: int = 1, page_size: int = 20
) -> tuple[List[Comment], int]:
    article = await Article.get_or_none(id=article_id)
    if not article:
        raise NotFoundException("文章不存在")
    
    query = Comment.filter(
        article_id=article_id,
        status=Comment.STATUS_APPROVED,
        parent_id=None,
    ).order_by("-is_pinned", "-created_at")
    
    total = await query.count()
    
    offset = (page - 1) * page_size
    comments = await query.offset(offset).limit(page_size).prefetch_related("guest")
    
    return comments, total


async def list_comments_admin(
    status: Optional[str] = None,
    article_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[Comment], int]:
    query = Comment.all()
    
    if status:
        query = query.filter(status=status)
    
    if article_id:
        query = query.filter(article_id=article_id)
    
    if keyword:
        query = query.filter(content__icontains=keyword)
    
    query = query.order_by("-created_at")
    
    total = await query.count()
    
    offset = (page - 1) * page_size
    comments = await query.offset(offset).limit(page_size).prefetch_related("guest", "article")
    
    return list(comments), total


async def admin_action_comment(
    comment_id: int,
    action: str,
    admin: AdminUser,
    reason: Optional[str] = None,
) -> Comment:
    comment = await Comment.get_or_none(id=comment_id)
    if not comment:
        raise NotFoundException("评论不存在")
    
    old_status = comment.status
    old_pinned = comment.is_pinned
    
    if action == "pin":
        comment.is_pinned = True
    elif action == "unpin":
        comment.is_pinned = False
    elif action == "approve":
        comment.status = Comment.STATUS_APPROVED
    elif action == "hide":
        comment.status = Comment.STATUS_HIDDEN
    elif action == "delete":
        comment.status = Comment.STATUS_DELETED
    else:
        raise BadRequestException("无效的操作")
    
    await comment.save()
    
    await OperationLog.create(
        operator=admin.username,
        action=f"comment_{action}",
        target_type="comment",
        target_id=comment.id,
        detail=f"操作: {action}, 原因: {reason or '无'}, 状态变更: {old_status} -> {comment.status}, 置顶: {old_pinned} -> {comment.is_pinned}",
        ip_address="127.0.0.1",
        result="success",
    )
    
    return comment


async def admin_reply_comment(
    comment_id: int, content: str, admin: AdminUser
) -> Comment:
    comment = await Comment.get_or_none(id=comment_id)
    if not comment:
        raise NotFoundException("评论不存在")
    
    comment.admin_reply = content
    await comment.save()
    
    await OperationLog.create(
        operator=admin.username,
        action="comment_reply",
        target_type="comment",
        target_id=comment.id,
        detail=f"回复内容: {content[:100]}",
        ip_address="127.0.0.1",
        result="success",
    )
    
    return comment


async def convert_comment_to_out(comment: Comment) -> CommentOut:
    guest = await comment.guest
    
    guest_out = GuestIdentityOut(
        id=guest.id,
        guest_token=guest.guest_token,
        nickname=guest.nickname,
        created_at=guest.created_at,
    )
    
    replies_out = []
    reply_items = await Comment.filter(
        parent_id=comment.id,
        status=Comment.STATUS_APPROVED,
    ).order_by("created_at").prefetch_related("guest")

    for reply in reply_items:
        reply_guest = await reply.guest
        reply_guest_out = GuestIdentityOut(
            id=reply_guest.id,
            guest_token=reply_guest.guest_token,
            nickname=reply_guest.nickname,
            created_at=reply_guest.created_at,
        )
        replies_out.append(
            CommentOut(
                id=reply.id,
                article_id=reply.article_id,
                guest=reply_guest_out,
                parent_id=reply.parent_id,
                reply_to_nickname=reply.reply_to_nickname,
                content=reply.content,
                rendered_content=reply.rendered_content,
                status=reply.status,
                is_pinned=reply.is_pinned,
                admin_reply=reply.admin_reply,
                created_at=reply.created_at,
                replies=[],
            )
        )
    
    return CommentOut(
        id=comment.id,
        article_id=comment.article_id,
        guest=guest_out,
        parent_id=comment.parent_id,
        reply_to_nickname=comment.reply_to_nickname,
        content=comment.content,
        rendered_content=comment.rendered_content,
        status=comment.status,
        is_pinned=comment.is_pinned,
        admin_reply=comment.admin_reply,
        created_at=comment.created_at,
        replies=replies_out,
    )
