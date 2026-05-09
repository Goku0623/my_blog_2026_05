from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status

from app.modules.articles.schemas import (
    CategoryCreate, CategoryUpdate, CategoryOut,
    TagCreate, TagUpdate, TagOut,
    ArticleCreate, ArticleUpdate, ArticleOut, ArticleListItem,
    PaginatedArticles
)
from app.modules.articles.service import CategoryService, TagService, ArticleService
from app.core.dependencies import get_current_admin, get_client_ip
from app.modules.auth.models import AdminUser
from app.common.response import success
from app.common.exceptions import NotFoundException, BadRequestException
from app.modules.system.service import OperationLogService


router = APIRouter(tags=["Articles"])


async def _log_article_operation(
    action: str,
    current_admin: AdminUser,
    request: Request,
    article_id: Optional[int] = None,
    detail: Optional[str] = None,
):
    await OperationLogService.log_operation(
        operator=current_admin.username,
        action=action,
        target_type="article",
        target_id=article_id,
        detail=detail,
        ip=get_client_ip(request),
        result="success",
    )


async def _serialize_article_list_item(article) -> dict:
    category = await article.category if article.category_id else None
    tags = []
    article_tags = await article.article_tags.all().prefetch_related("tag")
    for article_tag in article_tags:
        if article_tag.tag:
            tags.append(TagOut.model_validate(article_tag.tag).model_dump())

    draft_link = await ArticleService.get_draft_link_by_draft_id(article.id)
    return {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "summary": article.summary,
        "status": article.status,
        "category": CategoryOut.model_validate(category).model_dump() if category else None,
        "tags": tags,
        "cover_image": article.cover_image,
        "view_count": article.view_count,
        "is_featured": article.is_featured,
        "published_at": article.published_at,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
        "is_draft_copy": bool(draft_link),
        "source_article_id": draft_link.source_article_id if draft_link else None,
    }


@router.get("/articles", response_model=dict)
async def list_articles_public(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    keyword: Optional[str] = None
):
    try:
        result = await ArticleService.list_articles(
            page=page,
            page_size=page_size,
            category_id=category_id,
            tag_id=tag_id,
            keyword=keyword,
            is_admin=False
        )

        serialized_items = []
        for article in result["items"]:
            serialized_items.append(await _serialize_article_list_item(article))

        result["items"] = serialized_items
        return success(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching articles"
        )


@router.get("/articles/search", response_model=dict)
async def search_articles(
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search_in: str = Query("title_summary", pattern="^(title|summary|title_summary)$"),
    time_filter: str = Query("all", pattern="^(all|7d|30d|90d|365d)$"),
):
    try:
        result = await ArticleService.search_articles(
            keyword=keyword,
            page=page,
            page_size=page_size,
            search_in=search_in,
            time_filter=time_filter,
        )
        serialized_items = []
        for article in result["items"]:
            serialized_items.append(await _serialize_article_list_item(article))

        result["items"] = serialized_items
        return success(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while searching articles"
        )


@router.get("/articles/{slug}", response_model=dict)
async def get_article_by_slug(slug: str, request: Request):
    try:
        article = await ArticleService.get_article_by_slug(slug, is_admin=False)
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        
        incremented = await ArticleService.increment_view_count(article.id, ip_address, user_agent)
        if incremented:
            article.view_count += 1
        
        category = await article.category if article.category_id else None
        tags = []
        article_tags = await article.article_tags.all().prefetch_related("tag")
        for at in article_tags:
            if at.tag:
                tags.append(at.tag)
        
        article_dict = {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "summary": article.summary,
            "content": article.content,
            "rendered_content": article.rendered_content,
            "status": article.status,
            "category": CategoryOut.model_validate(category) if category else None,
            "tags": [TagOut.model_validate(tag) for tag in tags],
            "cover_image": article.cover_image,
            "view_count": article.view_count,
            "is_featured": article.is_featured,
            "allow_comment": article.allow_comment,
            "seo_title": article.seo_title,
            "seo_description": article.seo_description,
            "seo_keywords": article.seo_keywords,
            "published_at": article.published_at,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
        }
        draft_link = await ArticleService.get_draft_link_by_draft_id(article.id)
        article_dict["is_draft_copy"] = bool(draft_link)
        article_dict["source_article_id"] = draft_link.source_article_id if draft_link else None
        
        return success(article_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the article"
        )


@router.get("/categories", response_model=dict)
async def list_categories_public():
    try:
        categories = await CategoryService.list_categories(is_active_only=True)
        return success([CategoryOut.model_validate(cat) for cat in categories])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching categories"
        )


@router.get("/tags", response_model=dict)
async def list_tags_public():
    try:
        tags = await TagService.list_tags()
        return success([TagOut.model_validate(tag) for tag in tags])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching tags"
        )


admin_router = APIRouter(prefix="/admin", tags=["Articles Admin"])


@admin_router.get("/articles", response_model=dict)
async def list_articles_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = None,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    keyword: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        result = await ArticleService.list_articles(
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            category_id=category_id,
            tag_id=tag_id,
            keyword=keyword,
            is_admin=True
        )

        serialized_items = []
        for article in result["items"]:
            serialized_items.append(await _serialize_article_list_item(article))

        result["items"] = serialized_items
        return success(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching articles"
        )


@admin_router.post("/articles", response_model=dict)
async def create_article(
    article_data: ArticleCreate,
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        article = await ArticleService.create_article(article_data, current_admin.id)
        
        category = await article.category if article.category_id else None
        tags = []
        article_tags = await article.article_tags.all().prefetch_related("tag")
        for at in article_tags:
            if at.tag:
                tags.append(at.tag)
        
        article_dict = {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "summary": article.summary,
            "content": article.content,
            "rendered_content": article.rendered_content,
            "status": article.status,
            "category": CategoryOut.model_validate(category) if category else None,
            "tags": [TagOut.model_validate(tag) for tag in tags],
            "cover_image": article.cover_image,
            "view_count": article.view_count,
            "is_featured": article.is_featured,
            "allow_comment": article.allow_comment,
            "seo_title": article.seo_title,
            "seo_description": article.seo_description,
            "seo_keywords": article.seo_keywords,
            "published_at": article.published_at,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
        }
        
        await _log_article_operation(
            action="article_create",
            current_admin=current_admin,
            request=request,
            article_id=article.id,
            detail=f"创建文章：{article.title}",
        )
        return success(article_dict, "Article created successfully")
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the article"
        )


@admin_router.get("/articles/{article_id}", response_model=dict)
async def get_article_admin(
    article_id: int,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        article = await ArticleService.get_article_by_slug(str(article_id), is_admin=True)
        if not article:
            article_obj = await ArticleService.list_articles(is_admin=True)
            for item in article_obj["items"]:
                if item.id == article_id:
                    article = item
                    break
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        category = await article.category if hasattr(article, "category_id") and article.category_id else None
        tags = []
        if hasattr(article, "article_tags"):
            article_tags = await article.article_tags.all().prefetch_related("tag")
            for at in article_tags:
                if at.tag:
                    tags.append(at.tag)
        
        article_dict = {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "summary": article.summary,
            "content": article.content,
            "rendered_content": article.rendered_content if hasattr(article, "rendered_content") else None,
            "status": article.status,
            "category": CategoryOut.model_validate(category) if category else None,
            "tags": [TagOut.model_validate(tag) for tag in tags],
            "cover_image": article.cover_image,
            "view_count": article.view_count,
            "is_featured": article.is_featured if hasattr(article, "is_featured") else False,
            "allow_comment": article.allow_comment,
            "seo_title": article.seo_title if hasattr(article, "seo_title") else None,
            "seo_description": article.seo_description if hasattr(article, "seo_description") else None,
            "seo_keywords": article.seo_keywords if hasattr(article, "seo_keywords") else None,
            "published_at": article.published_at if hasattr(article, "published_at") else None,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
        }
        draft_link = await ArticleService.get_draft_link_by_draft_id(article.id)
        article_dict["is_draft_copy"] = bool(draft_link)
        article_dict["source_article_id"] = draft_link.source_article_id if draft_link else None
        
        return success(article_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the article"
        )


@admin_router.put("/articles/{article_id}", response_model=dict)
async def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        article = await ArticleService.update_article(article_id, article_data)
        
        category = await article.category if article.category_id else None
        tags = []
        article_tags = await article.article_tags.all().prefetch_related("tag")
        for at in article_tags:
            if at.tag:
                tags.append(at.tag)
        
        article_dict = {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "summary": article.summary,
            "content": article.content,
            "rendered_content": article.rendered_content,
            "status": article.status,
            "category": CategoryOut.model_validate(category) if category else None,
            "tags": [TagOut.model_validate(tag) for tag in tags],
            "cover_image": article.cover_image,
            "view_count": article.view_count,
            "is_featured": article.is_featured,
            "allow_comment": article.allow_comment,
            "seo_title": article.seo_title,
            "seo_description": article.seo_description,
            "seo_keywords": article.seo_keywords,
            "published_at": article.published_at,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
        }
        draft_link = await ArticleService.get_draft_link_by_draft_id(article.id)
        article_dict["is_draft_copy"] = bool(draft_link)
        article_dict["source_article_id"] = draft_link.source_article_id if draft_link else None
        
        await _log_article_operation(
            action="article_update",
            current_admin=current_admin,
            request=request,
            article_id=article.id,
            detail=f"更新文章：{article.title}",
        )
        return success(article_dict, "Article updated successfully")
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the article"
        )


@admin_router.delete("/articles/{article_id}", response_model=dict)
async def delete_article(
    article_id: int,
    request: Request,
    hard_delete: bool = Query(True),
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        article = await ArticleService.get_article_by_id(article_id)
        article_title = article.title if article else f"#{article_id}"
        await ArticleService.delete_article(article_id, hard_delete=hard_delete)
        await _log_article_operation(
            action="article_delete" if hard_delete else "article_soft_delete",
            current_admin=current_admin,
            request=request,
            article_id=article_id,
            detail=f"{'彻底删除' if hard_delete else '软删除'}文章：{article_title}",
        )
        return success(None, "Article deleted successfully")
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the article"
        )


@admin_router.post("/articles/{article_id}/publish", response_model=dict)
async def publish_article(
    article_id: int,
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        article = await ArticleService.publish_article(article_id)
        await _log_article_operation(
            action="article_publish",
            current_admin=current_admin,
            request=request,
            article_id=article.id,
            detail=f"发布文章：{article.title}",
        )
        return success({"status": article.status}, "Article published successfully")
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while publishing the article"
        )


@admin_router.post("/articles/{article_id}/unpublish", response_model=dict)
async def unpublish_article(
    article_id: int,
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        article = await ArticleService.unpublish_article(article_id)
        await _log_article_operation(
            action="article_unpublish",
            current_admin=current_admin,
            request=request,
            article_id=article.id,
            detail=f"下架文章：{article.title}",
        )
        return success({"status": article.status}, "Article unpublished successfully")
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )


@admin_router.post("/articles/{article_id}/draft", response_model=dict)
async def create_or_update_article_draft(
    article_id: int,
    article_data: ArticleUpdate,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        draft = await ArticleService.create_or_update_draft_copy(article_id, article_data)
        category = await draft.category if draft.category_id else None
        tags = []
        article_tags = await draft.article_tags.all().prefetch_related("tag")
        for at in article_tags:
            if at.tag:
                tags.append(at.tag)
        article_dict = {
            "id": draft.id,
            "title": draft.title,
            "slug": draft.slug,
            "summary": draft.summary,
            "content": draft.content,
            "rendered_content": draft.rendered_content,
            "status": draft.status,
            "category": CategoryOut.model_validate(category) if category else None,
            "tags": [TagOut.model_validate(tag) for tag in tags],
            "cover_image": draft.cover_image,
            "view_count": draft.view_count,
            "is_featured": draft.is_featured,
            "allow_comment": draft.allow_comment,
            "seo_title": draft.seo_title,
            "seo_description": draft.seo_description,
            "seo_keywords": draft.seo_keywords,
            "published_at": draft.published_at,
            "created_at": draft.created_at,
            "updated_at": draft.updated_at,
            "is_draft_copy": True,
            "source_article_id": article_id,
        }
        return success(article_dict, "Draft copy saved successfully")
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while saving draft copy"
        )


@admin_router.post("/articles/drafts/{draft_id}/publish", response_model=dict)
async def publish_draft_to_source_article(
    draft_id: int,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        article = await ArticleService.publish_from_draft_copy(draft_id)
        return success({"id": article.id, "status": article.status}, "Draft published successfully")
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while publishing draft"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while unpublishing the article"
        )


@admin_router.post("/categories", response_model=dict)
async def create_category(
    category_data: CategoryCreate,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        category = await CategoryService.create_category(category_data)
        return success(CategoryOut.model_validate(category), "Category created successfully")
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the category"
        )


@admin_router.put("/categories/{category_id}", response_model=dict)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        category = await CategoryService.update_category(category_id, category_data)
        return success(CategoryOut.model_validate(category), "Category updated successfully")
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the category"
        )


@admin_router.delete("/categories/{category_id}", response_model=dict)
async def delete_category(
    category_id: int,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        await CategoryService.delete_category(category_id)
        return success(None, "Category deleted successfully")
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the category"
        )


@admin_router.post("/tags", response_model=dict)
async def create_tag(
    tag_data: TagCreate,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        tag = await TagService.create_tag(tag_data)
        return success(TagOut.model_validate(tag), "Tag created successfully")
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the tag"
        )


@admin_router.put("/tags/{tag_id}", response_model=dict)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        tag = await TagService.update_tag(tag_id, tag_data)
        return success(TagOut.model_validate(tag), "Tag updated successfully")
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the tag"
        )


@admin_router.delete("/tags/{tag_id}", response_model=dict)
async def delete_tag(
    tag_id: int,
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        await TagService.delete_tag(tag_id)
        return success(None, "Tag deleted successfully")
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the tag"
        )


router.include_router(admin_router)
