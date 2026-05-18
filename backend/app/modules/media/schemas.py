from typing import Optional, Literal

from pydantic import BaseModel, Field


class MediaFetchRequest(BaseModel):
    url: str = Field(..., min_length=1)
    purpose: Literal["cover", "content"] = "content"


class MediaUploadResponse(BaseModel):
    url: str
    size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
