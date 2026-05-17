import request from './index'

export interface SiteConfig {
  site_name: string
  site_description: string
  site_keywords: string
  site_author: string
  icp_number?: string
  admin_email: string
  admin_avatar?: string
  github_url?: string
  bilibili_url?: string
  site_started_at?: string
  comment_enabled: boolean
  comment_audit_enabled: boolean
  ai_enabled: boolean
  cover_image_max_size_mb?: number
}

export interface SystemConfigItem {
  id?: number
  key: string
  value: string
  value_type: string
  description?: string
}

export interface SensitiveWord {
  id: number
  word: string
  category?: string
  created_at: string
}

export interface OperationLog {
  id: number
  operator: string
  action: string
  target_type?: string
  target_id?: number
  detail?: string
  ip_address: string
  result: string
  created_at: string
}

export interface LogListParams {
  page?: number
  page_size?: number
  operator?: string
  action?: string
  start_date?: string
  end_date?: string
}

export interface LogListResponse {
  items: OperationLog[]
  total: number
  page: number
  page_size: number
}

export const getSiteConfig = () => {
  return request.get<{ data: SiteConfig }>('/system/configs/public')
}

export const getAdminConfigs = () => {
  return request.get<{ data: SystemConfigItem[] }>('/admin/system/configs')
}

export const updateAdminConfig = (key: string, value: string) => {
  return request.put(`/admin/system/configs/${key}`, { value })
}

export const bulkUpdateConfigs = (configs: { key: string; value: string }[]) => {
  return request.post<{ data: SystemConfigItem[] }>('/admin/system/configs/bulk', { configs })
}

export const getSensitiveWords = () => {
  return request.get<{ data: SensitiveWord[] }>('/admin/system/sensitive-words')
}

export const addSensitiveWord = (data: { word: string; category?: string }) => {
  return request.post<{ data: SensitiveWord }>('/admin/system/sensitive-words', data)
}

export const importSensitiveWords = (items: Array<{ word: string; category?: string }>) => {
  return request.post<{ data: { created: number; skipped: number } }>('/admin/system/sensitive-words/import', { items })
}

export const deleteSensitiveWord = (id: number) => {
  return request.delete(`/admin/system/sensitive-words/${id}`)
}

export const refreshSensitiveWordsCache = () => {
  return request.post('/admin/system/sensitive-words/refresh-cache')
}

export const getOperationLogs = (params: LogListParams, signal?: AbortSignal) => {
  return request.get<{ data: LogListResponse }>('/admin/system/logs', { params, signal })
}

export const getScheduledTasks = () => {
  return request.get('/admin/system/tasks')
}

export const updateScheduledTask = (taskId: number, data: { is_active?: boolean; cron_expression?: string }) => {
  return request.put(`/admin/system/tasks/${taskId}`, data)
}

export const triggerScheduledTask = (taskId: number) => {
  return request.post(`/admin/system/tasks/${taskId}/trigger`)
}

export interface AdminNotification {
  id: number
  type: string
  title: string
  content: string | null
  link: string | null
  source_id: number | null
  is_read: boolean
  created_at: string
}

export interface NotificationListResponse {
  items: AdminNotification[]
  total: number
  page: number
  page_size: number
}

export const getNotifications = (page: number = 1, page_size: number = 10) => {
  return request.get<{ data: NotificationListResponse }>('/admin/system/notifications', {
    params: { page, page_size },
  })
}

export const getUnreadNotificationCount = () => {
  return request.get<{ data: { count: number } }>('/admin/system/notifications/unread-count')
}

export const markNotificationRead = (notificationId: number) => {
  return request.put(`/admin/system/notifications/${notificationId}/read`)
}

export const markAllNotificationsRead = () => {
  return request.put('/admin/system/notifications/read-all')
}
