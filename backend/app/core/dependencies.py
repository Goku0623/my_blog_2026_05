from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token, generate_guest_token
from app.core.redis_client import get_redis_client
from app.modules.auth.models import AdminUser, TokenBlacklist
from app.modules.comments.models import GuestIdentity


security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_redis():
    return await get_redis_client()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AdminUser:
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    jti = payload.get("jti")
    if jti:
        is_blacklisted = await TokenBlacklist.filter(jti=jti).exists()
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    user = await AdminUser.get_or_none(id=int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    return user


async def get_current_admin_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[AdminUser]:
    if not credentials:
        return None
    try:
        return await get_current_admin(credentials)
    except HTTPException:
        return None


async def get_guest_identity(
    request: Request,
    guest_token: Optional[str] = Cookie(None),
) -> GuestIdentity:
    token = guest_token or request.headers.get("X-Guest-Token")
    
    if token:
        guest = await GuestIdentity.get_or_none(guest_token=token)
        if guest and not guest.is_banned:
            return guest
    
    new_token = generate_guest_token()
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    guest = await GuestIdentity.create(
        guest_token=new_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return guest


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"

