from fastapi import APIRouter, Depends, Query

from app.modules.statistics.service import StatisticsService
from app.modules.statistics.schemas import (
    DashboardData, TrendResponse, APIMonitorResponse,
    CeleryTaskStats, SystemHealthResponse, TopArticle, RecentCommentActivity, CategoryDistribution
)
from app.core.dependencies import get_current_admin
from app.modules.auth.models import AdminUser
from app.common.response import success


router = APIRouter(prefix="/admin/statistics", tags=["Statistics Admin"])


@router.get("/dashboard", response_model=dict)
async def get_dashboard(
    current_admin: AdminUser = Depends(get_current_admin)
):
    data = await StatisticsService.get_dashboard_data()
    return success(data.model_dump())


@router.get("/trends", response_model=dict)
async def get_trends(
    metric: str = Query(..., description="Metric type: views/comments/articles/visitors"),
    period: str = Query(..., description="Period: day/week/month"),
    current_admin: AdminUser = Depends(get_current_admin)
):
    data = await StatisticsService.get_trend_data(metric, period)
    return success(data.model_dump())


@router.get("/api-monitor", response_model=dict)
async def get_api_monitor(
    hours: int = Query(24, ge=1, le=168),
    current_admin: AdminUser = Depends(get_current_admin)
):
    data = await StatisticsService.get_api_metrics(hours)
    return success(data.model_dump())


@router.get("/celery", response_model=dict)
async def get_celery_stats(
    current_admin: AdminUser = Depends(get_current_admin)
):
    data = await StatisticsService.get_celery_stats()
    return success([stat.model_dump() for stat in data])


@router.get("/health", response_model=dict)
async def get_system_health(
    current_admin: AdminUser = Depends(get_current_admin)
):
    data = await StatisticsService.check_system_health()
    return success(data.model_dump())


@router.get("/articles/top-viewed", response_model=dict)
async def get_top_viewed_articles(
    limit: int = Query(10, ge=1, le=50),
    current_admin: AdminUser = Depends(get_current_admin)
):
    data = await StatisticsService.get_top_viewed_articles(limit)
    return success([article.model_dump() for article in data])


@router.get("/comments/recent", response_model=dict)
async def get_recent_comments(
    limit: int = Query(10, ge=1, le=50),
    current_admin: AdminUser = Depends(get_current_admin)
):
    data = await StatisticsService.get_recent_comment_activity(limit)
    return success([activity.model_dump() for activity in data])


@router.get("/categories/distribution", response_model=dict)
async def get_category_distribution(
    current_admin: AdminUser = Depends(get_current_admin)
):
    data = await StatisticsService.get_category_distribution()
    return success([item.model_dump() for item in data])
