import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
import re
import httpx
import io
from zoneinfo import ZoneInfo
from PIL import Image, ImageOps, UnidentifiedImageError
from tortoise.expressions import F
from tortoise.queryset import Q

from app.modules.articles.models import (
    Article,
    Category,
    Tag,
    ArticleTag,
    ArticleView,
    ArticleDraftLink,
)
from app.modules.articles.schemas import (
    CategoryCreate, CategoryUpdate,
    TagCreate, TagUpdate,
    ArticleCreate, ArticleUpdate,
    PaginatedArticles
)
from app.modules.system.service import SiteConfigService
from app.common.utils import generate_slug
from app.common.exceptions import NotFoundException, BadRequestException
from app.core.redis_client import get_redis_client
from app.modules.media.service import MediaService
import logging
import math

logger = logging.getLogger(__name__)


class ArticleCacheService:
    DETAIL_PREFIX = "article:detail:"
    LIST_PREFIX = "article:list:"

    @staticmethod
    async def _redis():
        from app.core.redis_client import get_redis_client
        return await get_redis_client()

    @staticmethod
    async def get_article_detail(slug: str) -> dict | None:
        r = await ArticleCacheService._redis()
        data = await r.get(f"{ArticleCacheService.DETAIL_PREFIX}{slug}")
        if data:
            import json
            return json.loads(data)
        return None

    @staticmethod
    async def set_article_detail(slug: str, data: dict) -> None:
        r = await ArticleCacheService._redis()
        import json
        await r.set(f"{ArticleCacheService.DETAIL_PREFIX}{slug}", json.dumps(data, default=str))

    @staticmethod
    async def get_article_list(key: str) -> dict | None:
        r = await ArticleCacheService._redis()
        data = await r.get(f"{ArticleCacheService.LIST_PREFIX}{key}")
        if data:
            import json
            return json.loads(data)
        return None

    @staticmethod
    async def set_article_list(key: str, data: dict) -> None:
        r = await ArticleCacheService._redis()
        import json
        await r.set(f"{ArticleCacheService.LIST_PREFIX}{key}", json.dumps(data, default=str))

    @staticmethod
    async def invalidate_article_detail(slug: str) -> None:
        r = await ArticleCacheService._redis()
        await r.delete(f"{ArticleCacheService.DETAIL_PREFIX}{slug}")

    @staticmethod
    async def invalidate_all_article_lists() -> None:
        r = await ArticleCacheService._redis()
        keys = await r.keys(f"{ArticleCacheService.LIST_PREFIX}*")
        if keys:
            await r.delete(*keys)


class CategoryService:
    @staticmethod
    async def create_category(data: CategoryCreate) -> Category:
        existing = await Category.get_or_none(slug=data.slug)
        if existing:
            raise BadRequestException(f"Category with slug '{data.slug}' already exists")
        
        category = await Category.create(**data.model_dump())
        return category

    @staticmethod
    async def update_category(category_id: int, data: CategoryUpdate) -> Category:
        category = await Category.get_or_none(id=category_id)
        if not category:
            raise NotFoundException("Category not found")
        
        update_data = data.model_dump(exclude_unset=True)
        
        if "slug" in update_data and update_data["slug"] != category.slug:
            existing = await Category.get_or_none(slug=update_data["slug"])
            if existing:
                raise BadRequestException(f"Category with slug '{update_data['slug']}' already exists")
        
        for key, value in update_data.items():
            setattr(category, key, value)
        
        await category.save()
        return category

    @staticmethod
    async def delete_category(category_id: int) -> None:
        category = await Category.get_or_none(id=category_id)
        if not category:
            raise NotFoundException("Category not found")
        
        article_count = await Article.filter(category_id=category_id).count()
        if article_count > 0:
            raise BadRequestException(f"Cannot delete category: {article_count} articles are using it")
        
        await category.delete()

    @staticmethod
    async def list_categories(is_active_only: bool = False) -> List[Category]:
        query = Category.all().order_by("sort_order", "name")
        if is_active_only:
            query = query.filter(is_active=True)
        return await query

    @staticmethod
    async def get_category_by_id(category_id: int) -> Optional[Category]:
        return await Category.get_or_none(id=category_id)


class TagService:
    @staticmethod
    async def create_tag(data: TagCreate) -> Tag:
        existing = await Tag.get_or_none(slug=data.slug)
        if existing:
            raise BadRequestException(f"Tag with slug '{data.slug}' already exists")
        
        tag = await Tag.create(**data.model_dump())
        return tag

    @staticmethod
    async def update_tag(tag_id: int, data: TagUpdate) -> Tag:
        tag = await Tag.get_or_none(id=tag_id)
        if not tag:
            raise NotFoundException("Tag not found")
        
        update_data = data.model_dump(exclude_unset=True)
        
        if "slug" in update_data and update_data["slug"] != tag.slug:
            existing = await Tag.get_or_none(slug=update_data["slug"])
            if existing:
                raise BadRequestException(f"Tag with slug '{update_data['slug']}' already exists")
        
        for key, value in update_data.items():
            setattr(tag, key, value)
        
        await tag.save()
        return tag

    @staticmethod
    async def delete_tag(tag_id: int) -> None:
        tag = await Tag.get_or_none(id=tag_id)
        if not tag:
            raise NotFoundException("Tag not found")
        
        article_count = await ArticleTag.filter(tag_id=tag_id).count()
        if article_count > 0:
            raise BadRequestException(f"Cannot delete tag: {article_count} articles are using it")
        
        await tag.delete()

    @staticmethod
    async def list_tags() -> List[Tag]:
        return await Tag.all().order_by("name")

    @staticmethod
    async def get_tag_by_id(tag_id: int) -> Optional[Tag]:
        return await Tag.get_or_none(id=tag_id)


class ArticleService:
    APP_TIMEZONE = ZoneInfo("Asia/Shanghai")
    DEFAULT_MAX_COVER_IMAGE_MB = 2
    MAX_ALLOWED_COVER_IMAGE_MB = 20
    HTTP_IMAGE_TIMEOUT_SECONDS = 15
    DEFAULT_ARTICLE_COVER_IMAGE_KEY = "DEFAULT_ARTICLE_COVER_IMAGE"
    DEFAULT_ARTICLE_COVER_IMAGE_THUMB_KEY = "DEFAULT_ARTICLE_COVER_IMAGE_THUMB"
    DEFAULT_ARTICLE_COVER_IMAGE_LARGE_KEY = "DEFAULT_ARTICLE_COVER_IMAGE_LARGE"
    _RESIZE_SCALE_FACTORS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5)
    _ENCODE_QUALITIES = (88, 80, 72, 64, 56, 48, 40)
    CONTENT_IMAGE_MAX_COUNT = 20

    @staticmethod
    def _to_naive_utc(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        # 统一按业务时区（Asia/Shanghai）入库为 naive，避免管理端与定时任务出现 8 小时偏移。
        return value.astimezone(ArticleService.APP_TIMEZONE).replace(tzinfo=None)

    @staticmethod
    def _utcnow_naive() -> datetime:
        # 统一使用业务时区（Asia/Shanghai）naive 时间，避免不同进程系统时区导致发布时间排序错乱。
        return datetime.now(ArticleService.APP_TIMEZONE).replace(tzinfo=None)

    @staticmethod
    def _to_app_tz_aware(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            # 兼容管理端 datetime-local 与历史无时区入参，按业务时区解释。
            return value.replace(tzinfo=ArticleService.APP_TIMEZONE)
        return value.astimezone(ArticleService.APP_TIMEZONE)

    @staticmethod
    def _now_app_tz_aware() -> datetime:
        return datetime.now(ArticleService.APP_TIMEZONE)

    @staticmethod
    def _normalize_scheduled_publish(update_data: dict, current_status: Optional[str] = None) -> None:
        if "scheduled_publish_at" not in update_data:
            return

        scheduled = ArticleService._to_app_tz_aware(update_data.get("scheduled_publish_at"))
        update_data["scheduled_publish_at"] = scheduled

        # 发布后不应保留定时计划，避免重复触发。
        if update_data.get("status") == Article.STATUS_PUBLISHED:
            update_data["scheduled_publish_at"] = None
            return

        status = update_data.get("status", current_status)
        # 只有草稿允许设置定时发布时间。
        if scheduled is not None and status != Article.STATUS_DRAFT:
            raise BadRequestException("scheduled_publish_at can only be set for draft articles")

        # 防止写入已过期的计划时间。
        if scheduled is not None and scheduled <= ArticleService._now_app_tz_aware():
            raise BadRequestException("scheduled_publish_at must be in the future")

    # 16:9 固定尺寸缩略图，用于列表卡片与详情大图。
    COVER_THUMB_SIZE = (320, 180)
    COVER_LARGE_SIZE = (1600, 900)
    COVER_THUMB_QUALITY = 70
    COVER_LARGE_QUALITY = 85
    _MARKDOWN_IMAGE_URL_RE = re.compile(
        r"!\[[^\]]*]\(\s*(?:<)?(?P<url>https?://[^\s>)]+)(?:>)?(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]+\)))?\s*\)",
        flags=re.IGNORECASE,
    )
    _IMAGE_URL_HINT_RE = (
        r"https?://[^\s)]+?(?:"
        r"\.(?:png|jpe?g|gif|webp|bmp|svg)(?:\?[^\s)]*)?"
        r"|[?&](?:format|fmt|fm|f)=(?:png|jpe?g|gif|webp|bmp|svg)\b[^\s)]*"
        r")"
    )
    _MARKDOWN_LINK_IMAGE_URL_RE = re.compile(
        rf"(?<!!)\[(?P<text>[^\]]+)\]\((?P<url>{_IMAGE_URL_HINT_RE})\)",
        flags=re.IGNORECASE,
    )
    _PLAIN_IMAGE_URL_LINE_RE = re.compile(
        rf"^(?P<indent>\s*)(?P<url>{_IMAGE_URL_HINT_RE})\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    )
    _HTML_IMAGE_URL_RE = re.compile(
        r'(<img\b[^>]*?\bsrc=["\'])(?P<url>https?://[^"\']+)(["\'][^>]*>)',
        flags=re.IGNORECASE,
    )
    @staticmethod
    async def _get_max_cover_image_bytes() -> int:
        value = await SiteConfigService.get_config("COVER_IMAGE_MAX_SIZE_MB")
        default_mb = ArticleService.DEFAULT_MAX_COVER_IMAGE_MB
        try:
            max_mb = int(value) if value is not None else default_mb
        except (TypeError, ValueError):
            max_mb = default_mb

        max_mb = max(1, min(ArticleService.MAX_ALLOWED_COVER_IMAGE_MB, max_mb))
        return max_mb * 1024 * 1024

    @staticmethod
    async def _normalize_http_image_url_to_media_url(url: str, max_cover_bytes: int, folder: str) -> str:
        saved = await MediaService.save_image_from_url(
            url,
            folder=folder,
            max_bytes=max_cover_bytes,
            max_edge=MediaService.MAX_IMAGE_EDGE,
        )
        return saved["url"]

    @staticmethod
    async def _normalize_content_images(content: Optional[str]) -> Optional[str]:
        if content is None:
            return None

        markdown_matches = list(ArticleService._MARKDOWN_IMAGE_URL_RE.finditer(content))
        html_matches = list(ArticleService._HTML_IMAGE_URL_RE.finditer(content))
        markdown_link_matches = list(ArticleService._MARKDOWN_LINK_IMAGE_URL_RE.finditer(content))
        plain_line_matches = list(ArticleService._PLAIN_IMAGE_URL_LINE_RE.finditer(content))
        if not markdown_matches and not html_matches and not markdown_link_matches and not plain_line_matches:
            if "data:image/" in content.lower():
                raise BadRequestException("content contains legacy base64 images, please migrate first")
            return content

        image_urls: list[str] = []
        image_urls.extend(match.group("url") for match in markdown_matches)
        image_urls.extend(match.group("url") for match in html_matches)
        image_urls.extend(match.group("url") for match in markdown_link_matches)
        image_urls.extend(match.group("url") for match in plain_line_matches)
        unique_urls = list(dict.fromkeys(image_urls))
        if len(unique_urls) > ArticleService.CONTENT_IMAGE_MAX_COUNT:
            raise BadRequestException(
                f"content image URL count cannot exceed {ArticleService.CONTENT_IMAGE_MAX_COUNT}"
            )

        max_cover_bytes = await ArticleService._get_max_cover_image_bytes()
        normalized_urls: dict[str, str] = {}
        for url in unique_urls:
            normalized_urls[url] = await ArticleService._normalize_http_image_url_to_media_url(
                url,
                max_cover_bytes,
                "articles/content",
            )

        normalized_content = ArticleService._MARKDOWN_IMAGE_URL_RE.sub(
            lambda match: match.group(0).replace(match.group("url"), normalized_urls.get(match.group("url"), match.group("url"))),
            content,
        )
        normalized_content = ArticleService._HTML_IMAGE_URL_RE.sub(
            lambda match: f'{match.group(1)}{normalized_urls.get(match.group("url"), match.group("url"))}{match.group(3)}',
            normalized_content,
        )
        normalized_content = ArticleService._MARKDOWN_LINK_IMAGE_URL_RE.sub(
            lambda match: f'![{match.group("text")}]({normalized_urls.get(match.group("url"), match.group("url"))})',
            normalized_content,
        )
        normalized_content = ArticleService._PLAIN_IMAGE_URL_LINE_RE.sub(
            lambda match: f'{match.group("indent")}![image]({normalized_urls.get(match.group("url"), match.group("url"))})',
            normalized_content,
        )
        if "data:image/" in normalized_content.lower():
            raise BadRequestException("content contains legacy base64 images, please migrate first")
        return normalized_content

    @staticmethod
    async def _normalize_cover_image(cover_image: Optional[str]) -> Optional[str]:
        if cover_image is None:
            return None

        value = cover_image.strip()
        if not value:
            return None
        max_cover_bytes = await ArticleService._get_max_cover_image_bytes()

        existing_relative = MediaService.extract_relative_path_from_url(value)
        if existing_relative:
            return MediaService.to_public_url(existing_relative)

        if value.startswith("data:image/"):
            raise BadRequestException("cover_image data URL is deprecated, please upload via media API")

        if re.match(r"^https?://", value, flags=re.IGNORECASE):
            try:
                return await ArticleService._normalize_http_image_url_to_media_url(
                    value,
                    max_cover_bytes,
                    "articles/covers/original",
                )
            except BadRequestException as exc:
                detail = exc.message
                if detail == "image URL fetch failed":
                    raise BadRequestException("cover_image URL fetch failed")
                if detail == "image URL is not accessible":
                    raise BadRequestException("cover_image URL is not accessible")
                if detail == "image URL must be an image":
                    raise BadRequestException("cover_image URL must be an image")
                if detail == "image URL returned empty content":
                    raise BadRequestException("cover_image URL returned empty content")
                raise

        raise BadRequestException("cover_image must be media URL or http(s) URL")

    @staticmethod
    def _make_fixed_aspect_variant(
        image_bytes: bytes,
        size: tuple[int, int],
        quality: int,
    ) -> bytes:
        """生成固定 16:9 尺寸的居中裁剪缩略图，返回 JPEG bytes。"""
        try:
            with Image.open(io.BytesIO(image_bytes)) as im:
                im = ImageOps.exif_transpose(im)
                rgb = im.convert("RGB")
                resampling = getattr(Image, "Resampling", Image).LANCZOS
                fitted = ImageOps.fit(rgb, size, method=resampling, centering=(0.5, 0.5))
                buf = io.BytesIO()
                fitted.save(buf, format="JPEG", optimize=True, quality=quality)
                return buf.getvalue()
        except UnidentifiedImageError:
            raise BadRequestException("cover_image is not a valid image")
        except OSError:
            raise BadRequestException("cover_image cannot be processed")

    @staticmethod
    async def _generate_cover_variants(
        normalized_cover: Optional[str],
    ) -> tuple[Optional[str], Optional[str]]:
        """根据已归一化封面 URL 生成 (thumb, large) 两份 16:9 缩略图 URL。

        若 normalized_cover 为空，返回 (None, None)。
        """
        if not normalized_cover:
            return None, None
        raw_bytes = MediaService.read_image_bytes(normalized_cover)
        thumb_bytes = ArticleService._make_fixed_aspect_variant(
            raw_bytes,
            ArticleService.COVER_THUMB_SIZE,
            ArticleService.COVER_THUMB_QUALITY,
        )
        large_bytes = ArticleService._make_fixed_aspect_variant(
            raw_bytes,
            ArticleService.COVER_LARGE_SIZE,
            ArticleService.COVER_LARGE_QUALITY,
        )
        thumb_saved = MediaService.save_image_bytes(
            thumb_bytes,
            folder="articles/covers/thumb",
            max_edge=ArticleService.COVER_THUMB_SIZE[0],
        )
        large_saved = MediaService.save_image_bytes(
            large_bytes,
            folder="articles/covers/large",
            max_edge=ArticleService.COVER_LARGE_SIZE[0],
        )
        return thumb_saved["url"], large_saved["url"]

    @staticmethod
    async def _build_cover_update_dict(cover_image_value: Optional[str]) -> dict:
        """对外统一入口：归一化封面并生成两份缩略图，返回三键字典用于赋值/更新。"""
        normalized = await ArticleService._normalize_cover_image(cover_image_value)
        thumb, large = await ArticleService._generate_cover_variants(normalized)
        return {
            "cover_image": normalized,
            "cover_image_thumb": thumb,
            "cover_image_large": large,
        }

    @staticmethod
    async def _get_default_cover_dict() -> dict[str, str]:
        cover_configs = await SiteConfigService.get_configs_map([
            ArticleService.DEFAULT_ARTICLE_COVER_IMAGE_KEY,
            ArticleService.DEFAULT_ARTICLE_COVER_IMAGE_THUMB_KEY,
            ArticleService.DEFAULT_ARTICLE_COVER_IMAGE_LARGE_KEY,
        ])
        default_cover = (cover_configs.get(ArticleService.DEFAULT_ARTICLE_COVER_IMAGE_KEY) or "").strip()
        default_thumb = (cover_configs.get(ArticleService.DEFAULT_ARTICLE_COVER_IMAGE_THUMB_KEY) or "").strip()
        default_large = (cover_configs.get(ArticleService.DEFAULT_ARTICLE_COVER_IMAGE_LARGE_KEY) or "").strip()
        return {
            "cover_image": default_cover,
            "cover_image_thumb": default_thumb,
            "cover_image_large": default_large,
        }

    @staticmethod
    def _resolve_cover_fields_with_fallback(
        cover_image: Optional[str],
        cover_image_thumb: Optional[str],
        cover_image_large: Optional[str],
        default_cover: dict[str, str],
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        normalized_cover = (cover_image or "").strip()
        normalized_thumb = (cover_image_thumb or "").strip()
        normalized_large = (cover_image_large or "").strip()

        if normalized_cover:
            resolved_cover = normalized_cover
            resolved_thumb = normalized_thumb or normalized_cover
            resolved_large = normalized_large or normalized_cover
            return resolved_cover, resolved_thumb, resolved_large

        fallback_cover = default_cover.get("cover_image", "")
        if not fallback_cover:
            return None, None, None

        fallback_thumb = default_cover.get("cover_image_thumb", "") or fallback_cover
        fallback_large = default_cover.get("cover_image_large", "") or fallback_cover
        return fallback_cover, fallback_thumb, fallback_large

    @staticmethod
    def _apply_cover_fields_to_article(article: Article, default_cover: dict[str, str]) -> None:
        cover_image, cover_image_thumb, cover_image_large = ArticleService._resolve_cover_fields_with_fallback(
            article.cover_image,
            article.cover_image_thumb,
            article.cover_image_large,
            default_cover,
        )
        article.cover_image = cover_image
        article.cover_image_thumb = cover_image_thumb
        article.cover_image_large = cover_image_large

    @staticmethod
    async def get_draft_link_by_draft_id(draft_article_id: int) -> Optional[ArticleDraftLink]:
        return await ArticleDraftLink.get_or_none(draft_article_id=draft_article_id)

    @staticmethod
    async def get_draft_links_by_draft_ids(draft_article_ids: list[int]) -> Dict[int, ArticleDraftLink]:
        ids = list({article_id for article_id in draft_article_ids if article_id is not None})
        if not ids:
            return {}
        links = await ArticleDraftLink.filter(draft_article_id__in=ids).all()
        return {link.draft_article_id: link for link in links}

    @staticmethod
    async def get_article_by_id(article_id: int) -> Optional[Article]:
        return await Article.get_or_none(id=article_id)

    @staticmethod
    async def _replace_article_tags(article_id: int, tag_ids: list[int]):
        await ArticleTag.filter(article_id=article_id).delete()
        if not tag_ids:
            return

        existing_tag_ids = await Tag.filter(id__in=tag_ids).values_list("id", flat=True)
        existing_tag_id_set = set(existing_tag_ids)
        valid_tag_ids = [tag_id for tag_id in tag_ids if tag_id in existing_tag_id_set]
        if not valid_tag_ids:
            return

        await ArticleTag.bulk_create([
            ArticleTag(article_id=article_id, tag_id=tag_id)
            for tag_id in valid_tag_ids
        ])

    @staticmethod
    async def create_or_update_draft_copy(source_article_id: int, data: ArticleUpdate) -> Article:
        source_article = await Article.get_or_none(id=source_article_id)
        if not source_article:
            raise NotFoundException("Source article not found")

        link = await ArticleDraftLink.get_or_none(source_article_id=source_article_id).prefetch_related("draft_article")
        draft_article = await link.draft_article if link else None
        if draft_article and draft_article.status == "deleted":
            await ArticleDraftLink.filter(id=link.id).delete()
            draft_article = None
            link = None

        tag_ids = (
            list(data.tag_ids)
            if data.tag_ids is not None
            else await ArticleTag.filter(article_id=source_article_id).values_list("tag_id", flat=True)
        )

        cover_image_provided = "cover_image" in data.model_fields_set
        cover_fields_for_create: dict
        if cover_image_provided:
            cover_fields_for_create = await ArticleService._build_cover_update_dict(data.cover_image)
        else:
            cover_fields_for_create = {
                "cover_image": source_article.cover_image,
                "cover_image_thumb": source_article.cover_image_thumb,
                "cover_image_large": source_article.cover_image_large,
            }
        normalized_content = (
            await ArticleService._normalize_content_images(data.content)
            if data.content is not None
            else None
        )

        if not draft_article:
            slug_base = f"{source_article.slug}-draft"
            unique_slug = slug_base
            counter = 1
            while await Article.filter(slug=unique_slug).exists():
                unique_slug = f"{slug_base}-{counter}"
                counter += 1

            draft_article = await Article.create(
                title=data.title if data.title is not None else source_article.title,
                slug=unique_slug,
                summary=data.summary if data.summary is not None else source_article.summary,
                content=normalized_content if normalized_content is not None else source_article.content,
                rendered_content=source_article.rendered_content,
                status=Article.STATUS_DRAFT,
                category_id=data.category_id if data.category_id is not None else source_article.category_id,
                view_count=0,
                is_featured=source_article.is_featured,
                allow_comment=data.allow_comment if data.allow_comment is not None else source_article.allow_comment,
                seo_title=data.seo_title if data.seo_title is not None else source_article.seo_title,
                seo_description=data.seo_description if data.seo_description is not None else source_article.seo_description,
                seo_keywords=data.seo_keywords if data.seo_keywords is not None else source_article.seo_keywords,
                scheduled_publish_at=ArticleService._to_app_tz_aware(data.scheduled_publish_at),
                **cover_fields_for_create,
            )
            await ArticleDraftLink.create(source_article_id=source_article_id, draft_article_id=draft_article.id)
        else:
            update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
            ArticleService._normalize_scheduled_publish(update_data, current_status=draft_article.status)
            if "cover_image" in update_data:
                cover_fields = await ArticleService._build_cover_update_dict(update_data["cover_image"])
                update_data.update(cover_fields)
            if "content" in update_data:
                update_data["content"] = await ArticleService._normalize_content_images(update_data["content"])
            for key, value in update_data.items():
                setattr(draft_article, key, value)
            draft_article.status = Article.STATUS_DRAFT
            await draft_article.save()

        await ArticleService._replace_article_tags(draft_article.id, list(tag_ids))
        return await Article.get(id=draft_article.id).prefetch_related("category", "article_tags__tag")

    @staticmethod
    async def publish_from_draft_copy(draft_article_id: int) -> Article:
        link = await ArticleDraftLink.get_or_none(draft_article_id=draft_article_id)
        if not link:
            raise NotFoundException("Draft link not found")

        draft_article = await Article.get_or_none(id=draft_article_id)
        source_article = await Article.get_or_none(id=link.source_article_id)
        if not draft_article or not source_article:
            raise NotFoundException("Draft or source article not found")

        source_article.title = draft_article.title
        source_article.summary = draft_article.summary
        source_article.content = draft_article.content
        source_article.rendered_content = draft_article.rendered_content
        source_article.category_id = draft_article.category_id
        source_article.cover_image = draft_article.cover_image
        source_article.cover_image_thumb = draft_article.cover_image_thumb
        source_article.cover_image_large = draft_article.cover_image_large
        source_article.allow_comment = draft_article.allow_comment
        source_article.seo_title = draft_article.seo_title
        source_article.seo_description = draft_article.seo_description
        source_article.seo_keywords = draft_article.seo_keywords
        source_article.status = Article.STATUS_PUBLISHED
        if not source_article.published_at:
            source_article.published_at = ArticleService._utcnow_naive()
        await source_article.save()

        draft_tag_ids = await ArticleTag.filter(article_id=draft_article.id).values_list("tag_id", flat=True)
        await ArticleService._replace_article_tags(source_article.id, list(draft_tag_ids))

        await ArticleTag.filter(article_id=draft_article.id).delete()
        await ArticleDraftLink.filter(id=link.id).delete()
        await draft_article.delete()

        published_article = await Article.get(id=source_article.id).prefetch_related("category", "article_tags__tag")
        asyncio.create_task(ArticleService._notify_n8n_blog_ingest(published_article, "update"))
        return published_article

    @staticmethod
    async def _notify_n8n_blog_ingest(article: Article, action: str) -> None:
        try:
            configs = await SiteConfigService.get_configs_map([
                "N8N_BLOG_INGEST_WEBHOOK_URL",
                "N8N_SECRET",
                "SITE_URL",
            ])
            webhook_url = (configs.get("N8N_BLOG_INGEST_WEBHOOK_URL") or "").strip()
            if not webhook_url:
                return

            webhook_secret = (configs.get("N8N_SECRET") or "").strip()
            site_url = (configs.get("SITE_URL") or "").strip().rstrip("/")

            article_url = f"{site_url}/posts/{article.slug}" if site_url else f"/posts/{article.slug}"

            published_date = ""
            if article.published_at:
                published_date = article.published_at.strftime("%Y-%m-%d")

            payload = {
                "action": action,
                "article_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"article-{article.id}")),
                "title": article.title,
                "url": article_url,
                "date": published_date,
                "content": article.content,
            }

            headers = {"Content-Type": "application/json"}
            if webhook_secret:
                headers["X-N8N-Secret"] = webhook_secret

            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(webhook_url, json=payload, headers=headers)
        except Exception:
            logger.exception("Failed to notify N8N blog ingest webhook for article %s (action=%s)", article.slug, action)

    @staticmethod
    async def create_article(data: ArticleCreate, admin_id: int) -> Article:
        slug = generate_slug(data.title)
        
        counter = 1
        unique_slug = slug
        while await Article.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}-{counter}"
            counter += 1
        
        article_data = data.model_dump(exclude={"tag_ids"})
        ArticleService._normalize_scheduled_publish(article_data, current_status=article_data.get("status"))
        if article_data.get("status") == Article.STATUS_PUBLISHED and not article_data.get("published_at"):
            article_data["published_at"] = ArticleService._utcnow_naive()
        article_data["slug"] = unique_slug
        cover_fields = await ArticleService._build_cover_update_dict(article_data.get("cover_image"))
        article_data.update(cover_fields)
        article_data["content"] = await ArticleService._normalize_content_images(article_data.get("content"))

        article = await Article.create(**article_data)
        
        if data.tag_ids:
            await ArticleService._replace_article_tags(article.id, list(data.tag_ids))
        
        if article.status == Article.STATUS_PUBLISHED:
            asyncio.create_task(ArticleService._notify_n8n_blog_ingest(article, "create"))

        return await Article.get(id=article.id).prefetch_related("category", "article_tags__tag")

    @staticmethod
    async def update_article(article_id: int, data: ArticleUpdate) -> Article:
        article = await Article.get_or_none(id=article_id)
        if not article:
            raise NotFoundException("Article not found")
        
        original_status = article.status
        
        update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
        ArticleService._normalize_scheduled_publish(update_data, current_status=article.status)
        # 封面未变更时跳过重算缩略图，避免编辑页“更新发布”重复耗时。
        if "cover_image" in update_data and update_data["cover_image"] == article.cover_image:
            update_data.pop("cover_image")
        if "cover_image" in update_data:
            cover_fields = await ArticleService._build_cover_update_dict(update_data["cover_image"])
            update_data.update(cover_fields)

        # 内容未变更时跳过正文图片归一化（该步骤可能触发远程拉图，最耗时）。
        if "content" in update_data and update_data["content"] == article.content:
            update_data.pop("content")
        if "content" in update_data:
            update_data["content"] = await ArticleService._normalize_content_images(update_data["content"])
        if update_data.get("status") == Article.STATUS_PUBLISHED and not article.published_at:
            update_data["published_at"] = ArticleService._utcnow_naive()

        if "title" in update_data and update_data["title"] != article.title:
            new_slug = generate_slug(update_data["title"])
            counter = 1
            unique_slug = new_slug
            while await Article.filter(slug=unique_slug).exclude(id=article_id).exists():
                unique_slug = f"{new_slug}-{counter}"
                counter += 1
            update_data["slug"] = unique_slug

        for key, value in update_data.items():
            setattr(article, key, value)

        if update_data:
            await article.save()

        if data.tag_ids is not None:
            next_tag_ids = list(data.tag_ids)
            current_tag_ids = await ArticleTag.filter(article_id=article_id).values_list("tag_id", flat=True)
            if set(next_tag_ids) != set(current_tag_ids):
                await ArticleService._replace_article_tags(article_id, next_tag_ids)
        
        updated_article = await Article.get(id=article_id).prefetch_related("category", "article_tags__tag")
        if updated_article.status == Article.STATUS_PUBLISHED:
            was_published_before = original_status == Article.STATUS_PUBLISHED
            action = "update" if was_published_before else "create"
            asyncio.create_task(ArticleService._notify_n8n_blog_ingest(updated_article, action))
        return updated_article

    @staticmethod
    async def publish_article(article_id: int) -> Article:
        article = await Article.get_or_none(id=article_id)
        if not article:
            raise NotFoundException("Article not found")
        
        article.status = Article.STATUS_PUBLISHED
        article.scheduled_publish_at = None
        if not article.published_at:
            article.published_at = ArticleService._utcnow_naive()
        await article.save()
        
        asyncio.create_task(ArticleService._notify_n8n_blog_ingest(article, "create"))

        return article

    @staticmethod
    async def unpublish_article(article_id: int) -> Article:
        article = await Article.get_or_none(id=article_id)
        if not article:
            raise NotFoundException("Article not found")
        
        article.status = Article.STATUS_UNPUBLISHED
        article.scheduled_publish_at = None
        await article.save()
        
        return article

    @staticmethod
    async def delete_article(article_id: int, hard_delete: bool = False) -> None:
        article = await Article.get_or_none(id=article_id)
        if not article:
            raise NotFoundException("Article not found")

        # 如果删除的是草稿副本，直接删除草稿及链接。
        draft_link = await ArticleDraftLink.get_or_none(draft_article_id=article_id)
        if draft_link:
            await ArticleTag.filter(article_id=article_id).delete()
            await ArticleView.filter(article_id=article_id).delete()
            await ArticleDraftLink.filter(id=draft_link.id).delete()
            await article.delete()
            return

        if not hard_delete:
            article.status = "deleted"
            await article.save()
            return

        # 删除源文章时，同步清理其草稿副本与链接，避免孤儿数据。
        source_links = await ArticleDraftLink.filter(source_article_id=article_id).all()
        for link in source_links:
            draft_article = await Article.get_or_none(id=link.draft_article_id)
            if draft_article:
                await ArticleTag.filter(article_id=draft_article.id).delete()
                await ArticleView.filter(article_id=draft_article.id).delete()
                await draft_article.delete()
        await ArticleDraftLink.filter(source_article_id=article_id).delete()

        await ArticleTag.filter(article_id=article_id).delete()
        await ArticleView.filter(article_id=article_id).delete()
        asyncio.create_task(ArticleService._notify_n8n_blog_ingest(article, "delete"))
        await article.delete()

    @staticmethod
    async def list_articles(
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[str] = None,
        category_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        keyword: Optional[str] = None,
        is_featured: Optional[bool] = None,
        is_admin: bool = False
    ) -> Dict:
        query = Article.all()
        
        if not is_admin:
            try:
                await ArticleService.backfill_missing_published_at()
            except Exception:
                # 列表查询优先保证可用性，回填失败不阻断主接口。
                pass
            query = query.filter(status=Article.STATUS_PUBLISHED)
        elif status_filter:
            query = query.filter(status=status_filter)
        
        if category_id:
            query = query.filter(category_id=category_id)
        
        if tag_id:
            article_ids = await ArticleTag.filter(tag_id=tag_id).values_list("article_id", flat=True)
            query = query.filter(id__in=article_ids)
        
        if keyword:
            query = query.filter(
                Q(title__icontains=keyword) | 
                Q(content__icontains=keyword) | 
                Q(summary__icontains=keyword)
            )

        if is_featured is not None:
            query = query.filter(is_featured=is_featured)
        
        ordered_query = query.order_by("-published_at", "-created_at")
        offset = (page - 1) * page_size

        total, items = await asyncio.gather(
            query.count(),
            ordered_query.offset(offset).limit(page_size).prefetch_related("category", "article_tags__tag"),
        )
        total_views = 0
        if not is_admin and items:
            default_cover = await ArticleService._get_default_cover_dict()
            for item in items:
                ArticleService._apply_cover_fields_to_article(item, default_cover)
        
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return {
            "items": items,
            "total": total,
            "total_views": total_views,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

    @staticmethod
    async def backfill_missing_published_at() -> int:
        """为历史已发布但 published_at 为空的数据补齐发布时间（回填 created_at）。"""
        return await Article.filter(
            status=Article.STATUS_PUBLISHED,
            published_at__isnull=True,
        ).update(published_at=F("created_at"))

    @staticmethod
    async def get_article_by_slug(slug: str, is_admin: bool = False) -> Optional[Article]:
        query = Article.filter(slug=slug)
        
        if not is_admin:
            query = query.filter(status=Article.STATUS_PUBLISHED)
        
        article = await query.prefetch_related("category", "article_tags__tag").first()
        if article and not is_admin:
            default_cover = await ArticleService._get_default_cover_dict()
            ArticleService._apply_cover_fields_to_article(article, default_cover)
        return article

    @staticmethod
    async def increment_view_count(article_id: int, ip_address: str, user_agent: Optional[str] = None) -> bool:
        await Article.filter(id=article_id).update(view_count=F("view_count") + 1)
        
        await ArticleView.create(
            article_id=article_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return True

    @staticmethod
    async def search_articles(
        keyword: str,
        page: int = 1,
        page_size: int = 10,
        search_in: str = "title_summary",
        time_filter: str = "all",
    ) -> Dict:
        try:
            await ArticleService.backfill_missing_published_at()
        except Exception:
            # 测试环境或 Redis/配置异常时，回填失败不影响搜索主流程。
            pass
        query = Article.filter(status=Article.STATUS_PUBLISHED)

        keyword_query: Optional[Q] = None
        if search_in in {"title", "title_summary"}:
            keyword_query = Q(title__icontains=keyword) if keyword_query is None else keyword_query | Q(title__icontains=keyword)
        if search_in in {"summary", "title_summary"}:
            keyword_query = Q(summary__icontains=keyword) if keyword_query is None else keyword_query | Q(summary__icontains=keyword)

        # 兼容未知值，默认按标题+摘要搜索。
        if keyword_query is None:
            keyword_query = Q(title__icontains=keyword) | Q(summary__icontains=keyword)

        query = query.filter(keyword_query)

        now = ArticleService._utcnow_naive()
        if time_filter in {"7d", "30d", "90d", "365d"}:
            days = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}[time_filter]
            cutoff = now - timedelta(days=days)
            # 兼容历史数据：published_at 为空时回退 created_at 判断。
            query = query.filter(
                Q(published_at__gte=cutoff) |
                (Q(published_at__isnull=True) & Q(created_at__gte=cutoff))
            )
        
        total = await query.count()
        
        query = query.order_by("-published_at", "-created_at")
        
        offset = (page - 1) * page_size
        items = await query.offset(offset).limit(page_size).prefetch_related("category", "article_tags__tag")
        if items:
            default_cover = await ArticleService._get_default_cover_dict()
            for item in items:
                ArticleService._apply_cover_fields_to_article(item, default_cover)
        
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

    @staticmethod
    async def publish_due_scheduled_articles(now: Optional[datetime] = None) -> int:
        current_time = ArticleService._to_app_tz_aware(now) if now is not None else ArticleService._now_app_tz_aware()
        scheduled_articles = await Article.filter(
            status=Article.STATUS_DRAFT,
            scheduled_publish_at__isnull=False,
        ).all()

        if not scheduled_articles:
            return 0

        due_articles: list[Article] = []
        for item in scheduled_articles:
            normalized_scheduled = ArticleService._to_app_tz_aware(item.scheduled_publish_at)
            if normalized_scheduled is None:
                continue
            if normalized_scheduled <= current_time:
                due_articles.append(item)

        # 使用各自的计划发布时间作为 published_at，避免批量任务同一时刻触发时
        # 所有文章发布时间完全相同，导致前台排序与展示时间不符合预期。
        for item in due_articles:
            item.status = Article.STATUS_PUBLISHED
            item.published_at = ArticleService._to_app_tz_aware(item.scheduled_publish_at) or current_time
            item.scheduled_publish_at = None

        pending_saves = [item.save(update_fields=["status", "published_at", "scheduled_publish_at"]) for item in due_articles]
        if pending_saves:
            await asyncio.gather(*pending_saves)

        notification_tasks = [ArticleService._notify_n8n_blog_ingest(item, "create") for item in due_articles]
        if notification_tasks:
            await asyncio.gather(*notification_tasks, return_exceptions=True)

        return len(due_articles)
