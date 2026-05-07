import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query

from app.modules.chatroom.ws_manager import manager
from app.modules.chatroom.service import ChatroomService
from app.modules.chatroom.schemas import (
    SendMessageRequest,
    AdminActionRequest,
    OnlineInfo,
    MessageHistoryResponse,
    ChatMessageOut,
)
from app.modules.comments.models import GuestIdentity
from app.core.dependencies import get_redis, get_current_admin
from app.core.security import decode_token
from app.common.exceptions import BadRequestException, ForbiddenException


router = APIRouter(prefix="/chatroom", tags=["Chatroom"])


@router.get("/history", response_model=MessageHistoryResponse)
async def get_history(
    limit: int = Query(50, ge=1, le=100),
    before_id: Optional[int] = None
):
    messages = await ChatroomService.get_message_history(limit, before_id)
    return MessageHistoryResponse(messages=messages, total=len(messages))


@router.get("/online", response_model=OnlineInfo)
async def get_online():
    count = await manager.get_online_count()
    online_list = await manager.get_online_list()
    return OnlineInfo(online_count=count, online_list=online_list)


@router.websocket("/ws/chatroom")
async def chatroom_websocket(
    websocket: WebSocket,
    guest_token: Optional[str] = Query(None)
):
    redis = await get_redis()
    guest = None
    
    try:
        if not guest_token:
            await websocket.close(code=1008, reason="Missing guest_token")
            return
        
        guest = await GuestIdentity.get_or_none(guest_token=guest_token)
        if not guest:
            await websocket.close(code=1008, reason="Invalid guest_token")
            return
        
        is_banned = await ChatroomService.check_guest_banned(guest_token)
        if is_banned:
            await websocket.close(code=1008, reason="You are banned")
            return
        
        await manager.connect(guest_token, websocket)
        
        history_messages = await ChatroomService.get_message_history(limit=50)
        await websocket.send_json({
            "type": "history",
            "data": {
                "messages": [
                    {
                        "id": msg.id,
                        "sender_nickname": msg.sender_nickname,
                        "message_type": msg.message_type,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in history_messages
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await manager.broadcast({
            "type": "join",
            "data": {
                "guest_token": guest_token,
                "nickname": guest.nickname or "游客"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                msg_type = message_data.get("type")
                
                if msg_type == "pong":
                    continue
                
                if msg_type == "message":
                    content = message_data.get("content", "").strip()
                    
                    if not content or len(content) > 200:
                        await manager.send_personal(guest_token, {
                            "type": "error",
                            "data": {"message": "Invalid message length"},
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    rate_ok = await ChatroomService.check_rate_limit(guest_token, redis)
                    if not rate_ok:
                        await manager.send_personal(guest_token, {
                            "type": "error",
                            "data": {"message": "Too many messages, please slow down"},
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    has_sensitive = await ChatroomService.check_sensitive_words(content)
                    if has_sensitive:
                        await manager.send_personal(guest_token, {
                            "type": "error",
                            "data": {"message": "Message contains sensitive words"},
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    saved_message = await ChatroomService.save_message(
                        guest=guest,
                        content=content,
                        message_type="text"
                    )
                    
                    await manager.broadcast({
                        "type": "message",
                        "data": {
                            "id": saved_message.id,
                            "sender_nickname": saved_message.sender_nickname,
                            "message_type": saved_message.message_type,
                            "content": saved_message.content,
                            "created_at": saved_message.created_at.isoformat()
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
            except json.JSONDecodeError:
                await manager.send_personal(guest_token, {
                    "type": "error",
                    "data": {"message": "Invalid JSON format"},
                    "timestamp": datetime.utcnow().isoformat()
                })
                continue
            except Exception as e:
                await manager.send_personal(guest_token, {
                    "type": "error",
                    "data": {"message": f"Error: {str(e)}"},
                    "timestamp": datetime.utcnow().isoformat()
                })
                continue
    
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if guest and guest_token:
            await manager.disconnect(guest_token)


@router.websocket("/ws/admin/chatroom")
async def admin_chatroom_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    try:
        if not token:
            await websocket.close(code=1008, reason="Missing token")
            return
        
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        await websocket.accept()
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                action = message_data.get("action")
                
                if action == "recall":
                    message_id = message_data.get("message_id")
                    if message_id:
                        await ChatroomService.recall_message(message_id, "admin")
                        await manager.broadcast({
                            "type": "recall",
                            "data": {"message_id": message_id},
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        await websocket.send_json({
                            "type": "success",
                            "data": {"message": "Message recalled"}
                        })
                
                elif action == "ban":
                    target_token = message_data.get("target_guest_token")
                    reason = message_data.get("reason", "违规行为")
                    duration = message_data.get("ban_duration_minutes")
                    
                    if target_token:
                        await ChatroomService.ban_guest(target_token, reason, duration, "admin")
                        
                        await manager.send_personal(target_token, {
                            "type": "ban",
                            "data": {
                                "reason": reason,
                                "duration_minutes": duration
                            },
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        await manager.disconnect(target_token)
                        
                        await websocket.send_json({
                            "type": "success",
                            "data": {"message": "User banned"}
                        })
                
                elif action == "kick":
                    target_token = message_data.get("target_guest_token")
                    reason = message_data.get("reason", "踢出聊天室")
                    
                    if target_token:
                        await ChatroomService.kick_guest(target_token, reason, "admin")
                        
                        await manager.send_personal(target_token, {
                            "type": "kick",
                            "data": {"reason": reason},
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        await manager.disconnect(target_token)
                        
                        await websocket.send_json({
                            "type": "success",
                            "data": {"message": "User kicked"}
                        })
                
                elif action == "announcement":
                    content = message_data.get("content")
                    if content:
                        message = await ChatroomService.send_announcement(content, "admin")
                        
                        await manager.broadcast({
                            "type": "announcement",
                            "data": {
                                "id": message.id,
                                "content": message.content,
                                "created_at": message.created_at.isoformat()
                            },
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        await websocket.send_json({
                            "type": "success",
                            "data": {"message": "Announcement sent"}
                        })
                
                elif action == "clear_history":
                    await ChatroomService.clear_history("admin")
                    
                    await manager.broadcast({
                        "type": "system",
                        "data": {"message": "History cleared by admin"},
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    await websocket.send_json({
                        "type": "success",
                        "data": {"message": "History cleared"}
                    })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON"}
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": str(e)}
                })
    
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@router.post("/admin/chatroom/action")
async def admin_action(
    action_req: AdminActionRequest,
    admin = Depends(get_current_admin)
):
    if action_req.action == "recall":
        if not action_req.message_id:
            raise BadRequestException("message_id is required for recall action")
        
        await ChatroomService.recall_message(action_req.message_id, admin.username)
        await manager.broadcast({
            "type": "recall",
            "data": {"message_id": action_req.message_id},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return {"code": 0, "message": "Message recalled", "data": None}
    
    elif action_req.action == "ban":
        if not action_req.target_guest_token:
            raise BadRequestException("target_guest_token is required for ban action")
        
        await ChatroomService.ban_guest(
            action_req.target_guest_token,
            action_req.reason or "违规行为",
            action_req.ban_duration_minutes,
            admin.username
        )
        
        await manager.send_personal(action_req.target_guest_token, {
            "type": "ban",
            "data": {
                "reason": action_req.reason,
                "duration_minutes": action_req.ban_duration_minutes
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        await manager.disconnect(action_req.target_guest_token)
        
        return {"code": 0, "message": "User banned", "data": None}
    
    elif action_req.action == "kick":
        if not action_req.target_guest_token:
            raise BadRequestException("target_guest_token is required for kick action")
        
        await ChatroomService.kick_guest(
            action_req.target_guest_token,
            action_req.reason or "踢出聊天室",
            admin.username
        )
        
        await manager.send_personal(action_req.target_guest_token, {
            "type": "kick",
            "data": {"reason": action_req.reason},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        await manager.disconnect(action_req.target_guest_token)
        
        return {"code": 0, "message": "User kicked", "data": None}
    
    elif action_req.action == "announcement":
        if not action_req.content:
            raise BadRequestException("content is required for announcement action")
        
        message = await ChatroomService.send_announcement(action_req.content, admin.username)
        
        await manager.broadcast({
            "type": "announcement",
            "data": {
                "id": message.id,
                "content": message.content,
                "created_at": message.created_at.isoformat()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"code": 0, "message": "Announcement sent", "data": None}
    
    elif action_req.action == "clear_history":
        await ChatroomService.clear_history(admin.username)
        
        await manager.broadcast({
            "type": "system",
            "data": {"message": "History cleared by admin"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"code": 0, "message": "History cleared", "data": None}
    
    else:
        raise BadRequestException("Invalid action")


@router.get("/admin/chatroom/messages")
async def get_all_messages(
    admin = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_recalled: bool = Query(False)
):
    from app.modules.chatroom.models import ChatMessage
    
    query = ChatMessage.all()
    if not include_recalled:
        query = query.filter(is_recalled=False)
    
    total = await query.count()
    messages = await query.order_by("-created_at").offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "messages": [
                {
                    "id": msg.id,
                    "sender_nickname": msg.sender_nickname,
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "is_recalled": msg.is_recalled,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }
