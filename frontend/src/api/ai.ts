import request from './index'

export interface AiWeatherParams {
  latitude?: number
  longitude?: number
  city?: string
}

export interface AiWeatherData {
  city: string
  temperature: number
  feels_like: number
  description: string
  humidity: number
  wind_speed: number
  icon: string
  updated_at: string
}

export interface AiCommentReplyParams {
  comment_id: number
  article_title: string
  comment_content: string
  context_comments?: string[]
}

// 获取天气信息
export const getWeather = (params: AiWeatherParams) => {
  return request.get<{ data: AiWeatherData }>('/ai/weather', { params })
}

// 管理端：AI 生成评论回复
export const generateCommentReply = (data: AiCommentReplyParams) => {
  return request.post('/ai/admin/comment-reply', data)
}
