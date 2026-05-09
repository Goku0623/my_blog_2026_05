from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class GuestIdentityOut(BaseModel):
    id: int
    guest_token: str
    nickname: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SetNicknameRequest(BaseModel):
    nickname: str = Field(..., min_length=3, max_length=20)

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        if not re.match(r'^[\w\u4e00-\u9fa5]+$', v):
            raise ValueError("昵称只允许字母、数字、下划线和中文")
        return v


class CommentCreate(BaseModel):
    article_id: int
    parent_id: Optional[int] = None
    content: str = Field(..., min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: int
    article_id: int
    guest: GuestIdentityOut
    parent_id: Optional[int]
    reply_to_nickname: Optional[str]
    content: str
    rendered_content: Optional[str]
    status: str
    is_pinned: bool
    admin_reply: Optional[str]
    created_at: datetime
    replies: List["CommentOut"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CommentListResponse(BaseModel):
    items: List[CommentOut]
    total: int
    page: int
    page_size: int


class AdminCommentAction(BaseModel):
    action: str = Field(..., pattern="^(pin|unpin|hide|approve|delete)$")
    reason: Optional[str] = None


class AdminReplyRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
