import request from './index'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  expires_in: number
}

export interface AdminInfo {
  id: number
  username: string
  email?: string
  is_active: boolean
  last_login_at?: string | null
  created_at: string
}

// 管理员登录
export const login = (data: LoginParams) => {
  return request.post<{ data: LoginResponse }>('/auth/login', data)
}

// 刷新 token
export const refreshToken = (refreshToken: string) => {
  return request.post<{ data: LoginResponse }>('/auth/refresh', {
    refresh_token: refreshToken,
  })
}

// 获取管理员信息
export const getAdminInfo = () => {
  return request.get<{ data: AdminInfo }>('/auth/me')
}

// 更新管理员资料
export const updateAdminProfile = (data: { username: string; email?: string }) => {
  return request.put<{ data: AdminInfo }>('/auth/me', data)
}

// 管理员登出
export const logout = () => {
  return request.post('/auth/logout')
}

// 修改密码
export const changePassword = (data: { old_password: string; new_password: string }) => {
  return request.put('/auth/change-password', data)
}
