from datetime import datetime, timedelta
from typing import List, Optional, Dict
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
    @staticmethod
    async def get_draft_link_by_draft_id(draft_article_id: int) -> Optional[ArticleDraftLink]:
        return await ArticleDraftLink.get_or_none(draft_article_id=draft_article_id)

    @staticmethod
    async def get_article_by_id(article_id: int) -> Optional[Article]:
        return await Article.get_or_none(id=article_id)

    @staticmethod
    async def _replace_article_tags(article_id: int, tag_ids: list[int]):
        await ArticleTag.filter(article_id=article_id).delete()
        for tag_id in tag_ids:
            tag = await Tag.get_or_none(id=tag_id)
            if tag:
                await ArticleTag.create(article_id=article_id, tag_id=tag_id)

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
                content=data.content if data.content is not None else source_article.content,
                rendered_content=source_article.rendered_content,
                status=Article.STATUS_DRAFT,
                category_id=data.category_id if data.category_id is not None else source_article.category_id,
                cover_image=data.cover_image if data.cover_image is not None else source_article.cover_image,
                view_count=0,
                is_featured=source_article.is_featured,
                allow_comment=data.allow_comment if data.allow_comment is not None else source_article.allow_comment,
                seo_title=data.seo_title if data.seo_title is not None else source_article.seo_title,
                seo_description=data.seo_description if data.seo_description is not None else source_article.seo_description,
                seo_keywords=data.seo_keywords if data.seo_keywords is not None else source_article.seo_keywords,
            )
            await ArticleDraftLink.create(source_article_id=source_article_id, draft_article_id=draft_article.id)
        else:
            update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
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
        
        article = await Article.create(**article_data)
        
        if data.tag_ids:
            for tag_id in data.tag_ids:
                tag = await Tag.get_or_none(id=tag_id)
                if tag:
                    await ArticleTag.create(article_id=article.id, tag_id=tag_id)
        
        return await Article.get(id=article.id).prefetch_related("category", "article_tags__tag")

    @staticmethod
    async def update_article(article_id: int, data: ArticleUpdate) -> Article:
        article = await Article.get_or_none(id=article_id)
        if not article:
            raise NotFoundException("Article not found")
        
        update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
        
        for key, value in update_data.items():
            setattr(article, key, value)
        
        await article.save()
        
        if data.tag_ids is not None:
            await ArticleTag.filter(article_id=article_id).delete()
            
            for tag_id in data.tag_ids:
                tag = await Tag.get_or_none(id=tag_id)
                if tag:
                    await ArticleTag.create(article_id=article_id, tag_id=tag_id)
        
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
        
        total = await query.count()
        
        query = query.order_by("-published_at", "-created_at")
        
        offset = (page - 1) * page_size
        items = await query.offset(offset).limit(page_size).prefetch_related("category", "article_tags__tag")
        
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return {
            "items": items,
            "total": total,
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
        
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
