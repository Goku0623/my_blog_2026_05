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
  scheduled_publish_at?: string
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

export interface HomeAggregateResponse {
  articles: ArticleListResponse
  featured: ArticleListResponse
  latest_items: Article[]
  categories: Category[]
  tags: Tag[]
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

export const getArticles = (params: ArticleListParams) => {
  return request.get<{ data: ArticleListResponse }>('/articles', { params })
}

export const getArticleStatsSummary = () => {
  return request.get<{ data: ArticleStatsSummary }>('/articles/stats/summary')
}

export const getHomeAggregate = (params: {
  page: number
  page_size: number
  featured_page: number
  featured_page_size: number
}) => {
  return request.get<{ data: HomeAggregateResponse }>('/home/aggregate', { params })
}

export const getArticle = (slug: string) => {
  return request.get<{ data: Article }>(`/articles/${slug}`)
}

export const searchArticles = (params: {
  keyword: string
  page?: number
  page_size?: number
  search_in?: 'title' | 'summary' | 'title_summary'
  time_filter?: 'all' | '7d' | '30d' | '90d' | '365d'
}) => {
  return request.get<{ data: ArticleListResponse }>('/articles/search', { params })
}

export const getCategories = () => {
  return request.get<{ data: Category[] }>('/categories')
}

export const getTags = () => {
  return request.get<{ data: Tag[] }>('/tags')
}

export const getAdminArticles = (params: ArticleListParams) => {
  return request.get<{ data: ArticleListResponse }>('/admin/articles', { params })
}

export const getAdminArticle = (id: number) => {
  return request.get<{ data: Article }>(`/admin/articles/${id}`)
}

export const createArticle = (data: Partial<Article>) => {
  return request.post<{ data: Article }>('/admin/articles', data)
}

export const updateArticle = (id: number, data: Partial<Article>) => {
  return request.put<{ data: Article }>(`/admin/articles/${id}`, data)
}

export const deleteArticle = (id: number, hardDelete: boolean = true) => {
  return request.delete(`/admin/articles/${id}`, {
    params: { hard_delete: hardDelete },
  })
}

export const publishArticle = (id: number) => {
  return request.post(`/admin/articles/${id}/publish`)
}

export const unpublishArticle = (id: number) => {
  return request.post(`/admin/articles/${id}/unpublish`)
}

export const saveArticleDraftCopy = (id: number, data: Partial<Article>) => {
  return request.post<{ data: Article }>(`/admin/articles/${id}/draft`, data)
}

export const publishDraftToSource = (draftId: number) => {
  return request.post<{ data: { id: number; status: string } }>(`/admin/articles/drafts/${draftId}/publish`)
}

export const createCategory = (data: CategoryPayload) => {
  return request.post('/admin/categories', data)
}

export const updateCategory = (id: number, data: Partial<CategoryPayload>) => {
  return request.put(`/admin/categories/${id}`, data)
}

export const deleteCategory = (id: number) => {
  return request.delete(`/admin/categories/${id}`)
}

export const createTag = (data: TagPayload) => {
  return request.post('/admin/tags', data)
}

export const updateTag = (id: number, data: Partial<TagPayload>) => {
  return request.put(`/admin/tags/${id}`, data)
}

export const deleteTag = (id: number) => {
  return request.delete(`/admin/tags/${id}`)
}
