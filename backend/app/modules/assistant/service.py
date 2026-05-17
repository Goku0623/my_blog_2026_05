import os
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from redis.asyncio import Redis

from app.common.exceptions import BadRequestException, BusinessException
from app.modules.auth.models import AdminUser
from app.modules.comments.models import GuestIdentity
from app.modules.assistant.schemas import AssistantChatRequest, AssistantChatResponse
from app.modules.system.models import SiteConfig

DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_WEBHOOK_RESPONSE_PATHS = (
    ("data", "reply"),
    ("reply",),
    ("answer",),
    ("output",),
    ("text",),
    ("message",),
)


def build_visitor_fingerprint(ip: str, user_agent: str) -> str:
    normalized_ip = (ip or "unknown").strip()
    normalized_ua = (user_agent or "unknown").strip().lower()
    raw = f"{normalized_ip}|{normalized_ua}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def check_daily_rate_limit(
    redis: Redis,
    *,
    admin: Optional[AdminUser],
    guest: GuestIdentity,
    ip: str,
    user_agent: str,
) -> tuple[list[str], int]:
    date_key = datetime.now().strftime("%Y%m%d")
    if admin:
        return [], 0

    guest_limit_raw = await _get_config_value("ASSISTANT_GUEST_DAILY_LIMIT", "3")
    try:
        guest_daily_limit = max(0, int((guest_limit_raw or "3").strip()))
    except (TypeError, ValueError):
        guest_daily_limit = 3
    if guest_daily_limit == 0:
        return [], 0

    fingerprint = build_visitor_fingerprint(ip, user_agent)
    identity_keys = [
        f"assistant_rate_limit:guest:{guest.guest_token}:{date_key}",
        f"assistant_rate_limit:fp:{fingerprint}:{date_key}",
    ]

    ttl_seconds = 2 * 24 * 60 * 60

    for key in identity_keys:
        current_raw = await redis.get(key)
        current = int(current_raw) if current_raw is not None else 0
        if current >= guest_daily_limit:
            raise BusinessException(429, f"您每天只能提问{guest_daily_limit}次，明天再来吧")
    return identity_keys, ttl_seconds


async def consume_daily_rate_limit(
    redis: Redis,
    *,
    identity_keys: list[str],
    ttl_seconds: int,
) -> None:
    for key in identity_keys:
        new_count = await redis.incr(key)
        if new_count == 1:
            await redis.expire(key, ttl_seconds)


async def _get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    config = await SiteConfig.get_or_none(key=key)
    if config and config.value not in (None, ""):
        return config.value
    return os.getenv(key, default)


def _extract_text_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    for path in DEFAULT_WEBHOOK_RESPONSE_PATHS:
        current: Any = payload
        valid = True
        for segment in path:
            if isinstance(current, dict) and segment in current:
                current = current[segment]
            else:
                valid = False
                break
        if valid and isinstance(current, str) and current.strip():
            return current.strip()

    data = payload.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            for key in ("reply", "message", "text", "output"):
                value = first.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return None


def _extract_session_id_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    for key in ("session_id", "sessionId", "conversation_id", "conversationId"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("session_id", "sessionId", "conversation_id", "conversationId"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


async def chat_with_n8n(request: AssistantChatRequest) -> AssistantChatResponse:
    webhook_url = await _get_config_value("N8N_ASSISTANT_WEBHOOK_URL")
    webhook_secret = await _get_config_value("N8N_SECRET")

    if not webhook_url:
        raise BusinessException(500, "N8N_ASSISTANT_WEBHOOK_URL 未配置")

    outgoing_payload: Dict[str, Any] = {
        "message": request.message,
        "session_id": request.session_id,
        "history": [item.model_dump() for item in request.history],
    }

    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if webhook_secret:
        headers["X-N8N-Secret"] = webhook_secret

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
            response = await client.post(webhook_url, json=outgoing_payload, headers=headers)
    except httpx.HTTPError as exc:
        raise BusinessException(502, f"机器人服务请求失败: {str(exc)}") from exc

    if response.status_code >= 400:
        detail = response.text.strip()
        raise BusinessException(502, f"机器人服务返回异常: {detail or response.status_code}")

    response_json: Dict[str, Any]
    try:
        response_json = response.json()
    except ValueError as exc:
        raise BadRequestException("机器人服务返回了非 JSON 数据") from exc

    reply_text = _extract_text_from_payload(response_json)
    if not reply_text:
        raise BadRequestException("机器人服务返回格式不正确，缺少 reply 字段")

    session_id = _extract_session_id_from_payload(response_json) or request.session_id
    return AssistantChatResponse(reply=reply_text, session_id=session_id)
