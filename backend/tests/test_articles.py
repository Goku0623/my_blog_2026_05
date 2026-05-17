import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

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
async def test_search_endpoint_supports_field_and_time_filter(client: AsyncClient, auth_headers: dict):
    title_resp = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "Vue Search Title Match",
            "summary": "regular summary",
            "content": "regular content",
        },
        headers=auth_headers,
    )
    summary_resp = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "No Match Title",
            "summary": "contains phrase-only-in-summary",
            "content": "regular content",
        },
        headers=auth_headers,
    )
    content_only_resp = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "No Match",
            "summary": "regular summary",
            "content": "contains phrase-only-in-summary",
        },
        headers=auth_headers,
    )

    await client.post(f"/api/v1/admin/articles/{title_resp.json()['data']['id']}/publish", headers=auth_headers)
    await client.post(f"/api/v1/admin/articles/{summary_resp.json()['data']['id']}/publish", headers=auth_headers)
    await client.post(f"/api/v1/admin/articles/{content_only_resp.json()['data']['id']}/publish", headers=auth_headers)

    # 将 summary 命中项时间调旧，验证时间过滤。
    await Article.filter(id=summary_resp.json()["data"]["id"]).update(
        published_at=datetime.now() - timedelta(days=45)
    )

    title_search = await client.get(
        "/api/v1/articles/search",
        params={"keyword": "Vue Search Title", "search_in": "title"},
    )
    assert title_search.status_code == 200
    assert title_search.json()["data"]["total"] == 1
    assert title_search.json()["data"]["items"][0]["title"] == "Vue Search Title Match"

    summary_search = await client.get(
        "/api/v1/articles/search",
        params={"keyword": "phrase-only-in-summary", "search_in": "summary"},
    )
    assert summary_search.status_code == 200
    assert summary_search.json()["data"]["total"] == 1
    assert summary_search.json()["data"]["items"][0]["title"] == "No Match Title"

    # title_summary 不应匹配仅 content 命中的文章。
    combined_search = await client.get(
        "/api/v1/articles/search",
        params={"keyword": "phrase-only-in-summary", "search_in": "title_summary"},
    )
    assert combined_search.status_code == 200
    assert combined_search.json()["data"]["total"] == 1

    time_filtered = await client.get(
        "/api/v1/articles/search",
        params={
            "keyword": "phrase-only-in-summary",
            "search_in": "summary",
            "time_filter": "30d",
        },
    )
    assert time_filtered.status_code == 200
    assert time_filtered.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_scheduled_publish_draft_and_auto_publish(client: AsyncClient, auth_headers: dict):
    future_time = datetime.now() + timedelta(minutes=5)
    create_resp = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "Scheduled Draft",
            "content": "scheduled content",
            "status": "draft",
            "scheduled_publish_at": future_time.isoformat(),
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 200
    article_id = create_resp.json()["data"]["id"]

    # 草稿未到发布时间前，前台不可见。
    article_slug = create_resp.json()["data"]["slug"]
    before_visible = await client.get(f"/api/v1/articles/{article_slug}")
    assert before_visible.status_code == 404

    # 模拟任务触发后自动发布。
    from app.modules.articles.service import ArticleService
    published_count = await ArticleService.publish_due_scheduled_articles(now=future_time + timedelta(seconds=1))
    assert published_count >= 1

    refreshed = await Article.get(id=article_id)
    assert refreshed.status == "published"
    assert refreshed.scheduled_publish_at is None


@pytest.mark.asyncio
async def test_scheduled_publish_preserves_each_article_schedule_time(client: AsyncClient, auth_headers: dict):
    first_schedule = datetime.now() + timedelta(minutes=3)
    second_schedule = datetime.now() + timedelta(minutes=8)

    first_resp = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "Scheduled First",
            "content": "scheduled first content",
            "status": "draft",
            "scheduled_publish_at": first_schedule.isoformat(),
        },
        headers=auth_headers,
    )
    second_resp = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "Scheduled Second",
            "content": "scheduled second content",
            "status": "draft",
            "scheduled_publish_at": second_schedule.isoformat(),
        },
        headers=auth_headers,
    )
    assert first_resp.status_code == 200
    assert second_resp.status_code == 200

    first_id = first_resp.json()["data"]["id"]
    second_id = second_resp.json()["data"]["id"]

    from app.modules.articles.service import ArticleService
    published_count = await ArticleService.publish_due_scheduled_articles(now=second_schedule + timedelta(seconds=1))
    assert published_count >= 2

    first_article = await Article.get(id=first_id)
    second_article = await Article.get(id=second_id)
    assert first_article.status == "published"
    assert second_article.status == "published"
    assert first_article.scheduled_publish_at is None
    assert second_article.scheduled_publish_at is None
    assert first_article.published_at is not None
    assert second_article.published_at is not None
    assert first_article.published_at.replace(tzinfo=None) == first_schedule.replace(tzinfo=None)
    assert second_article.published_at.replace(tzinfo=None) == second_schedule.replace(tzinfo=None)


@pytest.mark.asyncio
async def test_scheduled_publish_not_triggered_early_with_timezone_input(client: AsyncClient, auth_headers: dict):
    from app.modules.articles.service import ArticleService

    current_time = ArticleService._utcnow_naive()
    future_time = current_time + timedelta(minutes=90)
    future_time_with_tz = future_time.replace(tzinfo=ArticleService.APP_TIMEZONE).isoformat()
    create_resp = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "Scheduled TZ Future",
            "content": "scheduled timezone future content",
            "status": "draft",
            "scheduled_publish_at": future_time_with_tz,
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 200
    article_id = create_resp.json()["data"]["id"]

    # 以更早的时间触发任务，不应提前发布。
    published_count = await ArticleService.publish_due_scheduled_articles(now=current_time + timedelta(minutes=10))
    refreshed = await Article.get(id=article_id)
    assert refreshed.status == "draft"
    assert refreshed.published_at is None
    assert refreshed.scheduled_publish_at is not None
    assert published_count >= 0


@pytest.mark.asyncio
async def test_edit_article_keeps_scheduled_publish_local_time(client: AsyncClient, auth_headers: dict):
    from app.modules.articles.service import ArticleService

    create_resp = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "Scheduled Local Time Keep",
            "content": "scheduled local time content",
            "status": "draft",
            "scheduled_publish_at": "2026-05-15T19:00:00+08:00",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 200
    article_id = create_resp.json()["data"]["id"]

    update_resp = await client.put(
        f"/api/v1/admin/articles/{article_id}",
        json={"summary": "only update summary"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["status"] == "draft"

    refreshed = await Article.get(id=article_id)
    assert refreshed.scheduled_publish_at is not None
    assert refreshed.scheduled_publish_at.astimezone(ArticleService.APP_TIMEZONE).hour == 19
    assert refreshed.scheduled_publish_at.minute == 0


@pytest.mark.asyncio
async def test_backfill_missing_published_at_for_historical_rows(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/admin/articles",
        json={
            "title": "Backfill PublishedAt",
            "content": "backfill content",
        },
        headers=auth_headers,
    )
    article_id = create_resp.json()["data"]["id"]
    await client.post(f"/api/v1/admin/articles/{article_id}/publish", headers=auth_headers)

    # 模拟历史脏数据：状态为已发布，但 published_at 为空。
    await Article.filter(id=article_id).update(published_at=None)

    from app.modules.articles.service import ArticleService
    backfilled = await ArticleService.backfill_missing_published_at()
    assert backfilled >= 1

    refreshed = await Article.get(id=article_id)
    assert refreshed.status == "published"
    assert refreshed.published_at is not None


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
