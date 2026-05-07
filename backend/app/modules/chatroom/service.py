from typing import List, Optional
from datetime import datetime, timedelta
from tortoise.expressions import Q

from app.modules.chatroom.models import ChatMessage, ChatBan
from app.modules.chatroom.schemas import ChatMessageOut
from app.modules.comments.models import GuestIdentity
from app.common.exceptions import BadRequestException, ForbiddenException, NotFoundException


class ChatroomService:
    
    @staticmethod
    async def get_message_history(limit: int = 50, before_id: Optional[int] = None) -> List[ChatMessageOut]:
        query = ChatMessage.filter(is_recalled=False)
        
        if before_id:
            query = query.filter(id__lt=before_id)
        
        messages = await query.order_by("-created_at").limit(limit).all()
        messages.reverse()
        
        return [ChatMessageOut.model_validate(msg) for msg in messages]
    
    @staticmethod
    async def save_message(
        guest: GuestIdentity,
        content: str,
        message_type: str = "text"
    ) -> ChatMessage:
        message = await ChatMessage.create(
            guest=guest,
            sender_nickname=guest.nickname or "游客",
            message_type=message_type,
            content=content
        )
        return message
    
    @staticmethod
    async def recall_message(message_id: int, operator: str):
        message = await ChatMessage.get_or_none(id=message_id)
        if not message:
            raise NotFoundException("Message not found")
        
        if message.is_recalled:
            raise BadRequestException("Message already recalled")
        
        message.is_recalled = True
        message.recalled_at = datetime.utcnow()
        await message.save()
        
        return message
    
    @staticmethod
    async def ban_guest(
        guest_token: str,
        reason: str,
        duration_minutes: Optional[int],
        operator: str
    ) -> ChatBan:
        guest = await GuestIdentity.get_or_none(guest_token=guest_token)
        if not guest:
            raise NotFoundException("Guest not found")
        
        is_permanent = duration_minutes is None
        ban_expires_at = None if is_permanent else datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        ban = await ChatBan.create(
            guest=guest,
            reason=reason,
            banned_by=operator,
            ban_expires_at=ban_expires_at,
            is_permanent=is_permanent
        )
        
        guest.is_banned = True
        guest.ban_reason = reason
        await guest.save()
        
        return ban
    
    @staticmethod
    async def kick_guest(guest_token: str, reason: str, operator: str):
        guest = await GuestIdentity.get_or_none(guest_token=guest_token)
        if not guest:
            raise NotFoundException("Guest not found")
        
        return {"guest_token": guest_token, "reason": reason, "operator": operator}
    
    @staticmethod
    async def send_announcement(content: str, admin: str) -> ChatMessage:
        message = await ChatMessage.create(
            guest=None,
            sender_nickname="系统管理员",
            message_type="announcement",
            content=content
        )
        return message
    
    @staticmethod
    async def clear_history(operator: str):
        await ChatMessage.all().update(is_recalled=True, recalled_at=datetime.utcnow())
        return {"operator": operator, "cleared_at": datetime.utcnow().isoformat()}
    
    @staticmethod
    async def check_rate_limit(guest_token: str, redis) -> bool:
        key = f"chatroom:rate_limit:{guest_token}"
        current = await redis.get(key)
        
        if current is None:
            await redis.setex(key, 10, 1)
            return True
        
        count = int(current)
        if count >= 3:
            return False
        
        await redis.incr(key)
        return True
    
    @staticmethod
    async def check_guest_banned(guest_token: str) -> bool:
        guest = await GuestIdentity.get_or_none(guest_token=guest_token)
        if not guest:
            return False
        
        if guest.is_banned:
            active_ban = await ChatBan.filter(
                guest=guest
            ).filter(
                Q(is_permanent=True) | Q(ban_expires_at__gte=datetime.utcnow())
            ).first()
            
            if active_ban:
                return True
            else:
                guest.is_banned = False
                guest.ban_reason = None
                await guest.save()
        
        return False
    
    @staticmethod
    async def check_sensitive_words(content: str) -> bool:
        sensitive_words = ["fuck", "shit", "damn"]
        content_lower = content.lower()
        
        for word in sensitive_words:
            if word in content_lower:
                return True
        
        return False
