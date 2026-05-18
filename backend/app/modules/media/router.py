from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.common.response import success
from app.core.config import settings
from app.core.dependencies import get_current_admin
from app.modules.auth.models import AdminUser
from app.modules.media.schemas import MediaFetchRequest
from app.modules.media.service import MediaService


router = APIRouter(prefix="/admin/media", tags=["Media Admin"])


def _resolve_upload_options(purpose: str) -> tuple[str, int, int]:
    if purpose == "cover":
        max_mb = max(1, min(20, settings.MAX_UPLOAD_SIZE // (1024 * 1024) if settings.MAX_UPLOAD_SIZE > 0 else 5))
        max_bytes = max_mb * 1024 * 1024
        return "articles/covers/original", max_bytes, 2000
    return "articles/content", max(settings.MAX_UPLOAD_SIZE, 5 * 1024 * 1024), 2000


@router.post("/upload", response_model=dict)
async def upload_image(
    file: UploadFile = File(...),
    purpose: str = Query("content", pattern="^(cover|content)$"),
    _: AdminUser = Depends(get_current_admin),
):
    try:
        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty file")
        folder, max_bytes, max_edge = _resolve_upload_options(purpose)
        saved = MediaService.save_image_bytes(payload, folder=folder, max_bytes=max_bytes, max_edge=max_edge)
        return success(saved)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/fetch", response_model=dict)
async def fetch_image(
    data: MediaFetchRequest,
    _: AdminUser = Depends(get_current_admin),
):
    try:
        folder, max_bytes, max_edge = _resolve_upload_options(data.purpose)
        saved = await MediaService.save_image_from_url(
            data.url,
            folder=folder,
            max_bytes=max_bytes,
            max_edge=max_edge,
        )
        return success(saved)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
