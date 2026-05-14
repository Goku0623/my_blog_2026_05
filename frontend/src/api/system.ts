import request from './index'

export interface SiteConfig {
  site_name: string
  site_description: string
  site_keywords: string
  site_author: string
  icp_number?: string
  admin_email: string
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
  level: 'low' | 'medium' | 'high'
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

// 获取站点配置（前台，返回键值对结构）
export const getSiteConfig = () => {
  return request.get<{ data: SiteConfig }>('/system/configs/public')
}

// 管理端：获取所有配置
export const getAdminConfigs = () => {
  return request.get<{ data: SystemConfigItem[] }>('/admin/system/configs')
}

// 管理端：更新单个配置
export const updateAdminConfig = (key: string, value: string) => {
  return request.put(`/admin/system/configs/${key}`, { value })
}

// 管理端：批量更新配置
export const bulkUpdateConfigs = (configs: { key: string; value: string }[]) => {
  return request.post<{ data: SystemConfigItem[] }>('/admin/system/configs/bulk', { configs })
}

// 管理端：获取敏感词列表
export const getSensitiveWords = () => {
  return request.get<{ data: SensitiveWord[] }>('/admin/system/sensitive-words')
}

// 管理端：添加敏感词
export const addSensitiveWord = (data: { word: string; level: string }) => {
  return request.post<{ data: SensitiveWord }>('/admin/system/sensitive-words', data)
}

// 管理端：删除敏感词
export const deleteSensitiveWord = (id: number) => {
  return request.delete(`/admin/system/sensitive-words/${id}`)
}

// 管理端：刷新敏感词缓存
export const refreshSensitiveWordsCache = () => {
  return request.post('/admin/system/sensitive-words/refresh-cache')
}

// 管理端：获取操作日志
export const getOperationLogs = (params: LogListParams, signal?: AbortSignal) => {
  return request.get<{ data: LogListResponse }>('/admin/system/logs', { params, signal })
}

// 管理端：获取定时任务列表
export const getScheduledTasks = () => {
  return request.get('/admin/system/tasks')
}

// 管理端：更新定时任务
export const updateScheduledTask = (taskId: number, data: { is_active?: boolean; cron_expression?: string }) => {
  return request.put(`/admin/system/tasks/${taskId}`, data)
}

// 管理端：手动触发定时任务
export const triggerScheduledTask = (taskId: number) => {
  return request.post(`/admin/system/tasks/${taskId}/trigger`)
}
