from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class N8NArticlePayload(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    category_name: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    n8n_secret: str


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
