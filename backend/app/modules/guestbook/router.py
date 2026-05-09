from typing import Optional
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.common.response import success
from app.core.dependencies import get_guest_identity, get_redis, get_current_admin, get_current_admin_optional
from app.modules.auth.models import AdminUser
from app.modules.comments.models import GuestIdentity
from app.modules.guestbook.schemas import GuestbookMessageCreate, AdminGuestbookAction
from app.modules.guestbook import service

router = APIRouter(prefix="/guestbook", tags=["Guestbook"])


@router.get("/messages")
async def list_guestbook_messages(
    page: int = 1,
    page_size: int = 20,
):
    messages, total = await service.list_messages(
        page=page,
        page_size=page_size,
    )

    items = []
    from app.modules.comments.service import resolve_guest_display_name
    for msg in messages:
        guest = await msg.guest
        items.append({
            "id": msg.id,
            "guest_name": await resolve_guest_display_name(guest),
            "content": msg.content,
            "rendered_content": msg.rendered_content,
            "status": msg.status,
            "created_at": msg.created_at.isoformat(),
        })

    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/messages")
async def create_guestbook_message(
    data: GuestbookMessageCreate,
    guest: GuestIdentity = Depends(get_guest_identity),
    redis: Redis = Depends(get_redis),
    admin: Optional[AdminUser] = Depends(get_current_admin_optional),
):
    message = await service.create_message(data, guest, redis, admin=admin)

    guest_obj = await message.guest
    from app.modules.comments.service import resolve_guest_display_name

    return success({
        "id": message.id,
        "guest_name": await resolve_guest_display_name(guest_obj),
        "content": message.content,
        "rendered_content": message.rendered_content,
        "status": message.status,
        "created_at": message.created_at.isoformat(),
    }, "留言发布成功")


@router.get("/admin/messages")
async def list_admin_guestbook_messages(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    admin: AdminUser = Depends(get_current_admin),
):
    _ = admin
    messages, total = await service.list_messages_admin(
        status=status,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    from app.modules.comments.service import resolve_guest_display_name
    items = []
    for msg in messages:
        guest = await msg.guest
        items.append({
            "id": msg.id,
            "guest_name": await resolve_guest_display_name(guest),
            "content": msg.content,
            "rendered_content": msg.rendered_content,
            "status": msg.status,
            "ip_address": msg.ip_address,
            "created_at": msg.created_at.isoformat(),
            "updated_at": msg.updated_at.isoformat(),
        })

    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/admin/messages/{message_id}/action")
async def admin_action_guestbook_message(
    message_id: int,
    data: AdminGuestbookAction,
    admin: AdminUser = Depends(get_current_admin),
):
    message = await service.admin_action_message(
        message_id=message_id,
        action=data.action,
        admin=admin,
        reason=data.reason,
    )
    if data.action == "delete":
        return success({"message_id": message_id, "deleted": True})

    guest = await message.guest
    from app.modules.comments.service import resolve_guest_display_name
    return success({
        "id": message.id,
        "guest_name": await resolve_guest_display_name(guest),
        "content": message.content,
        "rendered_content": message.rendered_content,
        "status": message.status,
        "ip_address": message.ip_address,
        "created_at": message.created_at.isoformat(),
        "updated_at": message.updated_at.isoformat(),
    })