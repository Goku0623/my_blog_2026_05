import request from './index'

export interface GuestbookMessage {
  id: number
  guest_name: string
  content: string
  rendered_content?: string
  status: string
  ip_address?: string
  created_at: string
  updated_at?: string
}

export interface GuestbookMessageListResponse {
  items: GuestbookMessage[]
  total: number
  page: number
  page_size: number
}

export const getGuestbookMessages = (params: { page?: number; page_size?: number } = {}) => {
  return request.get<{ data: GuestbookMessageListResponse }>('/guestbook/messages', { params })
}

export const createGuestbookMessage = (content: string) => {
  return request.post<{ data: GuestbookMessage }>('/guestbook/messages', { content })
}

export const getAdminGuestbookMessages = (params: {
  status?: string
  keyword?: string
  page?: number
  page_size?: number
} = {}) => {
  return request.get<{ data: GuestbookMessageListResponse }>('/guestbook/admin/messages', { params })
}

export const guestbookMessageAction = (id: number, action: 'approve' | 'hide' | 'delete', reason?: string) => {
  return request.post(`/guestbook/admin/messages/${id}/action`, { action, reason })
}