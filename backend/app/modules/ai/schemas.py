from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class N8NArticlePayload(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    status: Optional[str] = Field(default="draft")
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    tag_ids: List[int] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    cover_image: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    scheduled_publish_at: Optional[datetime] = None
    is_featured: bool = False
    allow_comment: bool = True


class N8NArticleResponse(BaseModel):
    article_id: int
    title: str
    status: str
    message: str


class WeatherRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None


class WeatherResponse(BaseModel):
    city: str
    temperature: float
    feels_like: float
    description: str
    humidity: int
    wind_speed: float
    icon: str
    updated_at: datetime


class AICommentReplyRequest(BaseModel):
    comment_id: int
    article_title: str
    comment_content: str
    context_comments: List[str] = Field(default_factory=list)


class AICommentReplyResponse(BaseModel):
    suggested_reply: str
    model_used: str
    tokens_used: int
