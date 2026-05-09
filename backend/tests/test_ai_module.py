from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.modules.ai import service
from app.modules.ai.schemas import AICommentReplyResponse, WeatherResponse


@pytest.mark.asyncio
async def test_receive_n8n_article_success(client: AsyncClient, monkeypatch):
    class DummyArticle:
        id = 1
        title = "AI created article"
        status = "draft"

    async def _mock_receive(payload):
        return DummyArticle()

    monkeypatch.setattr(service, "receive_n8n_article", _mock_receive)

    response = await client.post(
        "/api/v1/ai/n8n/article",
        json={
            "title": "AI created article",
            "content": "content",
            "summary": "summary",
            "category_name": "AI",
            "tags": ["python"],
            "n8n_secret": "secret",
        },
        headers={"X-N8N-Secret": "secret"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["article_id"] == 1


@pytest.mark.asyncio
async def test_receive_n8n_article_missing_secret(client: AsyncClient):
    response = await client.post(
        "/api/v1/ai/n8n/article",
        json={
            "title": "AI created article",
            "content": "content",
            "summary": "summary",
            "category_name": "AI",
            "tags": ["python"],
            "n8n_secret": "",
        },
    )
    assert response.status_code == 401
    assert response.json()["message"] == "缺少 N8N 密钥"


@pytest.mark.asyncio
async def test_get_weather(client: AsyncClient, monkeypatch):
    async def _mock_weather(*args, **kwargs):
        return WeatherResponse(
            city="Beijing",
            temperature=23.5,
            feels_like=22.8,
            description="sunny",
            humidity=50,
            wind_speed=2.3,
            icon="01d",
            updated_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(service, "get_weather", _mock_weather)
    response = await client.get(
        "/api/v1/ai/weather",
        params={"latitude": 39.90, "longitude": 116.40, "city": "Beijing"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["city"] == "Beijing"


@pytest.mark.asyncio
async def test_generate_comment_reply(client: AsyncClient, auth_headers: dict, monkeypatch):
    async def _mock_reply(*args, **kwargs):
        return AICommentReplyResponse(
            suggested_reply="Thanks for your comment!",
            model_used="gpt-test",
            tokens_used=88,
        )

    monkeypatch.setattr(service, "generate_comment_reply", _mock_reply)
    response = await client.post(
        "/api/v1/ai/admin/comment-reply",
        json={
            "comment_id": 1,
            "article_title": "A title",
            "comment_content": "A comment",
            "context_comments": [],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["model_used"] == "gpt-test"
