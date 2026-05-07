import pytest
from httpx import AsyncClient

from app.modules.system.models import ScheduledTask, SiteConfig


@pytest.mark.asyncio
async def test_public_configs(client: AsyncClient):
    await SiteConfig.create(
        key="SITE_NAME",
        value="Blog",
        value_type="str",
        description="site name",
        is_public=True,
    )

    response = await client.get("/api/v1/system/configs/public")
    assert response.status_code == 200
    assert response.json()["data"]["SITE_NAME"] == "Blog"


@pytest.mark.asyncio
async def test_update_and_bulk_update_configs(client: AsyncClient, auth_headers: dict):
    await SiteConfig.create(
        key="APP_THEME",
        value="light",
        value_type="str",
        description="theme",
        is_public=False,
    )
    await SiteConfig.create(
        key="APP_FOOTER",
        value="old",
        value_type="str",
        description="footer",
        is_public=False,
    )

    update_resp = await client.put(
        "/api/v1/admin/system/configs/APP_THEME",
        json={"value": "dark"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["value"] == "dark"

    bulk_resp = await client.post(
        "/api/v1/admin/system/configs/bulk",
        json={
            "configs": [
                {"key": "APP_THEME", "value": "blue"},
                {"key": "APP_FOOTER", "value": "new"},
            ]
        },
        headers=auth_headers,
    )
    assert bulk_resp.status_code == 200
    values = {item["key"]: item["value"] for item in bulk_resp.json()["data"]}
    assert values["APP_THEME"] == "blue"
    assert values["APP_FOOTER"] == "new"


@pytest.mark.asyncio
async def test_sensitive_word_crud(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/admin/system/sensitive-words",
        json={"word": "blocked-word", "category": "spam"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 200
    word_id = create_resp.json()["data"]["id"]

    list_resp = await client.get("/api/v1/admin/system/sensitive-words", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(item["word"] == "blocked-word" for item in list_resp.json()["data"])

    refresh_resp = await client.post(
        "/api/v1/admin/system/sensitive-words/refresh-cache",
        headers=auth_headers,
    )
    assert refresh_resp.status_code == 200

    delete_resp = await client.delete(
        f"/api/v1/admin/system/sensitive-words/{word_id}",
        headers=auth_headers,
    )
    assert delete_resp.status_code == 200


@pytest.mark.asyncio
async def test_scheduled_tasks_endpoints(client: AsyncClient, auth_headers: dict):
    task = await ScheduledTask.create(
        name="nightly_backup",
        task_path="app.tasks.backup",
        cron_expression="0 2 * * *",
        is_active=True,
    )

    list_resp = await client.get("/api/v1/admin/system/tasks", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(item["name"] == "nightly_backup" for item in list_resp.json()["data"])

    update_resp = await client.put(
        f"/api/v1/admin/system/tasks/{task.id}",
        json={"is_active": False},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["is_active"] is False

    trigger_resp = await client.post(
        f"/api/v1/admin/system/tasks/{task.id}/trigger",
        headers=auth_headers,
    )
    assert trigger_resp.status_code == 200
    assert "nightly_backup" in trigger_resp.json()["data"]["message"]
