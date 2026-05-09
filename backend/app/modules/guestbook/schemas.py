from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class GuestbookMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class GuestIdentitySimple(BaseModel):
    id: int
    guest_token: str
    nickname: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GuestbookMessageOut(BaseModel):
    id: int
    guest: GuestIdentitySimple
    content: str
    rendered_content: Optional[str]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GuestbookMessageListResponse(BaseModel):
    items: List[GuestbookMessageOut]
    total: int
    page: int
    page_size: int


class AdminGuestbookAction(BaseModel):
    action: str = Field(..., pattern="^(approve|hide|delete)$")
    reason: Optional[str] = Field(default=None, max_length=200)