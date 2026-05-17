import request from './index'

export interface Comment {
  id: number
  article_id: number
  guest?: {
    id: number
    guest_token: string
    nickname?: string
    avatar?: string | null
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

export const createComment = (data: CreateCommentParams) => {
  return request.post<{ data: Comment }>('/comments', data)
}

export const getGuestIdentity = () => {
  return request.get<{ data: GuestIdentity }>('/guest/identity')
}

export const getAdminComments = (params: CommentListParams, signal?: AbortSignal) => {
  return request.get<{ data: CommentListResponse }>('/admin/comments', {
    params,
    signal,
  }).then((response) => {
    response.data.data.items = response.data.data.items.map(normalizeComment)
    return response
  })
}

export const adminCommentAction = (commentId: number, action: string, reason?: string) => {
  return request.post(`/admin/comments/${commentId}/action`, { action, reason })
}

export const adminReplyComment = (commentId: number, content: string) => {
  return request.post(`/admin/comments/${commentId}/reply`, { content })
}
