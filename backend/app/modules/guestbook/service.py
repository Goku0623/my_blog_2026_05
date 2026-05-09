from typing import List, Optional
from datetime import datetime
import markdown
from redis.asyncio import Redis

from app.common.exceptions import BusinessException, BadRequestException, NotFoundException
from app.modules.guestbook.models import GuestbookMessage
from app.modules.guestbook.schemas import GuestbookMessageCreate
from app.modules.comments.models import GuestIdentity
from app.modules.auth.models import AdminUser
from app.modules.system.models import OperationLog
from app.modules.system.service import SensitiveWordService, FeatureSwitchService


async def check_guestbook_rate_limit(guest_token: str, redis: Redis) -> bool:
    key = f"guestbook_rate_limit:{guest_token}"
    window = 86400
    limit = 3

    now = datetime.now().timestamp()

    await redis.zremrangebyscore(key, 0, now - window)

    count = await redis.zcard(key)
    if count >= limit:
        raise BusinessException(429, "留言过于频繁，每位游客每天最多留言 3 条，请明天再来")

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


async def resolve_message_guest_identity(guest: GuestIdentity, admin: Optional[AdminUser]) -> GuestIdentity:
    if not admin:
        return guest

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
            user_agent=guest.user_agent or "system-admin-guestbook",
        )
        return admin_guest

    old_nickname = admin_guest.nickname
    admin_guest.ip_address = guest.ip_address
    admin_guest.user_agent = guest.user_agent
    desired_nickname = admin.username.strip() or old_nickname
    admin_guest.nickname = desired_nickname

    try:
        await admin_guest.save()
    except Exception:
        # 昵称冲突时仅同步来源信息，展示层会优先解析管理员最新用户名。
        admin_guest.nickname = old_nickname
        await admin_guest.save(update_fields=["ip_address", "user_agent"])

    return admin_guest


async def create_message(
    data: GuestbookMessageCreate,
    guest: GuestIdentity,
    redis: Redis,
    admin: Optional[AdminUser] = None,
) -> GuestbookMessage:
    if not await FeatureSwitchService.is_comment_enabled():
        raise BadRequestException("留言功能已关闭")

    guest = await resolve_message_guest_identity(guest, admin)

    await check_guestbook_rate_limit(guest.guest_token, redis)

    words = await SensitiveWordService.get_sensitive_words_cached()
    normalized = data.content.lower()
    for word in words:
        clean = word.strip()
        if clean and clean.lower() in normalized:
            raise BadRequestException(f"内容包含敏感词：{word}")

    rendered = await render_markdown_content(data.content)

    message = await GuestbookMessage.create(
        guest=guest,
        content=data.content,
        rendered_content=rendered,
        status=GuestbookMessage.STATUS_APPROVED,
        ip_address=guest.ip_address,
    )

    return message


async def list_messages(
    page: int = 1,
    page_size: int = 20,
) -> tuple:
    query = GuestbookMessage.filter(
        status=GuestbookMessage.STATUS_APPROVED,
    ).order_by("-created_at")

    total = await query.count()
    offset = (page - 1) * page_size
    messages = await query.offset(offset).limit(page_size).prefetch_related("guest")

    return list(messages), total


async def list_messages_admin(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[GuestbookMessage], int]:
    query = GuestbookMessage.all()

    if status:
        query = query.filter(status=status)

    if keyword:
        query = query.filter(content__icontains=keyword)

    query = query.order_by("-created_at")

    total = await query.count()
    offset = (page - 1) * page_size
    messages = await query.offset(offset).limit(page_size).prefetch_related("guest")
    return list(messages), total


async def admin_action_message(
    message_id: int,
    action: str,
    admin: AdminUser,
    reason: Optional[str] = None,
) -> Optional[GuestbookMessage]:
    message = await GuestbookMessage.get_or_none(id=message_id).prefetch_related("guest")
    if not message:
        raise NotFoundException("留言不存在")

    old_status = message.status
    if action == "delete":
        await message.delete()
        await OperationLog.create(
            operator=admin.username,
            action="guestbook_delete",
            target_type="guestbook_message",
            target_id=message_id,
            detail=f"删除留言，原状态: {old_status}，原因: {reason or '无'}",
            ip_address="127.0.0.1",
            result="success",
        )
        return None

    if action == "approve":
        message.status = GuestbookMessage.STATUS_APPROVED
    elif action == "hide":
        message.status = GuestbookMessage.STATUS_HIDDEN
    else:
        raise BadRequestException("无效的操作")

    await message.save()
    await OperationLog.create(
        operator=admin.username,
        action=f"guestbook_{action}",
        target_type="guestbook_message",
        target_id=message_id,
        detail=f"留言状态变更: {old_status} -> {message.status}，原因: {reason or '无'}",
        ip_address="127.0.0.1",
        result="success",
    )
    return message