from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.modules.statistics import service
from app.modules.statistics.schemas import (
    APIMonitorResponse,
    APIMetrics,
    DashboardData,
    HealthStatus,
    RecentCommentActivity,
    RecentError,
    SystemHealthResponse,
    TopArticle,
    TrendData,
    TrendResponse,
)


@pytest.mark.asyncio
async def test_dashboard_and_trends(client: AsyncClient, auth_headers: dict, monkeypatch):
    async def _mock_dashboard():
        return DashboardData(
            total_articles=10,
            published_articles=8,
            draft_articles=2,
            total_views=1000,
            total_comments=200,
            pending_comments=5,
            online_users=3,
            today_views=20,
            today_comments=4,
            today_new_articles=1,
        )

    async def _mock_trends(metric: str, period: str):
        return TrendResponse(
            period=period,
            metric=metric,
            data=[TrendData(date="2026-05-07", value=12)],
        )

    monkeypatch.setattr(service.StatisticsService, "get_dashboard_data", _mock_dashboard)
    monkeypatch.setattr(service.StatisticsService, "get_trend_data", _mock_trends)

    dashboard = await client.get("/api/v1/admin/statistics/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["data"]["total_articles"] == 10

    trends = await client.get(
        "/api/v1/admin/statistics/trends",
        params={"metric": "views", "period": "day"},
        headers=auth_headers,
    )
    assert trends.status_code == 200
    assert trends.json()["data"]["data"][0]["value"] == 12


@pytest.mark.asyncio
async def test_monitor_health_and_rankings(client: AsyncClient, auth_headers: dict, monkeypatch):
    async def _mock_api_metrics(hours: int):
        return APIMonitorResponse(
            total_calls=120,
            avg_response_ms=45.5,
            error_rate=0.02,
            top_endpoints=[
                APIMetrics(
                    endpoint="/api/v1/articles",
                    method="GET",
                    call_count=80,
                    avg_response_ms=30.0,
                    success_rate=0.99,
                    error_count=1,
                )
            ],
            recent_errors=[
                RecentError(
                    endpoint="/api/v1/auth/login",
                    method="POST",
                    status_code=401,
                    error_message="Unauthorized",
                    ip_address="127.0.0.1",
                    created_at=datetime.now(timezone.utc),
                )
            ],
        )

    async def _mock_health():
        return SystemHealthResponse(
            overall_status="healthy",
            services=[HealthStatus(service="db", status="ok", latency_ms=8.6, detail=None)],
            checked_at=datetime.now(timezone.utc),
        )

    async def _mock_top_articles(limit: int):
        return [
            TopArticle(
                id=1,
                title="Top One",
                slug="top-one",
                view_count=99,
                published_at=datetime.now(timezone.utc),
            )
        ]

    async def _mock_recent_comments(limit: int):
        return [
            RecentCommentActivity(
                article_id=1,
                article_title="Top One",
                comment_count=7,
                latest_comment_at=datetime.now(timezone.utc),
            )
        ]

    monkeypatch.setattr(service.StatisticsService, "get_api_metrics", _mock_api_metrics)
    monkeypatch.setattr(service.StatisticsService, "check_system_health", _mock_health)
    monkeypatch.setattr(service.StatisticsService, "get_top_viewed_articles", _mock_top_articles)
    monkeypatch.setattr(service.StatisticsService, "get_recent_comment_activity", _mock_recent_comments)

    monitor = await client.get("/api/v1/admin/statistics/api-monitor", headers=auth_headers)
    assert monitor.status_code == 200
    assert monitor.json()["data"]["total_calls"] == 120

    health = await client.get("/api/v1/admin/statistics/health", headers=auth_headers)
    assert health.status_code == 200
    assert health.json()["data"]["overall_status"] == "healthy"

    top = await client.get(
        "/api/v1/admin/statistics/articles/top-viewed",
        params={"limit": 5},
        headers=auth_headers,
    )
    assert top.status_code == 200
    assert top.json()["data"][0]["slug"] == "top-one"

    recent = await client.get(
        "/api/v1/admin/statistics/comments/recent",
        params={"limit": 5},
        headers=auth_headers,
    )
    assert recent.status_code == 200
    assert recent.json()["data"][0]["article_id"] == 1
