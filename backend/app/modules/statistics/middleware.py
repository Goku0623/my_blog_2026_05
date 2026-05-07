import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from app.modules.statistics.models import APICallLog
from app.core.dependencies import get_client_ip


class APILogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/static") or request.url.path.startswith("/docs"):
            return await call_next(request)
        
        start_time = time.time()
        error_message = None
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            response_time_ms = int((time.time() - start_time) * 1000)
            
            try:
                await APICallLog.create(
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    ip_address=get_client_ip(request),
                    error_message=None
                )
            except Exception:
                pass
            
            return response
        except Exception as e:
            error_message = str(e)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            try:
                await APICallLog.create(
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    ip_address=get_client_ip(request),
                    error_message=error_message
                )
            except Exception:
                pass
            
            raise
