from typing import List, Optional, Set
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Response, Request
from redis.asyncio import Redis

from app.common.response import success
from app.core.dependencies import get_current_admin, get_current_admin_optional, get_guest_identity, get_redis, get_client_ip
from app.modules.comments.models import GuestIdentity
from app.modules.comments.schemas import (
    CommentCreate,
    CommentOut,
    CommentListResponse,
    SetNicknameRequest,
    GuestIdentityOut,
    AdminCommentAction,
    AdminReplyRequest,
)
from app.modules.comments import service
from app.modules.auth.models import AdminUser


router = APIRouter()


@router.get("/articles/{article_id}/comments")
async def get_article_comments(
    article_id: int,
    page: int = 1,
    page_size: int = 20,
):
    comments, total = await service.list_comments_for_article(
        article_id=article_id,
        page=page,
        page_size=page_size,
    )
    
    items = []
    for comment in comments:
        comment_out = await service.convert_comment_to_out(comment)
        items.append(comment_out.model_dump())
    
    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/comments")
async def create_comment(
    data: CommentCreate,
    guest: GuestIdentity = Depends(get_guest_identity),
    redis: Redis = Depends(get_redis),
    admin: Optional[AdminUser] = Depends(get_current_admin_optional),
):
    comment = await service.create_comment(data, guest, redis, admin=admin)
    comment_out = await service.convert_comment_to_out(comment)
    
    await notify_new_comment(comment.id)
    
    return success(comment_out.model_dump())


@router.get("/guest/identity")
async def get_guest_identity_endpoint(
    response: Response,
    guest: GuestIdentity = Depends(get_guest_identity),
):
    response.set_cookie(
        key="guest_token",
        value=guest.guest_token,
        max_age=365 * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
    )
    
    guest_out = GuestIdentityOut(
        id=guest.id,
        guest_token=guest.guest_token,
        nickname=service.build_guest_display_name(guest),
        created_at=guest.created_at,
    )
    
    return success(guest_out.model_dump())


@router.put("/guest/nickname")
async def set_guest_nickname(
    data: SetNicknameRequest,
    guest: GuestIdentity = Depends(get_guest_identity),
):
    updated_guest = await service.set_guest_nickname(guest.guest_token, data.nickname)
    
    guest_out = GuestIdentityOut(
        id=updated_guest.id,
        guest_token=updated_guest.guest_token,
        nickname=service.build_guest_display_name(updated_guest),
        created_at=updated_guest.created_at,
    )
    
    return success(guest_out.model_dump())


@router.get("/admin/comments")
async def list_admin_comments(
    status: Optional[str] = None,
    article_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    admin: AdminUser = Depends(get_current_admin),
):
    comments, total = await service.list_comments_admin(
        status=status,
        article_id=article_id,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    
    items = []
    for comment in comments:
        comment_out = await service.convert_comment_to_out(comment)
        items.append(comment_out.model_dump())
    
    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/admin/comments/{comment_id}/action")
async def admin_action_on_comment(
    comment_id: int,
    data: AdminCommentAction,
    admin: AdminUser = Depends(get_current_admin),
):
    comment = await service.admin_action_comment(
        comment_id=comment_id,
        action=data.action,
        admin=admin,
        reason=data.reason,
    )

    if data.action == "delete":
        return success({"comment_id": comment_id, "deleted": True})

    comment_out = await service.convert_comment_to_out(comment)
    return success(comment_out.model_dump())


@router.post("/admin/comments/{comment_id}/reply")
async def admin_reply_to_comment(
    comment_id: int,
    data: AdminReplyRequest,
    admin: AdminUser = Depends(get_current_admin),
):
    comment = await service.admin_reply_comment(
        comment_id=comment_id,
        content=data.content,
        admin=admin,
    )
    
    comment_out = await service.convert_comment_to_out(comment)
    return success(comment_out.model_dump())


class CommentWebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


ws_manager = CommentWebSocketManager()


async def notify_new_comment(comment_id: int):
    await ws_manager.broadcast({
        "type": "new_comment",
        "comment_id": comment_id,
    })


@router.websocket("/ws/admin/comments")
async def websocket_admin_comments(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
