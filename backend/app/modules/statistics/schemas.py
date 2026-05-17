from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class DashboardData(BaseModel):
    total_articles: int
    published_articles: int
    draft_articles: int
    total_views: int
    total_comments: int
    today_views: int
    today_comments: int
    today_new_articles: int


class TrendData(BaseModel):
    date: str
    value: int


class TrendResponse(BaseModel):
    period: str
    metric: str
    data: list[TrendData]


class APIMetrics(BaseModel):
    endpoint: str
    method: str
    call_count: int
    avg_response_ms: float
    success_rate: float
    error_count: int


class RecentError(BaseModel):
    endpoint: str
    method: str
    status_code: int
    error_message: Optional[str]
    ip_address: str
    created_at: datetime


class APIMonitorResponse(BaseModel):
    total_calls: int
    avg_response_ms: float
    error_rate: float
    top_endpoints: list[APIMetrics]
    recent_errors: list[RecentError]


class CeleryTaskStats(BaseModel):
    task_name: str
    total: int
    succeeded: int
    failed: int
    pending: int
    avg_runtime_ms: float


class HealthStatus(BaseModel):
    service: str
    status: str
    latency_ms: Optional[float]
    detail: Optional[str]


class SystemHealthResponse(BaseModel):
    overall_status: str
    services: list[HealthStatus]
    checked_at: datetime
    uptime: Optional[str] = None
    started_at: Optional[datetime] = None


class TopArticle(BaseModel):
    id: int
    title: str
    slug: str
    view_count: int
    published_at: Optional[datetime]


class CategoryDistribution(BaseModel):
    category_name: str
    article_count: int


class RecentCommentActivity(BaseModel):
    id: Optional[int] = None
    article_id: int
    article_title: str
    guest_name: Optional[str] = None
    guest_avatar: Optional[str] = None
    content: Optional[str] = None
    created_at: Optional[datetime] = None
    comment_count: int
    latest_comment_at: datetime
