import hashlib
import io
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageOps, UnidentifiedImageError

from app.common.exceptions import BadRequestException
from app.core.config import settings


class MediaService:
    MEDIA_URL_PREFIX = "/media"
    DEFAULT_HTTP_TIMEOUT_SECONDS = 15
    MAX_IMAGE_EDGE = 2400
    ENCODE_QUALITIES = (88, 80, 72, 64, 56, 48, 40)
    RESIZE_SCALE_FACTORS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5)

    @staticmethod
    def _upload_root() -> Path:
        root = Path(settings.UPLOAD_DIR).resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _normalize_relative_path(relative_path: str) -> str:
        return relative_path.replace("\\", "/").lstrip("/")

    @staticmethod
    def to_public_url(relative_path: str) -> str:
        normalized = MediaService._normalize_relative_path(relative_path)
        return f"{MediaService.MEDIA_URL_PREFIX}/{normalized}"

    @staticmethod
    def extract_relative_path_from_url(url: str) -> Optional[str]:
        value = (url or "").strip()
        if not value:
            return None
        if value.startswith(MediaService.MEDIA_URL_PREFIX + "/"):
            return MediaService._normalize_relative_path(value[len(MediaService.MEDIA_URL_PREFIX) + 1 :])

        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and parsed.path.startswith(MediaService.MEDIA_URL_PREFIX + "/"):
            return MediaService._normalize_relative_path(parsed.path[len(MediaService.MEDIA_URL_PREFIX) + 1 :])
        return None

    @staticmethod
    def resolve_disk_path(url_or_relative_path: str) -> Optional[Path]:
        relative = MediaService.extract_relative_path_from_url(url_or_relative_path)
        if not relative:
            normalized = MediaService._normalize_relative_path(url_or_relative_path)
            if normalized == url_or_relative_path.strip():
                relative = normalized
        if not relative:
            return None
        return MediaService._upload_root() / relative

    @staticmethod
    def read_image_bytes(url_or_relative_path: str) -> bytes:
        disk_path = MediaService.resolve_disk_path(url_or_relative_path)
        if disk_path is None or not disk_path.exists() or not disk_path.is_file():
            raise BadRequestException("stored image does not exist")
        return disk_path.read_bytes()

    @staticmethod
    def _ensure_max_edge(image: Image.Image, max_edge: int) -> Image.Image:
        if max_edge <= 0:
            return image
        width, height = image.size
        long_edge = max(width, height)
        if long_edge <= max_edge:
            return image
        scale = max_edge / long_edge
        target_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        resampling = getattr(Image, "Resampling", Image).LANCZOS
        return image.resize(target_size, resampling)

    @staticmethod
    def _encode_jpeg_with_size_limit(
        rgb_image: Image.Image,
        *,
        max_bytes: Optional[int] = None,
    ) -> bytes:
        width, height = rgb_image.size
        resampling = getattr(Image, "Resampling", Image).LANCZOS

        for scale in MediaService.RESIZE_SCALE_FACTORS:
            image_for_scale = rgb_image
            if scale != 1.0:
                image_for_scale = rgb_image.resize(
                    (max(1, int(width * scale)), max(1, int(height * scale))),
                    resampling,
                )

            for quality in MediaService.ENCODE_QUALITIES:
                buffer = io.BytesIO()
                image_for_scale.save(buffer, format="JPEG", optimize=True, quality=quality)
                data = buffer.getvalue()
                if max_bytes is None or len(data) <= max_bytes:
                    return data

        raise BadRequestException("image cannot be compressed below configured limit")

    @staticmethod
    def normalize_image_bytes(
        image_bytes: bytes,
        *,
        max_bytes: Optional[int] = None,
        max_edge: int = MAX_IMAGE_EDGE,
    ) -> tuple[bytes, int, int]:
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                image = ImageOps.exif_transpose(image)
                rgb = image.convert("RGB")
                rgb = MediaService._ensure_max_edge(rgb, max_edge)
                encoded = MediaService._encode_jpeg_with_size_limit(rgb, max_bytes=max_bytes)
                return encoded, rgb.width, rgb.height
        except UnidentifiedImageError:
            raise BadRequestException("invalid image file")
        except OSError:
            raise BadRequestException("image cannot be processed")

    @staticmethod
    def save_image_bytes(
        image_bytes: bytes,
        *,
        folder: str,
        max_bytes: Optional[int] = None,
        max_edge: int = MAX_IMAGE_EDGE,
    ) -> dict:
        normalized_bytes, width, height = MediaService.normalize_image_bytes(
            image_bytes,
            max_bytes=max_bytes,
            max_edge=max_edge,
        )
        digest = hashlib.sha256(normalized_bytes).hexdigest()
        date_path = datetime.now().strftime("%Y/%m")
        relative_dir = Path(folder) / date_path
        relative_path = relative_dir / f"{digest}.jpg"
        disk_path = MediaService._upload_root() / relative_path
        disk_path.parent.mkdir(parents=True, exist_ok=True)
        if not disk_path.exists():
            disk_path.write_bytes(normalized_bytes)

        normalized_relative = MediaService._normalize_relative_path(str(relative_path))
        return {
            "relative_path": normalized_relative,
            "url": MediaService.to_public_url(normalized_relative),
            "size": len(normalized_bytes),
            "width": width,
            "height": height,
        }

    @staticmethod
    async def fetch_remote_image(url: str) -> tuple[bytes, str]:
        timeout = httpx.Timeout(MediaService.DEFAULT_HTTP_TIMEOUT_SECONDS)
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)
        except httpx.HTTPError:
            raise BadRequestException("image URL fetch failed")

        if response.status_code >= 400:
            raise BadRequestException("image URL is not accessible")

        content_type = (response.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
        if not content_type.startswith("image/"):
            raise BadRequestException("image URL must be an image")

        content = response.content
        if not content:
            raise BadRequestException("image URL returned empty content")
        return content, content_type

    @staticmethod
    async def save_image_from_url(
        url: str,
        *,
        folder: str,
        max_bytes: Optional[int] = None,
        max_edge: int = MAX_IMAGE_EDGE,
    ) -> dict:
        existing_relative = MediaService.extract_relative_path_from_url(url)
        if existing_relative:
            return {
                "relative_path": existing_relative,
                "url": MediaService.to_public_url(existing_relative),
                "size": None,
                "width": None,
                "height": None,
            }

        image_bytes, _ = await MediaService.fetch_remote_image(url)
        return MediaService.save_image_bytes(
            image_bytes,
            folder=folder,
            max_bytes=max_bytes,
            max_edge=max_edge,
        )
