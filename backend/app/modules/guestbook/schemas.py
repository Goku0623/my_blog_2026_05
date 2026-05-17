from typing import Optional
from pydantic import BaseModel, Field


class GuestbookMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class AdminGuestbookAction(BaseModel):
    action: str = Field(..., pattern="^(approve|hide|delete)$")
    reason: Optional[str] = Field(default=None, max_length=200)