import pytest
from httpx import AsyncClient

from app.modules.articles.models import Article, Category, Tag


@pytest.mark.asyncio
async def test_create_article(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "Pytest Async Guide",
            "summary": "create article test",
            "content": "article content",
            "status": "draft",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["title"] == "Pytest Async Guide"
    assert body["data"]["slug"] == "pytest-async-guide"
    assert body["data"]["status"] == "draft"


@pytest.mark.asyncio
async def test_publish_article(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/admin/articles",
        json={"title": "Publish Me", "content": "publish test"},
        headers=auth_headers,
    )
    article_id = create_resp.json()["data"]["id"]

    publish_resp = await client.post(
        f"/api/v1/admin/articles/{article_id}/publish",
        headers=auth_headers,
    )
    assert publish_resp.status_code == 200
    assert publish_resp.json()["data"]["status"] == "published"


@pytest.mark.asyncio
async def test_get_article_by_slug_published_only(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/admin/articles",
        json={"title": "Draft Article", "content": "draft body"},
        headers=auth_headers,
    )
    article = create_resp.json()["data"]

    draft_get = await client.get(f"/api/v1/articles/{article['slug']}")
    assert draft_get.status_code == 404

    await client.post(
        f"/api/v1/admin/articles/{article['id']}/publish",
        headers=auth_headers,
    )
    published_get = await client.get(f"/api/v1/articles/{article['slug']}")
    assert published_get.status_code == 200
    assert published_get.json()["data"]["slug"] == article["slug"]


@pytest.mark.asyncio
async def test_view_count_dedup(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/admin/articles",
        json={"title": "View Count Article", "content": "view count body"},
        headers=auth_headers,
    )
    article = create_resp.json()["data"]

    await client.post(
        f"/api/v1/admin/articles/{article['id']}/publish",
        headers=auth_headers,
    )

    request_headers = {"X-Forwarded-For": "203.0.113.8"}
    first = await client.get(f"/api/v1/articles/{article['slug']}", headers=request_headers)
    second = await client.get(f"/api/v1/articles/{article['slug']}", headers=request_headers)
    assert first.status_code == 200
    assert second.status_code == 200

    refreshed = await Article.get(id=article["id"])
    assert refreshed.view_count == 1


@pytest.mark.asyncio
async def test_search_articles(client: AsyncClient, auth_headers: dict):
    target_create = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "FastAPI Searchable",
            "summary": "contains unique phrase",
            "content": "search keyword python-fastapi",
        },
        headers=auth_headers,
    )
    other_create = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "Other Article",
            "summary": "no keyword",
            "content": "plain content",
        },
        headers=auth_headers,
    )

    await client.post(
        f"/api/v1/admin/articles/{target_create.json()['data']['id']}/publish",
        headers=auth_headers,
    )
    await client.post(
        f"/api/v1/admin/articles/{other_create.json()['data']['id']}/publish",
        headers=auth_headers,
    )

    search_resp = await client.get("/api/v1/articles", params={"keyword": "python-fastapi"})
    assert search_resp.status_code == 200
    data = search_resp.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["title"] == "FastAPI Searchable"


@pytest.mark.asyncio
async def test_create_category_and_tag(client: AsyncClient, auth_headers: dict):
    category_resp = await client.post(
        "/api/v1/admin/categories",
        json={"name": "Testing", "slug": "testing"},
        headers=auth_headers,
    )
    tag_resp = await client.post(
        "/api/v1/admin/tags",
        json={"name": "pytest", "slug": "pytest", "color": "#00AAFF"},
        headers=auth_headers,
    )

    assert category_resp.status_code == 200
    assert tag_resp.status_code == 200
    assert category_resp.json()["data"]["slug"] == "testing"
    assert tag_resp.json()["data"]["slug"] == "pytest"

    list_categories = await client.get("/api/v1/categories")
    list_tags = await client.get("/api/v1/tags")
    assert any(item["slug"] == "testing" for item in list_categories.json()["data"])
    assert any(item["slug"] == "pytest" for item in list_tags.json()["data"])

    category = await Category.get(slug="testing")
    tag = await Tag.get(slug="pytest")
    assert category.name == "Testing"
    assert tag.name == "pytest"
