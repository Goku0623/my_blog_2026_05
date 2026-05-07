import asyncio
import json
from typing import Dict
from datetime import datetime
from fastapi import WebSocket

from app.core.redis_client import get_redis_client


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._heartbeat_task = None
        
    async def connect(self, guest_token: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[guest_token] = websocket
        
        redis = await get_redis_client()
        await redis.setex(
            f"chatroom:online:{guest_token}",
            65,
            datetime.utcnow().isoformat()
        )
        
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def disconnect(self, guest_token: str):
        if guest_token in self.active_connections:
            del self.active_connections[guest_token]
        
        redis = await get_redis_client()
        await redis.delete(f"chatroom:online:{guest_token}")
        
        await self.broadcast({
            "type": "leave",
            "data": {"guest_token": guest_token},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast(self, message: dict):
        message_text = json.dumps(message, ensure_ascii=False)
        disconnected = []
        
        for guest_token, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_text)
            except Exception:
                disconnected.append(guest_token)
        
        for guest_token in disconnected:
            await self.disconnect(guest_token)
    
    async def send_personal(self, guest_token: str, message: dict):
        if guest_token in self.active_connections:
            try:
                message_text = json.dumps(message, ensure_ascii=False)
                await self.active_connections[guest_token].send_text(message_text)
            except Exception:
                await self.disconnect(guest_token)
    
    async def get_online_count(self) -> int:
        redis = await get_redis_client()
        keys = await redis.keys("chatroom:online:*")
        return len(keys)
    
    async def get_online_list(self) -> list:
        from app.modules.comments.models import GuestIdentity
        
        redis = await get_redis_client()
        keys = await redis.keys("chatroom:online:*")
        
        guest_tokens = [key.replace("chatroom:online:", "") for key in keys]
        
        if not guest_tokens:
            return []
        
        guests = await GuestIdentity.filter(guest_token__in=guest_tokens).all()
        return [{"guest_token": g.guest_token, "nickname": g.nickname} for g in guests]
    
    async def _heartbeat_loop(self):
        while True:
            try:
                await asyncio.sleep(30)
                
                if not self.active_connections:
                    continue
                
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                redis = await get_redis_client()
                
                disconnected = []
                for guest_token, websocket in self.active_connections.items():
                    try:
                        await websocket.send_json(ping_message)
                        
                        await redis.expire(f"chatroom:online:{guest_token}", 65)
                    except Exception:
                        disconnected.append(guest_token)
                
                for guest_token in disconnected:
                    await self.disconnect(guest_token)
                    
            except Exception:
                continue


manager = ConnectionManager()
