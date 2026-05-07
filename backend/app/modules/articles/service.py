from datetime import datetime
from typing import List, Optional, Dict
from tortoise.expressions import F
from tortoise.queryset import Q

from app.modules.articles.models import Article, Category, Tag, ArticleTag, ArticleView
from app.modules.articles.schemas import (
    CategoryCreate, CategoryUpdate,
    TagCreate, TagUpdate,
    ArticleCreate, ArticleUpdate,
    PaginatedArticles
)
from app.common.utils import generate_slug
from app.common.exceptions import NotFoundException, BadRequestException
from app.core.redis_client import get_redis_client
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
        
        if hard_delete:
            await ArticleTag.filter(article_id=article_id).delete()
            await ArticleView.filter(article_id=article_id).delete()
            await article.delete()
        else:
            article.status = "deleted"
            await article.save()

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
        redis = await get_redis_client()
        cache_key = f"view:{article_id}:{ip_address}"
        
        if await redis.get(cache_key):
            return False
        
        await redis.setex(cache_key, 86400, "1")
        
        await Article.filter(id=article_id).update(view_count=F("view_count") + 1)
        
        await ArticleView.create(
            article_id=article_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return True

    @staticmethod
    async def search_articles(keyword: str, page: int = 1, page_size: int = 10) -> Dict:
        query = Article.filter(status=Article.STATUS_PUBLISHED)
        
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
