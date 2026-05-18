import time
import asyncio
import logging
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings


logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


async def _persist_api_call_log(
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: int,
    ip_address: str,
):
    try:
        from app.modules.statistics.models import APICallLog
        await APICallLog.create(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
        )
    except Exception as e:
        logger.error(f"Failed to log API call: {e}")


async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    process_time_ms = int(process_time * 1000)
    
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.3f}s with status {response.status_code}"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    
    # 静态媒体与健康检查不落库，避免图片密集请求拖慢主流程。
    path = request.url.path
    if path.startswith("/media/") or path == "/health":
        return response

    ip_address = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    if isinstance(ip_address, str) and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()
    asyncio.create_task(
        _persist_api_call_log(
            endpoint=str(request.url.path),
            method=request.method,
            status_code=response.status_code,
            response_time_ms=process_time_ms,
            ip_address=ip_address if isinstance(ip_address, str) else "unknown",
        )
    )
    
    return response


def setup_middlewares(app: FastAPI):
    app.middleware("http")(log_requests)
    
    if settings.RATE_LIMIT_ENABLED:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
