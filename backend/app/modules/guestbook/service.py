import asyncio
import hashlib
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


def build_visitor_fingerprint(ip: str, user_agent: str) -> str:
    normalized_ip = (ip or "unknown").strip()
    normalized_ua = (user_agent or "unknown").strip().lower()
    raw = f"{normalized_ip}|{normalized_ua}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _get_config_int(key: str, default: int) -> int:
    from app.modules.system.models import SiteConfig
    import os

    config = await SiteConfig.get_or_none(key=key)
    value = config.value if config and config.value not in (None, "") else os.getenv(key, str(default))
    try:
        return max(0, int(str(value).strip()))
    except (TypeError, ValueError):
        return default


async def check_guestbook_rate_limit(guest: GuestIdentity, redis: Redis) -> None:
    per_user_limit = await _get_config_int("GUESTBOOK_DAILY_LIMIT_PER_USER", 2)
    if per_user_limit == 0:
        return

    today = datetime.now().strftime("%Y%m%d")
    ttl_seconds = 2 * 24 * 60 * 60
    keys_to_check = [f"guestbook_daily:token:{guest.guest_token}:{today}"]

    is_guest_user = not (guest.guest_token or "").startswith("admin-")
    if is_guest_user:
        fingerprint = build_visitor_fingerprint(guest.ip_address, guest.user_agent or "")
        keys_to_check.append(f"guestbook_daily:fp:{fingerprint}:{today}")

    for key in keys_to_check:
        current_raw = await redis.get(key)
        current = int(current_raw) if current_raw is not None else 0
        if current >= per_user_limit:
            raise BusinessException(429, f"您每天至多留言{per_user_limit}条，明天再来吧")

    for key in keys_to_check:
        new_count = await redis.incr(key)
        if new_count == 1:
            await redis.expire(key, ttl_seconds)


async def render_markdown_content(content: str) -> str:
    def _render() -> str:
        md = markdown.Markdown(
            extensions=[
                'extra',
                'codehilite',
                'nl2br',
                'sane_lists',
            ]
        )
        return md.convert(content)

    return await asyncio.to_thread(_render)


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

    words = await SensitiveWordService.get_sensitive_words_cached()
    normalized = data.content.lower()
    for word in words:
        clean = word.strip()
        if clean and clean.lower() in normalized:
            raise BadRequestException(f"内容包含敏感词：{word}")

    if not admin:
        await check_guestbook_rate_limit(guest, redis)

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