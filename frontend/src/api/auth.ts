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
  avatar?: string | null
  is_active: boolean
  last_login_at?: string | null
  created_at: string
}

export const login = (data: LoginParams) => {
  return request.post<{ data: LoginResponse }>('/auth/login', data)
}

export const refreshToken = (refreshToken: string) => {
  return request.post<{ data: LoginResponse }>('/auth/refresh', {
    refresh_token: refreshToken,
  })
}

export const getAdminInfo = () => {
  return request.get<{ data: AdminInfo }>('/auth/me')
}

export const updateAdminProfile = (data: { username: string; email?: string; avatar?: string | null }) => {
  return request.put<{ data: AdminInfo }>('/auth/me', data)
}

export const logout = () => {
  return request.post('/auth/logout')
}

export const changePassword = (data: { old_password: string; new_password: string }) => {
  return request.put('/auth/change-password', data)
}
