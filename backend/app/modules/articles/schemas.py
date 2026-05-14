from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=20)


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    slug: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=20)


class TagOut(BaseModel):
    id: int
    name: str
    slug: str
    color: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)
    category_id: Optional[int] = None
    tag_ids: List[int] = Field(default_factory=list)
    status: str = Field(default="draft")
    cover_image: Optional[str] = None
    is_featured: bool = False
    allow_comment: bool = True
    seo_title: Optional[str] = Field(None, max_length=200)
    seo_description: Optional[str] = Field(None, max_length=500)
    seo_keywords: Optional[str] = Field(None, max_length=200)


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    summary: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    status: Optional[str] = None
    cover_image: Optional[str] = None
    is_featured: Optional[bool] = None
    allow_comment: Optional[bool] = None
    seo_title: Optional[str] = Field(None, max_length=200)
    seo_description: Optional[str] = Field(None, max_length=500)
    seo_keywords: Optional[str] = Field(None, max_length=200)


class ArticleOut(BaseModel):
    id: int
    title: str
    slug: str
    summary: Optional[str]
    content: str
    rendered_content: Optional[str]
    status: str
    category: Optional[CategoryOut]
    tags: List[TagOut]
    cover_image: Optional[str] = None
    cover_image_thumb: Optional[str] = None
    cover_image_large: Optional[str] = None
    view_count: int
    is_featured: bool
    allow_comment: bool
    seo_title: Optional[str]
    seo_description: Optional[str]
    seo_keywords: Optional[str]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleListItem(BaseModel):
    id: int
    title: str
    slug: str
    summary: Optional[str]
    status: str
    category: Optional[CategoryOut]
    tags: List[TagOut]
    # 列表只返回缩略图（约 10-30KB），节省带宽，前端卡片直接渲染。
    cover_image_thumb: Optional[str] = None
    view_count: int
    is_featured: bool
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleSearchResult(BaseModel):
    id: int
    title: str
    slug: str
    summary: Optional[str]
    highlight: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PaginatedArticles(BaseModel):
    items: List[ArticleListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
