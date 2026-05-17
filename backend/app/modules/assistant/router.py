from typing import Optional
import logging

from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from redis.asyncio import Redis

from app.common.response import success
from app.core.dependencies import get_current_admin_optional, get_guest_identity, get_redis, get_client_ip
from app.modules.assistant import service
from app.modules.assistant.schemas import AssistantChatRequest
from app.modules.auth.models import AdminUser
from app.modules.comments.models import GuestIdentity

router = APIRouter(prefix="/assistant", tags=["Assistant"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=dict)
async def assistant_chat(
    payload: AssistantChatRequest,
    request: Request,
    response: Response,
    guest: GuestIdentity = Depends(get_guest_identity),
    redis: Redis = Depends(get_redis),
    admin: Optional[AdminUser] = Depends(get_current_admin_optional),
):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员登录状态已失效，请重新登录",
        )

    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    identity_keys, ttl_seconds = await service.check_daily_rate_limit(
        redis=redis,
        admin=admin,
        guest=guest,
        ip=ip,
        user_agent=user_agent,
    )
    try:
        await service.consume_daily_rate_limit(
            redis=redis,
            identity_keys=identity_keys,
            ttl_seconds=ttl_seconds,
        )
    except Exception:
        logger.exception("assistant rate-limit consume failed")
    result = await service.chat_with_n8n(payload)
    if not admin:
        response.set_cookie(
            key="guest_token",
            value=guest.guest_token,
            max_age=365 * 24 * 60 * 60,
            httponly=True,
            samesite="lax",
        )
    return success(result.model_dump())
