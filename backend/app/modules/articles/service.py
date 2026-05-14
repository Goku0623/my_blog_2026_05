import base64
import binascii
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import re
import httpx
import io
from PIL import Image, ImageOps, UnidentifiedImageError
from tortoise.expressions import F
from tortoise.functions import Sum
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
import math


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
    DEFAULT_MAX_COVER_IMAGE_MB = 2
    MAX_ALLOWED_COVER_IMAGE_MB = 20
    HTTP_IMAGE_TIMEOUT_SECONDS = 15
    DEFAULT_ARTICLE_COVER_IMAGE_KEY = "DEFAULT_ARTICLE_COVER_IMAGE"
    DEFAULT_ARTICLE_COVER_IMAGE_THUMB_KEY = "DEFAULT_ARTICLE_COVER_IMAGE_THUMB"
    DEFAULT_ARTICLE_COVER_IMAGE_LARGE_KEY = "DEFAULT_ARTICLE_COVER_IMAGE_LARGE"
    _RESIZE_SCALE_FACTORS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5)
    _ENCODE_QUALITIES = (88, 80, 72, 64, 56, 48, 40)
    CONTENT_IMAGE_MAX_COUNT = 20

    # 16:9 固定尺寸缩略图，用于列表卡片与详情大图。
    COVER_THUMB_SIZE = (400, 225)
    COVER_LARGE_SIZE = (1600, 900)
    COVER_THUMB_QUALITY = 80
    COVER_LARGE_QUALITY = 85
    _MARKDOWN_IMAGE_URL_RE = re.compile(
        r"!\[[^\]]*]\((?P<url>https?://[^)\s]+)\)",
        flags=re.IGNORECASE,
    )
    _HTML_IMAGE_URL_RE = re.compile(
        r'(<img\b[^>]*?\bsrc=["\'])(?P<url>https?://[^"\']+)(["\'][^>]*>)',
        flags=re.IGNORECASE,
    )

    @staticmethod
    def _limit_message(max_cover_bytes: int) -> str:
        max_mb = round(max_cover_bytes / (1024 * 1024), 2)
        return f"cover_image size cannot exceed {max_mb}MB"

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
    def _compress_image_bytes(image_bytes: bytes, max_cover_bytes: int) -> tuple[bytes, str]:
        try:
            with Image.open(io.BytesIO(image_bytes)) as original:
                # 统一转为 JPEG 以获得更稳定的压缩率。
                rgb_image = original.convert("RGB")
                width, height = rgb_image.size
                resampling = getattr(Image, "Resampling", Image).LANCZOS

                for scale in ArticleService._RESIZE_SCALE_FACTORS:
                    resized = rgb_image
                    if scale != 1.0:
                        resized = rgb_image.resize(
                            (max(1, int(width * scale)), max(1, int(height * scale))),
                            resampling,
                        )

                    for quality in ArticleService._ENCODE_QUALITIES:
                        output = io.BytesIO()
                        resized.save(output, format="JPEG", optimize=True, quality=quality)
                        data = output.getvalue()
                        if len(data) <= max_cover_bytes:
                            return data, "image/jpeg"
        except UnidentifiedImageError:
            raise BadRequestException("cover_image is not a valid image")
        except OSError:
            raise BadRequestException("cover_image cannot be processed")

        raise BadRequestException(
            f"cover_image is too large and cannot be compressed below limit ({ArticleService._limit_message(max_cover_bytes)})"
        )

    @staticmethod
    def _to_data_url(image_bytes: bytes, content_type: str) -> str:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{content_type};base64,{encoded}"

    @staticmethod
    async def _fetch_image_from_url(url: str) -> tuple[bytes, str]:
        timeout = httpx.Timeout(ArticleService.HTTP_IMAGE_TIMEOUT_SECONDS)
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

        image_bytes = response.content
        if not image_bytes:
            raise BadRequestException("image URL returned empty content")

        return image_bytes, content_type

    @staticmethod
    async def _normalize_http_image_url_to_data_url(url: str, max_cover_bytes: int) -> str:
        image_bytes, content_type = await ArticleService._fetch_image_from_url(url)
        if len(image_bytes) > max_cover_bytes:
            image_bytes, content_type = ArticleService._compress_image_bytes(image_bytes, max_cover_bytes)
        return ArticleService._to_data_url(image_bytes, content_type)

    @staticmethod
    async def _normalize_content_images(content: Optional[str]) -> Optional[str]:
        if content is None:
            return None

        markdown_matches = list(ArticleService._MARKDOWN_IMAGE_URL_RE.finditer(content))
        html_matches = list(ArticleService._HTML_IMAGE_URL_RE.finditer(content))
        if not markdown_matches and not html_matches:
            return content

        image_urls: list[str] = []
        image_urls.extend(match.group("url") for match in markdown_matches)
        image_urls.extend(match.group("url") for match in html_matches)
        unique_urls = list(dict.fromkeys(image_urls))
        if len(unique_urls) > ArticleService.CONTENT_IMAGE_MAX_COUNT:
            raise BadRequestException(
                f"content image URL count cannot exceed {ArticleService.CONTENT_IMAGE_MAX_COUNT}"
            )

        max_cover_bytes = await ArticleService._get_max_cover_image_bytes()
        normalized_urls: dict[str, str] = {}
        for url in unique_urls:
            normalized_urls[url] = await ArticleService._normalize_http_image_url_to_data_url(url, max_cover_bytes)

        normalized_content = ArticleService._MARKDOWN_IMAGE_URL_RE.sub(
            lambda match: match.group(0).replace(match.group("url"), normalized_urls.get(match.group("url"), match.group("url"))),
            content,
        )
        normalized_content = ArticleService._HTML_IMAGE_URL_RE.sub(
            lambda match: f'{match.group(1)}{normalized_urls.get(match.group("url"), match.group("url"))}{match.group(3)}',
            normalized_content,
        )
        return normalized_content

    @staticmethod
    async def _normalize_cover_image(cover_image: Optional[str]) -> Optional[str]:
        if cover_image is None:
            return None

        value = cover_image.strip()
        if not value:
            return None
        max_cover_bytes = await ArticleService._get_max_cover_image_bytes()

        if value.startswith("data:image/"):
            if ";base64," not in value:
                raise BadRequestException("cover_image base64 format is invalid")

            base64_body = value.split(";base64,", 1)[1]
            try:
                decoded = base64.b64decode(base64_body, validate=True)
            except (binascii.Error, ValueError):
                raise BadRequestException("cover_image base64 content is invalid")

            if len(decoded) > max_cover_bytes:
                compressed_bytes, compressed_type = ArticleService._compress_image_bytes(decoded, max_cover_bytes)
                return ArticleService._to_data_url(compressed_bytes, compressed_type)

            return value

        if re.match(r"^https?://", value, flags=re.IGNORECASE):
            try:
                return await ArticleService._normalize_http_image_url_to_data_url(value, max_cover_bytes)
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

        raise BadRequestException("cover_image must be data:image base64 or http(s) URL")

    @staticmethod
    def _decode_data_url(data_url: str) -> bytes:
        """Decode a `data:image/...;base64,...` URL into raw bytes."""
        if ";base64," not in data_url:
            raise BadRequestException("cover_image base64 format is invalid")
        base64_body = data_url.split(";base64,", 1)[1]
        try:
            return base64.b64decode(base64_body, validate=True)
        except (binascii.Error, ValueError):
            raise BadRequestException("cover_image base64 content is invalid")

    @staticmethod
    def _make_fixed_aspect_variant(
        image_bytes: bytes,
        size: tuple[int, int],
        quality: int,
    ) -> str:
        """生成固定 16:9 尺寸的居中裁剪缩略图，返回 data URL。

        - 使用 ImageOps.fit 保证输出严格匹配 size，无变形（多余部分居中裁掉）。
        - 输出 JPEG，前端 <img> 用 object-cover 填充固定容器，视觉永远一致。
        """
        try:
            with Image.open(io.BytesIO(image_bytes)) as im:
                im = ImageOps.exif_transpose(im)
                rgb = im.convert("RGB")
                resampling = getattr(Image, "Resampling", Image).LANCZOS
                fitted = ImageOps.fit(rgb, size, method=resampling, centering=(0.5, 0.5))
                buf = io.BytesIO()
                fitted.save(buf, format="JPEG", optimize=True, quality=quality)
                return ArticleService._to_data_url(buf.getvalue(), "image/jpeg")
        except UnidentifiedImageError:
            raise BadRequestException("cover_image is not a valid image")
        except OSError:
            raise BadRequestException("cover_image cannot be processed")

    @staticmethod
    async def _generate_cover_variants(
        normalized_cover: Optional[str],
    ) -> tuple[Optional[str], Optional[str]]:
        """根据已归一化的封面 data URL 生成 (thumb, large) 两份 16:9 缩略图。

        若 normalized_cover 为空，返回 (None, None)。
        """
        if not normalized_cover:
            return None, None
        if not normalized_cover.startswith("data:image/"):
            return None, None

        raw_bytes = ArticleService._decode_data_url(normalized_cover)
        thumb = ArticleService._make_fixed_aspect_variant(
            raw_bytes,
            ArticleService.COVER_THUMB_SIZE,
            ArticleService.COVER_THUMB_QUALITY,
        )
        large = ArticleService._make_fixed_aspect_variant(
            raw_bytes,
            ArticleService.COVER_LARGE_SIZE,
            ArticleService.COVER_LARGE_QUALITY,
        )
        return thumb, large

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
                **cover_fields_for_create,
            )
            await ArticleDraftLink.create(source_article_id=source_article_id, draft_article_id=draft_article.id)
        else:
            update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
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
            source_article.published_at = datetime.now()
        await source_article.save()

        draft_tag_ids = await ArticleTag.filter(article_id=draft_article.id).values_list("tag_id", flat=True)
        await ArticleService._replace_article_tags(source_article.id, list(draft_tag_ids))

        await ArticleTag.filter(article_id=draft_article.id).delete()
        await ArticleDraftLink.filter(id=link.id).delete()
        await draft_article.delete()

        return await Article.get(id=source_article.id).prefetch_related("category", "article_tags__tag")

    @staticmethod
    async def create_article(data: ArticleCreate, admin_id: int) -> Article:
        slug = generate_slug(data.title)
        
        counter = 1
        unique_slug = slug
        while await Article.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}-{counter}"
            counter += 1
        
        article_data = data.model_dump(exclude={"tag_ids"})
        article_data["slug"] = unique_slug
        cover_fields = await ArticleService._build_cover_update_dict(article_data.get("cover_image"))
        article_data.update(cover_fields)
        article_data["content"] = await ArticleService._normalize_content_images(article_data.get("content"))

        article = await Article.create(**article_data)
        
        if data.tag_ids:
            await ArticleService._replace_article_tags(article.id, list(data.tag_ids))
        
        return await Article.get(id=article.id).prefetch_related("category", "article_tags__tag")

    @staticmethod
    async def update_article(article_id: int, data: ArticleUpdate) -> Article:
        article = await Article.get_or_none(id=article_id)
        if not article:
            raise NotFoundException("Article not found")
        
        update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
        if "cover_image" in update_data:
            cover_fields = await ArticleService._build_cover_update_dict(update_data["cover_image"])
            update_data.update(cover_fields)
        if "content" in update_data:
            update_data["content"] = await ArticleService._normalize_content_images(update_data["content"])

        for key, value in update_data.items():
            setattr(article, key, value)
        
        await article.save()
        
        if data.tag_ids is not None:
            await ArticleService._replace_article_tags(article_id, list(data.tag_ids))
        
        return await Article.get(id=article_id).prefetch_related("category", "article_tags__tag")

    @staticmethod
    async def publish_article(article_id: int) -> Article:
        article = await Article.get_or_none(id=article_id)
        if not article:
            raise NotFoundException("Article not found")
        
        article.status = Article.STATUS_PUBLISHED
        if not article.published_at:
            article.published_at = datetime.now()
        await article.save()
        
        return article

    @staticmethod
    async def unpublish_article(article_id: int) -> Article:
        article = await Article.get_or_none(id=article_id)
        if not article:
            raise NotFoundException("Article not found")
        
        article.status = Article.STATUS_UNPUBLISHED
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

        total, total_views_result, items = await asyncio.gather(
            query.count(),
            query.annotate(total_views=Sum("view_count")).values("total_views"),
            ordered_query.offset(offset).limit(page_size).prefetch_related("category", "article_tags__tag"),
        )
        total_views = total_views_result[0]["total_views"] if total_views_result and total_views_result[0]["total_views"] else 0
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

        now = datetime.now()
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
