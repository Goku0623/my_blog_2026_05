from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.modules.auth.schemas import (
    AdminUserOut,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
)
from app.modules.auth.service import AuthService, RateLimitException
from app.core.dependencies import get_current_admin, get_client_ip
from app.core.security import decode_token
from app.modules.auth.models import AdminUser
from app.common.response import success, error
from app.common.exceptions import UnauthorizedException, BadRequestException


router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=dict)
@limiter.limit("10/minute")
async def login(request: Request, login_data: LoginRequest):
    try:
        ip_address = get_client_ip(request)
        
        admin = await AuthService.authenticate_admin(
            login_data.username,
            login_data.password,
            ip_address
        )
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        tokens = await AuthService.create_token_pair(admin)
        return success(tokens, "Login successful")
        
    except HTTPException:
        raise
    except RateLimitException as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_data: RefreshRequest):
    try:
        tokens = await AuthService.refresh_access_token(refresh_data.refresh_token)
        return success(tokens, "Token refreshed successfully")
        
    except HTTPException:
        raise
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while refreshing token"
        )


@router.post("/logout", response_model=dict)
async def logout(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )
        
        access_token = auth_header.split(" ")[1]
        access_payload = decode_token(access_token)
        
        if not access_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            )
        
        access_jti = access_payload.get("jti", "")
        access_exp = access_payload.get("exp", 0)
        access_ttl = access_exp - int(datetime.now(timezone.utc).timestamp())
        
        refresh_jti = ""
        refresh_ttl = 0
        
        await AuthService.logout(access_jti, refresh_jti, access_ttl, refresh_ttl)
        
        return success(None, "Logout successful")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )


@router.get("/me", response_model=dict)
async def get_current_user_info(current_admin: AdminUser = Depends(get_current_admin)):
    try:
        return success(AdminUserOut.model_validate(current_admin))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching user info"
        )


@router.put("/me", response_model=dict)
async def update_current_user_info(
    profile_data: UpdateProfileRequest,
    current_admin: AdminUser = Depends(get_current_admin),
):
    try:
        admin = await AuthService.update_profile(
            current_admin,
            profile_data.username,
            profile_data.email,
        )
        return success(AdminUserOut.model_validate(admin), "Profile updated successfully")
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating profile"
        )


@router.put("/change-password", response_model=dict)
async def change_password(
    password_data: ChangePasswordRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        await AuthService.change_password(
            current_admin,
            password_data.old_password,
            password_data.new_password
        )
        
        return success(None, "Password changed successfully")
        
    except HTTPException:
        raise
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing password"
        )
