import request from './index'

export interface Tag {
  id: number
  name: string
  slug: string
  color?: string
}

export interface ArticleCategory {
  id: number
  name: string
  slug: string
}

export interface Article {
  id: number
  title: string
  slug: string
  summary: string
  content?: string
  rendered_content?: string
  cover_image?: string
  cover_image_thumb?: string
  cover_image_large?: string
  category?: ArticleCategory | null
  category_id?: number
  category_name?: string
  tags?: Tag[]
  view_count: number
  comment_count?: number
  allow_comment?: boolean
  status: string
  is_featured?: boolean
  is_published?: boolean
  published_at?: string
  created_at: string
  updated_at: string
  is_draft_copy?: boolean
  source_article_id?: number | null
}

export interface ArticleListParams {
  page?: number
  page_size?: number
  category_id?: number
  tag_id?: number
  keyword?: string
  is_published?: boolean
  status_filter?: string
  is_featured?: boolean
}

export interface ArticleListResponse {
  items: Article[]
  total: number
  total_views?: number
  page: number
  page_size: number
}

export interface ArticleStatsSummary {
  total_views: number
}

export interface Category {
  id: number
  name: string
  slug: string
  description?: string
  article_count: number
}

export interface CategoryPayload {
  name: string
  slug: string
  description?: string
  sort_order?: number
  is_active?: boolean
}

export interface TagPayload {
  name: string
  slug: string
  color?: string
}

// 获取文章列表（前台）
export const getArticles = (params: ArticleListParams) => {
  return request.get<{ data: ArticleListResponse }>('/articles', { params })
}

// 获取文章统计概览（前台）
export const getArticleStatsSummary = () => {
  return request.get<{ data: ArticleStatsSummary }>('/articles/stats/summary')
}

// 获取文章详情（前台）
export const getArticle = (slug: string) => {
  return request.get<{ data: Article }>(`/articles/${slug}`)
}

// 搜索文章（支持字段与时间筛选）
export const searchArticles = (params: {
  keyword: string
  page?: number
  page_size?: number
  search_in?: 'title' | 'summary' | 'title_summary'
  time_filter?: 'all' | '7d' | '30d' | '90d' | '365d'
}) => {
  return request.get<{ data: ArticleListResponse }>('/articles/search', { params })
}

// 获取所有分类
export const getCategories = () => {
  return request.get<{ data: Category[] }>('/categories')
}

// 获取所有标签
export const getTags = () => {
  return request.get<{ data: Tag[] }>('/tags')
}

// 管理端：获取文章列表
export const getAdminArticles = (params: ArticleListParams) => {
  return request.get<{ data: ArticleListResponse }>('/admin/articles', { params })
}

// 管理端：获取文章详情
export const getAdminArticle = (id: number) => {
  return request.get<{ data: Article }>(`/admin/articles/${id}`)
}

// 管理端：创建文章
export const createArticle = (data: Partial<Article>) => {
  return request.post<{ data: Article }>('/admin/articles', data)
}

// 管理端：更新文章
export const updateArticle = (id: number, data: Partial<Article>) => {
  return request.put<{ data: Article }>(`/admin/articles/${id}`, data)
}

// 管理端：删除文章
export const deleteArticle = (id: number, hardDelete: boolean = true) => {
  return request.delete(`/admin/articles/${id}`, {
    params: { hard_delete: hardDelete },
  })
}

// 管理端：发布文章
export const publishArticle = (id: number) => {
  return request.post(`/admin/articles/${id}/publish`)
}

// 管理端：取消发布文章
export const unpublishArticle = (id: number) => {
  return request.post(`/admin/articles/${id}/unpublish`)
}

// 管理端：从已发布文章保存/更新草稿副本
export const saveArticleDraftCopy = (id: number, data: Partial<Article>) => {
  return request.post<{ data: Article }>(`/admin/articles/${id}/draft`, data)
}

// 管理端：将草稿副本发布回原文并删除草稿
export const publishDraftToSource = (draftId: number) => {
  return request.post<{ data: { id: number; status: string } }>(`/admin/articles/drafts/${draftId}/publish`)
}

// 管理端：创建分类
export const createCategory = (data: CategoryPayload) => {
  return request.post('/admin/categories', data)
}

// 管理端：更新分类
export const updateCategory = (id: number, data: Partial<CategoryPayload>) => {
  return request.put(`/admin/categories/${id}`, data)
}

// 管理端：删除分类
export const deleteCategory = (id: number) => {
  return request.delete(`/admin/categories/${id}`)
}

// 管理端：创建标签
export const createTag = (data: TagPayload) => {
  return request.post('/admin/tags', data)
}

// 管理端：更新标签
export const updateTag = (id: number, data: Partial<TagPayload>) => {
  return request.put(`/admin/tags/${id}`, data)
}

// 管理端：删除标签
export const deleteTag = (id: number) => {
  return request.delete(`/admin/tags/${id}`)
}
