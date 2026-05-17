from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.middleware import setup_middlewares
from app.common.exceptions import setup_exception_handlers

from app.modules.auth.router import router as auth_router
from app.modules.articles.router import router as articles_router
from app.modules.comments.router import router as comments_router
from app.modules.guestbook.router import router as guestbook_router
from app.modules.ai.router import router as ai_router
from app.modules.system.router import router as system_router
from app.modules.statistics.router import router as statistics_router
from app.modules.assistant.router import router as assistant_router
from app.modules.ai.init_config import init_ai_configs
from app.modules.system.service import SiteConfigService
from app.modules.system.models import SiteConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_ai_configs()
    await SiteConfigService.init_default_configs()
    await _ensure_site_started_at()
    yield
    await close_db()


async def _ensure_site_started_at():
    env_value = (settings.SITE_STARTED_AT or "").strip()
    if env_value:
        try:
            datetime.fromisoformat(env_value)
        except ValueError:
            pass
        else:
            existing = await SiteConfig.get_or_none(key="SITE_STARTED_AT")
            if not existing:
                await SiteConfig.create(
                    key="SITE_STARTED_AT",
                    value=env_value,
                    value_type="str",
                    description="站点上线时间（由环境变量 SITE_STARTED_AT 设置）",
                    is_public=True,
                )
            elif existing.value != env_value:
                existing.value = env_value
                await existing.save()
            return

    existing = await SiteConfig.get_or_none(key="SITE_STARTED_AT")
    if not existing:
        await SiteConfig.create(
            key="SITE_STARTED_AT",
            value=datetime.now(timezone.utc).isoformat(),
            value_type="str",
            description="站点首次启动时间（自动记录）",
            is_public=True,
        )
    elif not existing.value:
        existing.value = datetime.now(timezone.utc).isoformat()
        await existing.save()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_middlewares(app)
setup_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(articles_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")
app.include_router(guestbook_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(statistics_router, prefix="/api/v1")
app.include_router(assistant_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Blog API", "version": settings.APP_VERSION}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
