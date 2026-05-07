import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise

from app.common.exceptions import setup_exception_handlers
from app.core.middleware import setup_middlewares
from app.core.security import create_access_token
from app.modules.auth.models import AdminUser
from app.modules.articles.models import Article
from app.modules.comments.models import GuestIdentity
from app.modules.auth.router import router as auth_router
from app.modules.articles.router import router as articles_router
from app.modules.comments.router import router as comments_router
from app.modules.chatroom.router import router as chatroom_router
from app.modules.ai.router import router as ai_router
from app.modules.system.router import router as system_router
from app.modules.statistics.router import router as statistics_router


MODEL_MODULES = [
    "app.modules.auth.models",
    "app.modules.articles.models",
    "app.modules.comments.models",
    "app.modules.chatroom.models",
    "app.modules.system.models",
    "app.modules.statistics.models",
]


class FakeRedis:
    def __init__(self):
        self._store: dict[str, str] = {}
        self._zsets: dict[str, list[tuple[float, str]]] = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value):
        self._store[key] = str(value)
        return True

    async def incr(self, key: str):
        current = int(self._store.get(key, "0")) + 1
        self._store[key] = str(current)
        return current

    async def delete(self, key: str):
        self._store.pop(key, None)
        self._zsets.pop(key, None)
        return True

    async def keys(self, pattern: str):
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [key for key in self._store.keys() if key.startswith(prefix)]
        return [key for key in self._store.keys() if key == pattern]

    async def expire(self, key: str, ttl: int):
        return key in self._store or key in self._zsets

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float):
        zset = self._zsets.get(key, [])
        self._zsets[key] = [
            (score, member) for score, member in zset if not (min_score <= score <= max_score)
        ]
        return True

    async def zcard(self, key: str):
        return len(self._zsets.get(key, []))

    async def zadd(self, key: str, mapping: dict[str, float]):
        zset = self._zsets.setdefault(key, [])
        for member, score in mapping.items():
            zset.append((score, member))
        return True

    async def close(self):
        return None


@pytest_asyncio.fixture
async def fake_redis():
    return FakeRedis()


@pytest_asyncio.fixture
async def db_setup(monkeypatch, fake_redis):

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.auth.service.get_redis_client", _get_redis)
    monkeypatch.setattr("app.modules.articles.service.get_redis_client", _get_redis)
    monkeypatch.setattr("app.core.dependencies.get_redis_client", _get_redis)
    monkeypatch.setattr("app.modules.system.service.get_redis_client", _get_redis)
    monkeypatch.setattr("app.modules.chatroom.ws_manager.get_redis_client", _get_redis)
    monkeypatch.setattr(
        "app.modules.auth.service.verify_password",
        lambda plain, hashed: plain == hashed,
    )
    monkeypatch.setattr("app.modules.auth.service.hash_password", lambda value: value)

    await Tortoise.init(db_url="sqlite://:memory:", modules={"models": MODEL_MODULES})
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client(db_setup):
    test_app = FastAPI()
    setup_middlewares(test_app)
    setup_exception_handlers(test_app)
    test_app.include_router(auth_router, prefix="/api/v1")
    test_app.include_router(articles_router, prefix="/api/v1")
    test_app.include_router(comments_router, prefix="/api/v1")
    test_app.include_router(chatroom_router, prefix="/api/v1")
    test_app.include_router(ai_router, prefix="/api/v1")
    test_app.include_router(system_router, prefix="/api/v1")
    test_app.include_router(statistics_router, prefix="/api/v1")

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def create_admin(db_setup):
    async def _create_admin(
        username: str = "test_admin",
        email: str = "admin@example.com",
        password: str = "admin123456",
        is_active: bool = True,
    ):
        return await AdminUser.create(
            username=username,
            email=email,
            hashed_password=password,
            is_active=is_active,
        )

    return _create_admin


@pytest_asyncio.fixture
async def create_article(db_setup):
    async def _create_article(
        title: str = "Test Article",
        slug: str = "test-article",
        content: str = "content",
        status: str = Article.STATUS_DRAFT,
        allow_comment: bool = True,
    ):
        return await Article.create(
            title=title,
            slug=slug,
            content=content,
            status=status,
            allow_comment=allow_comment,
        )

    return _create_article


@pytest_asyncio.fixture
async def create_guest(db_setup):
    async def _create_guest(
        guest_token: str = "guest_token",
        nickname: str | None = "guest",
        ip_address: str = "127.0.0.1",
        user_agent: str = "pytest",
    ):
        return await GuestIdentity.create(
            guest_token=guest_token,
            nickname=nickname,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    return _create_guest


@pytest_asyncio.fixture
async def admin_token(create_admin):
    admin = await create_admin()
    return create_access_token({"sub": str(admin.id)})


@pytest_asyncio.fixture
async def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
