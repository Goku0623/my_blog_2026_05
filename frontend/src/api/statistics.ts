import request from './index'

export interface DashboardStats {
  total_articles: number
  total_comments: number
  total_views: number
  today_views: number
}

export interface TrendItem {
  date: string
  value: number
}

export interface TrendResponse {
  metric: string
  period: string
  data: TrendItem[]
}

export interface ArticleStats {
  id: number
  title: string
  view_count: number
  comment_count: number
}

export interface CategoryStats {
  category_name: string
  article_count: number
}

export interface SystemHealth {
  status: string
  database: string
  redis: string
  celery: string
  uptime: string
}

export interface RecentComment {
  id: number
  article_id: number
  article_title: string
  guest_name: string
  content: string
  created_at: string
}

export interface ApiMonitor {
  endpoint: string
  method: string
  total_calls: number
  avg_latency: number
  error_rate: number
}

interface BackendSystemHealth {
  overall_status?: string
  services?: Array<{ service?: string; status?: string }>
  uptime?: string
}

interface BackendApiMonitor {
  top_endpoints?: Array<{
    endpoint?: string
    method?: string
    call_count?: number
    avg_response_ms?: number
    error_count?: number
  }>
}

interface BackendRecentComment {
  id?: number
  article_id?: number
  article_title?: string
  guest_name?: string
  content?: string
  created_at?: string
  guest?: {
    nickname?: string
    guest_token?: string
  }
  comment_count?: number
  latest_comment_at?: string
}

export interface CeleryTaskStat {
  task_name: string
  total_count: number
  success_count: number
  fail_count: number
  avg_duration: number
}

// 获取仪表盘统计数据
export const getDashboardStats = () => {
  return request.get<{ data: DashboardStats }>('/admin/statistics/dashboard')
}

// 获取趋势数据
export const getTrends = (metric: 'views' | 'comments' | 'articles' | 'visitors', period: 'day' | 'week' | 'month') => {
  return request.get<{ data: TrendResponse }>('/admin/statistics/trends', {
    params: { metric, period },
  })
}

// 获取热门文章排行
export const getTopArticles = (limit: number = 10) => {
  return request.get<{ data: ArticleStats[] }>('/admin/statistics/articles/top-viewed', {
    params: { limit },
  })
}

// 获取分类统计
export const getCategoryStats = () => {
  return request.get<{ data: CategoryStats[] }>('/admin/statistics/categories/distribution')
}

// 获取系统健康状态
export const getSystemHealth = () => {
  return request.get<{ data: BackendSystemHealth }>('/admin/statistics/health').then((response) => {
    const payload = response.data?.data ?? {}
    const services = payload.services ?? []
    const byName = (name: string) =>
      services.find((item) => item.service?.toLowerCase().includes(name.toLowerCase()))?.status

    const databaseStatus = byName('postgres') || byName('database') || 'unknown'
    const redisStatus = byName('redis') || 'unknown'
    const celeryStatus = byName('celery') || 'unknown'

    const normalized: SystemHealth = {
      status: payload.overall_status || 'unknown',
      database: databaseStatus,
      redis: redisStatus,
      celery: celeryStatus,
      uptime: payload.uptime || '-',
    }

    return {
      ...response,
      data: {
        ...response.data,
        data: normalized,
      },
    }
  })
}

// 获取最近评论
export const getRecentComments = (limit: number = 10) => {
  return request.get<{ data: BackendRecentComment[] }>('/admin/statistics/comments/recent', {
    params: { limit }
  }).then((response) => {
    const rows = response.data?.data ?? []
    const normalized: RecentComment[] = rows.map((item, index) => {
      const guestShortCode = (item.guest?.guest_token || '').replace(/-/g, '').toUpperCase().slice(0, 6)
      const displayGuestName = item.guest_name || item.guest?.nickname || (guestShortCode ? `游客${guestShortCode}` : '游客')
      return {
      id: item.id ?? Number(`${item.article_id ?? 0}${index}`),
      article_id: item.article_id ?? 0,
      article_title: item.article_title ?? '未命名文章',
      guest_name: displayGuestName,
      content: item.content ?? '',
      created_at: item.created_at ?? item.latest_comment_at ?? new Date().toISOString(),
      }
    })
    return {
      ...response,
      data: {
        ...response.data,
        data: normalized,
      },
    }
  })
}

// 获取 API 调用监控
export const getApiMonitor = (hours: number = 24) => {
  return request.get<{ data: BackendApiMonitor | ApiMonitor[] }>('/admin/statistics/api-monitor', {
    params: { hours }
  }).then((response) => {
    const payload = response.data?.data
    const endpoints = Array.isArray(payload) ? payload : (payload?.top_endpoints ?? [])
    const normalized: ApiMonitor[] = endpoints.map((item: any) => {
      const totalCalls = Number(item.total_calls ?? item.call_count ?? 0)
      const errorCount = Number(item.error_count ?? 0)
      return {
        endpoint: item.endpoint ?? 'unknown',
        method: item.method ?? 'GET',
        total_calls: totalCalls,
        avg_latency: Number(item.avg_latency ?? item.avg_response_ms ?? 0),
        error_rate: totalCalls > 0 ? errorCount / totalCalls : Number(item.error_rate ?? 0),
      }
    })
    return {
      ...response,
      data: {
        ...response.data,
        data: normalized,
      },
    }
  })
}

// 获取 Celery 任务统计
export const getCeleryStats = () => {
  return request.get<{ data: CeleryTaskStat[] }>('/admin/statistics/celery')
}
