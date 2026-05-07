import pytest
from httpx import AsyncClient

from app.core.security import decode_token
from app.modules.auth.models import LoginAttempt, TokenBlacklist
from app.modules.auth.router import AuthService, RateLimitException


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, create_admin):
    await create_admin(username="admin_login_ok", email="login_ok@example.com")

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_login_ok", "password": "admin123456"},
        headers={"X-Forwarded-For": "198.51.100.1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, create_admin):
    await create_admin(username="admin_wrong_pwd", email="wrong_pwd@example.com")

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_wrong_pwd", "password": "wrong-password"},
        headers={"X-Forwarded-For": "198.51.100.2"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


@pytest.mark.asyncio
async def test_login_rate_limit(client: AsyncClient, monkeypatch, create_admin):
    await create_admin(username="admin_rate_limit", email="rate_limit@example.com")

    for _ in range(5):
        await LoginAttempt.create(
            ip_address="127.0.0.1",
            username_tried="admin_rate_limit",
            success=False,
        )

    async def _mock_rate_limit(*args, **kwargs):
        raise RateLimitException("Too many failed login attempts. Please try again later.")

    monkeypatch.setattr(AuthService, "authenticate_admin", _mock_rate_limit)

    blocked = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_rate_limit", "password": "bad-pass"},
    )
    assert blocked.status_code == 429
    assert "Too many failed login attempts" in blocked.json()["detail"]

    failed_attempts = await LoginAttempt.filter(
        ip_address="127.0.0.1",
        success=False,
    ).count()
    assert failed_attempts == 5


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, create_admin):
    await create_admin(username="admin_refresh", email="refresh@example.com")
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_refresh", "password": "admin123456"},
        headers={"X-Forwarded-For": "198.51.100.3"},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    refresh_data = refresh_resp.json()
    assert refresh_data["code"] == 0
    assert refresh_data["data"]["access_token"]
    assert refresh_data["data"]["refresh_token"] == refresh_token


@pytest.mark.asyncio
async def test_logout_and_token_invalidation(client: AsyncClient, create_admin):
    await create_admin(username="admin_logout", email="logout@example.com")
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_logout", "password": "admin123456"},
        headers={"X-Forwarded-For": "198.51.100.4"},
    )
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    me_before = await client.get("/api/v1/auth/me", headers=headers)
    assert me_before.status_code == 200

    logout_resp = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["code"] == 0

    me_after = await client.get("/api/v1/auth/me", headers=headers)
    assert me_after.status_code == 401
    assert me_after.json()["detail"] == "Token has been revoked"


@pytest.mark.asyncio
async def test_access_protected_with_blacklisted_token(client: AsyncClient, create_admin):
    admin = await create_admin(username="admin_blacklist", email="blacklist@example.com")

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin_blacklist", "password": "admin123456"},
        headers={"X-Forwarded-For": "198.51.100.5"},
    )
    access_token = login_resp.json()["data"]["access_token"]
    token_payload = decode_token(access_token)
    assert token_payload is not None

    await TokenBlacklist.create(
        jti=token_payload["jti"],
        token_type="access",
        expired_at=admin.created_at,
    )

    denied = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert denied.status_code == 401
    assert denied.json()["detail"] == "Token has been revoked"
