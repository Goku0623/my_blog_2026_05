from fastapi import APIRouter, Depends, Header, Query, Request
from redis.asyncio import Redis

from app.common.response import success
from app.common.exceptions import UnauthorizedException
from app.core.dependencies import get_current_admin, get_redis, get_client_ip
from app.modules.auth.models import AdminUser
from app.modules.ai.schemas import (
    N8NArticlePayload,
    WeatherResponse,
    AICommentReplyRequest,
    AICommentReplyResponse,
)
from app.modules.ai import service


router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/n8n/article", response_model=dict)
async def receive_n8n_article(
    payload: N8NArticlePayload,
    x_n8n_secret: str = Header(None, alias="X-N8N-Secret"),
):
    if not x_n8n_secret:
        raise UnauthorizedException("缺少 N8N 密钥")

    article = await service.receive_n8n_article(payload, x_n8n_secret)

    if article.status == article.STATUS_DRAFT:
        from app.tasks.notification_tasks import send_n8n_draft_email_safe

        await send_n8n_draft_email_safe(article.title, article.id, article.slug)

    return success({
        "article_id": article.id,
        "title": article.title,
        "status": article.status,
        "message": "文章已创建为草稿，请登录后台编辑发布",
    })


@router.get("/weather", response_model=dict)
async def get_weather(
    request: Request,
    latitude: float = None,
    longitude: float = None,
    city: str = None,
    redis: Redis = Depends(get_redis),
):
    ip = get_client_ip(request)
    
    weather = await service.get_weather(
        ip=ip,
        lat=latitude,
        lon=longitude,
        city=city,
        redis=redis,
    )
    
    return success(weather.model_dump())


@router.get("/admin/weather/city-lookup", response_model=dict)
async def lookup_weather_city_code(
    keyword: str = Query(..., min_length=1, description="城市名称，例如 深圳"),
    admin: AdminUser = Depends(get_current_admin),
):
    _ = admin
    result = await service.lookup_amap_city_code(keyword)
    return success(result)


@router.post("/admin/comment-reply", response_model=dict)
async def generate_comment_reply(
    request: AICommentReplyRequest,
    admin: AdminUser = Depends(get_current_admin),
    redis: Redis = Depends(get_redis),
):
    response = await service.generate_comment_reply(
        request=request,
        admin_username=admin.username,
        redis=redis,
    )
    
    return success(response.model_dump())
