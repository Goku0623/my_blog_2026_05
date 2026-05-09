from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.middleware import setup_middlewares
from app.common.exceptions import setup_exception_handlers

from app.modules.auth.router import router as auth_router
from app.modules.articles.router import router as articles_router
from app.modules.comments.router import router as comments_router
from app.modules.ai.router import router as ai_router
from app.modules.system.router import router as system_router
from app.modules.statistics.router import router as statistics_router
from app.modules.ai.init_config import init_ai_configs
from app.modules.system.service import SiteConfigService


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_ai_configs()
    await SiteConfigService.init_default_configs()
    yield
    await close_db()


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
app.include_router(ai_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(statistics_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Blog API", "version": settings.APP_VERSION}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
