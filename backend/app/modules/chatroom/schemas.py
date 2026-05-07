from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class WSMessage(BaseModel):
    type: str
    data: dict
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChatMessageOut(BaseModel):
    id: int
    sender_nickname: str
    message_type: str
    content: str
    is_recalled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SendMessageRequest(BaseModel):
    content: str = Field(..., max_length=200, min_length=1)
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Content cannot be empty")
        return v


class AdminActionRequest(BaseModel):
    action: str = Field(..., pattern="^(recall|ban|kick|announcement|clear_history)$")
    target_guest_token: Optional[str] = None
    reason: Optional[str] = None
    content: Optional[str] = None
    ban_duration_minutes: Optional[int] = Field(default=None, ge=1)
    message_id: Optional[int] = None
    
    @field_validator("action")
    @classmethod
    def validate_action_requirements(cls, v: str) -> str:
        return v


class OnlineInfo(BaseModel):
    online_count: int
    online_list: list[dict]


class MessageHistoryResponse(BaseModel):
    messages: list[ChatMessageOut]
    total: int
