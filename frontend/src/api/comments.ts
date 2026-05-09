import request from './index'

export interface Comment {
  id: number
  article_id: number
  guest?: {
    id: number
    guest_token: string
    nickname?: string
    created_at: string
  }
  article_title?: string
  parent_id?: number
  guest_name: string
  guest_email?: string
  guest_website?: string
  content: string
  ip_address: string
  user_agent: string
  status?: string
  created_at: string
  replies?: Comment[]
}

export interface CommentListParams {
  article_id?: number
  status?: string
  keyword?: string
  page?: number
  page_size?: number
}

export interface CommentListResponse {
  items: Comment[]
  total: number
  page: number
  page_size: number
}

export interface CreateCommentParams {
  article_id: number
  parent_id?: number
  content: string
}

export interface GuestIdentity {
  id: number
  guest_token: string
  nickname?: string
  created_at: string
}

const normalizeComment = (comment: any): Comment => {
  const shortCode = (comment.guest?.guest_token || '').replace(/-/g, '').toUpperCase().slice(0, 6)
  const defaultGuestName = shortCode ? `游客${shortCode}` : '游客'
  const guestName = comment.guest?.nickname
    || (comment.guest_name && comment.guest_name !== '游客' ? comment.guest_name : '')
    || defaultGuestName
  return {
    ...comment,
    guest_name: guestName,
    replies: Array.isArray(comment.replies) ? comment.replies.map(normalizeComment) : [],
  } as Comment
}

// 获取评论列表（前台，仅显示已发布）
export const getComments = (params: CommentListParams) => {
  const { article_id, ...rest } = params
  if (!article_id) {
    return Promise.reject(new Error('article_id is required for getComments'))
  }
  return request
    .get<{ data: CommentListResponse }>(`/articles/${article_id}/comments`, { params: rest })
    .then((response) => {
      response.data.data.items = response.data.data.items.map(normalizeComment)
      return response
    })
}

// 创建评论（前台）
export const createComment = (data: CreateCommentParams) => {
  return request.post<{ data: Comment }>('/comments', data)
}

// 获取游客身份（若无则自动创建）
export const getGuestIdentity = () => {
  return request.get<{ data: GuestIdentity }>('/guest/identity')
}

// 管理端：获取评论列表
export const getAdminComments = (params: CommentListParams) => {
  return request.get<{ data: CommentListResponse }>('/admin/comments', {
    params,
  }).then((response) => {
    response.data.data.items = response.data.data.items.map(normalizeComment)
    return response
  })
}

// 管理端：评论管理动作 (hide / delete / pin / unpin)
export const commentAction = (id: number, action: string, reason?: string) => {
  return request.post(`/admin/comments/${id}/action`, { action, reason })
}

// 管理端：管理员回复评论
export const adminReplyComment = (id: number, content: string) => {
  return request.post(`/admin/comments/${id}/reply`, { content })
}
