import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getAdminInfo, logout as logoutApi, type LoginParams, type AdminInfo } from '@/api/auth'

const TOKEN_KEY = 'admin_token'
const REFRESH_TOKEN_KEY = 'admin_refresh_token'
const ADMIN_INFO_KEY = 'admin_info'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_TOKEN_KEY))
  const adminInfo = ref<AdminInfo | null>(
    localStorage.getItem(ADMIN_INFO_KEY)
      ? JSON.parse(localStorage.getItem(ADMIN_INFO_KEY) as string)
      : null
  )

  const isAuthenticated = computed(() => !!token.value)

  const login = async (params: LoginParams) => {
    try {
      const response = await loginApi(params)
      const { access_token, refresh_token } = response.data.data

      token.value = access_token
      refreshToken.value = refresh_token
      localStorage.setItem(TOKEN_KEY, access_token)
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)

      await fetchAdminInfo()

      return true
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  const fetchAdminInfo = async () => {
    try {
      const response = await getAdminInfo()
      adminInfo.value = response.data.data
      localStorage.setItem(ADMIN_INFO_KEY, JSON.stringify(adminInfo.value))
    } catch (error) {
      console.error('获取管理员信息失败:', error)
      throw error
    }
  }

  const updateTokens = (newToken: string, newRefreshToken: string) => {
    token.value = newToken
    refreshToken.value = newRefreshToken
    localStorage.setItem(TOKEN_KEY, newToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken)
  }

  const logout = async (callApi = true) => {
    try {
      if (callApi && token.value) {
        await logoutApi()
      }
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      token.value = null
      refreshToken.value = null
      adminInfo.value = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem(ADMIN_INFO_KEY)
    }
  }

  const checkAuth = async () => {
    if (token.value && !adminInfo.value) {
      try {
        await fetchAdminInfo()
      } catch (error) {
        await logout(false)
      }
    }
  }

  return {
    token,
    refreshToken,
    adminInfo,
    isAuthenticated,
    login,
    logout,
    updateTokens,
    fetchAdminInfo,
    checkAuth,
  }
})
