from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status

from app.modules.auth.models import AdminUser, LoginAttempt, TokenBlacklist
from app.modules.auth.schemas import TokenResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.redis_client import get_redis_client
from app.core.config import settings
from app.common.exceptions import BadRequestException, UnauthorizedException, ForbiddenException


class RateLimitException(Exception):
    pass


class AuthService:
    @staticmethod
    async def authenticate_admin(username: str, password: str, ip_address: str) -> Optional[AdminUser]:
        cutoff = datetime.now() - timedelta(minutes=15)
        recent_attempts = await LoginAttempt.filter(
            ip_address=ip_address,
            username_tried=username,
            success=False,
        ).values_list("attempted_at", flat=True)
        failed_attempts = 0
        for attempted_at in recent_attempts:
            if attempted_at is None:
                continue
            cutoff_for_compare = cutoff
            if attempted_at.tzinfo and cutoff.tzinfo is None:
                cutoff_for_compare = cutoff.replace(tzinfo=attempted_at.tzinfo)
            if attempted_at >= cutoff_for_compare:
                failed_attempts += 1
        
        if failed_attempts >= 5:
            raise RateLimitException("Too many failed login attempts. Please try again later.")
        
        user = await AdminUser.get_or_none(username=username)
        
        if not user or not verify_password(password, user.hashed_password):
            await LoginAttempt.create(
                ip_address=ip_address,
                username_tried=username,
                success=False,
            )
            return None
        
        if not user.is_active:
            await LoginAttempt.create(
                ip_address=ip_address,
                username_tried=username,
                success=False,
            )
            raise ForbiddenException("User account is inactive")
        
        user.last_login_at = datetime.now()
        await user.save()
        
        await LoginAttempt.create(
            ip_address=ip_address,
            username_tried=username,
            success=True,
        )
        await LoginAttempt.filter(
            ip_address=ip_address,
            username_tried=username,
            success=False,
        ).delete()
        
        return user

    @staticmethod
    async def create_token_pair(admin: AdminUser) -> dict:
        access_token = create_access_token({"sub": str(admin.id)})
        refresh_token = create_refresh_token({"sub": str(admin.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        
        if not payload:
            raise UnauthorizedException("Invalid refresh token")
        
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Token type must be refresh")
        
        jti = payload.get("jti")
        if jti:
            redis = await get_redis_client()
            is_blacklisted = await redis.get(f"blacklist:{jti}")
            if is_blacklisted:
                raise UnauthorizedException("Token has been revoked")
        
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")
        
        admin = await AdminUser.get_or_none(id=int(user_id))
        if not admin or not admin.is_active:
            raise UnauthorizedException("User not found or inactive")
        
        if jti:
            redis = await get_redis_client()
            exp = payload.get("exp")
            if exp:
                ttl = exp - int(datetime.now(timezone.utc).timestamp())
                if ttl > 0:
                    await redis.setex(f"blacklist:{jti}", ttl, "1")
        
        new_access_token = create_access_token({"sub": str(admin.id)})
        
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @staticmethod
    async def logout(access_jti: str, refresh_jti: str, access_ttl: int, refresh_ttl: int):
        redis = await get_redis_client()
        
        if access_ttl > 0:
            await redis.setex(f"blacklist:{access_jti}", access_ttl, "1")
        
        if refresh_ttl > 0:
            await redis.setex(f"blacklist:{refresh_jti}", refresh_ttl, "1")
        
        await TokenBlacklist.create(
            jti=access_jti,
            token_type="access",
            expired_at=datetime.now() + timedelta(seconds=access_ttl),
        )
        
        await TokenBlacklist.create(
            jti=refresh_jti,
            token_type="refresh",
            expired_at=datetime.now() + timedelta(seconds=refresh_ttl),
        )

    @staticmethod
    async def change_password(admin: AdminUser, old_password: str, new_password: str):
        if not verify_password(old_password, admin.hashed_password):
            raise BadRequestException("Old password is incorrect")
        
        if old_password == new_password:
            raise BadRequestException("New password must be different from old password")
        
        admin.hashed_password = hash_password(new_password)
        await admin.save()

    @staticmethod
    async def update_profile(admin: AdminUser, username: str, email: Optional[str], avatar: Optional[str] = None):
        username = username.strip()
        if not username:
            raise BadRequestException("Username cannot be empty")

        username_owner = await AdminUser.get_or_none(username=username)
        if username_owner and username_owner.id != admin.id:
            raise BadRequestException("Username already exists")

        normalized_email = (email or "").strip() or None
        if normalized_email:
            email_owner = await AdminUser.get_or_none(email=normalized_email)
            if email_owner and email_owner.id != admin.id:
                raise BadRequestException("Email already exists")

        admin.username = username
        admin.email = normalized_email
        if avatar is not None:
            normalized_avatar = avatar.strip()
            if normalized_avatar and not normalized_avatar.startswith("data:image/"):
                raise BadRequestException("avatar must be a data:image base64 URL")
            admin.avatar = normalized_avatar or None
        await admin.save()

        # 同步 ADMIN_EMAIL 配置项，确保"关于我"等公开页面展示最新邮箱。
        from app.modules.system.models import SiteConfig
        from app.core.redis_client import get_redis_client
        admin_email_config = await SiteConfig.get_or_none(key="ADMIN_EMAIL")
        if admin_email_config:
            admin_email_config.value = normalized_email or ""
            await admin_email_config.save()
            redis = await get_redis_client()
            await redis.delete("config:ADMIN_EMAIL")

        # 同步管理员对应的评论身份昵称，避免前端不同模块出现旧昵称。
        from app.modules.comments.models import GuestIdentity
        admin_guest = await GuestIdentity.get_or_none(guest_token=f"admin-{admin.id}")
        if admin_guest:
            admin_guest.nickname = username
            try:
                await admin_guest.save()
            except Exception:
                # GuestIdentity 昵称有唯一约束，冲突时保持原值；
                # 展示层仍会优先解析为当前管理员用户名。
                pass

        return admin

    @staticmethod
    async def create_first_admin():
        existing_admin = await AdminUser.first()
        if existing_admin:
            return None
        
        admin = await AdminUser.create(
            username="admin",
            email="admin@example.com",
            hashed_password=hash_password("admin123456"),
            is_active=True,
        )
        
        return admin
