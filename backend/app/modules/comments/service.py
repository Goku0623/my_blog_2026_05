import asyncio
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
from app.modules.system.models import OperationLog
from app.modules.system.service import SensitiveWordService, FeatureSwitchService
from app.modules.auth.models import AdminUser


def build_guest_display_name(guest: GuestIdentity) -> str:
    if guest.nickname:
        return guest.nickname
    token_seed = (guest.guest_token or "").replace("-", "").upper()
    short_code = token_seed[:6] if token_seed else "ANON"
    return f"游客{short_code}"


async def resolve_guest_display_name(guest: GuestIdentity) -> str:
    """
    管理员回复评论时，GuestIdentity 可能因昵称唯一约束被加后缀（如 _2）。
    展示层应优先显示当前管理员用户名，避免暴露内部兜底昵称。
    """
    token = guest.guest_token or ""
    if token.startswith("admin-"):
        admin_id_str = token.removeprefix("admin-")
        if admin_id_str.isdigit():
            admin = await AdminUser.get_or_none(id=int(admin_id_str))
            if admin and admin.username:
                return admin.username
    return build_guest_display_name(guest)


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
    # 复用系统模块的统一缓存 key，避免后台刷新后评论侧读到旧缓存。
    words = await SensitiveWordService.get_sensitive_words_cached()
    return list(words)


async def filter_sensitive_words(content: str, redis: Redis) -> str:
    words = await get_sensitive_words_from_cache(redis)

    normalized_content = content.lower()
    for word in words:
        clean_word = word.strip()
        if clean_word and clean_word.lower() in normalized_content:
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


async def create_comment(
    data: CommentCreate, guest: GuestIdentity, redis: Redis, admin: Optional[AdminUser] = None
) -> Comment:
    if not await FeatureSwitchService.is_comment_enabled():
        raise BadRequestException("评论功能已关闭")

    await check_guest_banned(guest)

    if admin:
        # 管理员发表评论统一绑定到 admin-{id} 身份，避免沿用旧游客昵称导致展示不一致。
        admin_guest_token = f"admin-{admin.id}"
        admin_guest = await GuestIdentity.get_or_none(guest_token=admin_guest_token)

        if not admin_guest:
            nickname_base = admin.username.strip() or "管理员"
            nickname = nickname_base
            suffix = 1
            while await GuestIdentity.filter(nickname=nickname).exclude(guest_token=admin_guest_token).exists():
                suffix += 1
                nickname = f"{nickname_base}_{suffix}"

            admin_guest = await GuestIdentity.create(
                guest_token=admin_guest_token,
                nickname=nickname,
                ip_address=guest.ip_address,
                user_agent=guest.user_agent or "system-admin-comment",
            )
        else:
            # 复用管理员身份时更新最近来源信息，便于审计。
            admin_guest.ip_address = guest.ip_address
            admin_guest.user_agent = guest.user_agent
            await admin_guest.save()

        guest = admin_guest
    
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
        reply_to_nickname = build_guest_display_name(parent_guest)
    
    rendered_content = await render_markdown_content(data.content)
    
    comment = await Comment.create(
        article_id=data.article_id,
        guest=guest,
        parent_id=data.parent_id,
        reply_to_nickname=reply_to_nickname,
        content=data.content,
        rendered_content=rendered_content,
        status=Comment.STATUS_APPROVED,
        ip_address=guest.ip_address,
    )

    if data.parent_id is None:
        # 不阻塞用户评论请求：AI 自动回复改为后台异步执行。
        asyncio.create_task(_try_auto_ai_reply(comment.id, redis))

    return comment


async def _try_auto_ai_reply(comment_id: int, redis: Redis) -> None:
    if not await FeatureSwitchService.is_ai_enabled():
        return

    from app.modules.ai import service as ai_service

    comment = await Comment.filter(id=comment_id).prefetch_related("guest").first()
    if not comment:
        return

    article = await Article.get_or_none(id=comment.article_id)
    if not article:
        return

    try:
        ai_result = await ai_service.call_openai_api(
            messages=[
                {
                    "role": "system",
                    "content": "你是博客站点的 AI 助手。请用简洁、友好、专业的中文回复用户评论。",
                },
                {
                    "role": "user",
                    "content": f"文章标题：{article.title}\n用户评论：{comment.content}\n请给出一条自然、礼貌且有帮助的回复。",
                },
            ],
            redis=redis,
        )
        suggested_reply = (ai_result.get("content") or "").strip()
        if not suggested_reply:
            return

        ai_guest = await GuestIdentity.get_or_none(guest_token="ai-assistant")
        if not ai_guest:
            ai_nickname = "AI助手"
            if await GuestIdentity.filter(nickname=ai_nickname).exists():
                ai_nickname = "AI助手Bot"
            ai_guest = await GuestIdentity.create(
                guest_token="ai-assistant",
                nickname=ai_nickname,
                ip_address="127.0.0.1",
                user_agent="system-ai-assistant",
            )

        await Comment.create(
            article_id=comment.article_id,
            guest=ai_guest,
            parent_id=comment.id,
            reply_to_nickname=build_guest_display_name(await comment.guest),
            content=suggested_reply,
            rendered_content=await render_markdown_content(suggested_reply),
            status=Comment.STATUS_APPROVED,
            ip_address="127.0.0.1",
        )
    except Exception:
        # AI 自动回复失败不影响正常评论发布。
        return


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
) -> Optional[Comment]:
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
        await comment.delete()
        await OperationLog.create(
            operator=admin.username,
            action=f"comment_{action}",
            target_type="comment",
            target_id=comment_id,
            detail=f"操作: {action}, 原因: {reason or '无'}, 物理删除评论，原状态: {old_status}, 原置顶: {old_pinned}",
            ip_address="127.0.0.1",
            result="success",
        )
        return None
    else:
        raise BadRequestException("无效的操作")
    
    await comment.save()
    
    await OperationLog.create(
        operator=admin.username,
        action=f"comment_{action}",
        target_type="comment",
        target_id=comment_id,
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

    # 将管理员回复落为真实评论，确保前台/管理端回复链可见。
    # 统一挂到根评论下，避免出现前台不展示的多层嵌套。
    root_comment_id = comment.parent_id or comment.id
    target_guest = await comment.guest

    admin_guest = await GuestIdentity.get_or_none(guest_token=f"admin-{admin.id}")
    if not admin_guest:
        nickname_base = admin.username.strip() or "管理员"
        nickname = nickname_base
        suffix = 1
        while await GuestIdentity.filter(nickname=nickname).exclude(guest_token=f"admin-{admin.id}").exists():
            suffix += 1
            nickname = f"{nickname_base}_{suffix}"

        admin_guest = await GuestIdentity.create(
            guest_token=f"admin-{admin.id}",
            nickname=nickname,
            ip_address="127.0.0.1",
            user_agent="system-admin-reply",
        )

    rendered_reply = await render_markdown_content(content)
    await Comment.create(
        article_id=comment.article_id,
        guest=admin_guest,
        parent_id=root_comment_id,
        reply_to_nickname=build_guest_display_name(target_guest),
        content=content,
        rendered_content=rendered_reply,
        status=Comment.STATUS_APPROVED,
        ip_address="127.0.0.1",
    )
    
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
    guest_display_name = await resolve_guest_display_name(guest)
    
    guest_out = GuestIdentityOut(
        id=guest.id,
        guest_token=guest.guest_token,
        nickname=guest_display_name,
        created_at=guest.created_at,
    )
    
    replies_out = []
    reply_items = await Comment.filter(
        parent_id=comment.id,
        status=Comment.STATUS_APPROVED,
    ).order_by("created_at").prefetch_related("guest")

    for reply in reply_items:
        reply_guest = await reply.guest
        reply_guest_display_name = await resolve_guest_display_name(reply_guest)
        reply_guest_out = GuestIdentityOut(
            id=reply_guest.id,
            guest_token=reply_guest.guest_token,
            nickname=reply_guest_display_name,
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
