import axios, { AxiosError, type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useGuestStore } from '@/stores/guest'

// 创建 Axios 实例
const request = axios.create({
  baseURL: '/api/v1',
  timeout: 12000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 是否为管理后台路径
const isAdminRoute = () => window.location.pathname.startsWith('/admin')

// 安全获取 auth store（避免 pinia 未初始化时报错）
const useAuthStoreSafe = () => {
  try {
    return useAuthStore()
  } catch {
    return null
  }
}

// 是否正在刷新 token
let isRefreshing = false
// 刷新 token 失败的请求队列
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

// 处理队列中的请求
const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error)
    } else {
      promise.resolve(token)
    }
  })
  failedQueue = []
}

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore()
    const guestStore = useGuestStore()

    // 如果是管理员已登录，注入 Bearer token
    if (authStore.isAuthenticated && authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }

    // 注入游客 token 到自定义请求头
    if (guestStore.guestToken) {
      config.headers['X-Guest-Token'] = guestStore.guestToken
    }

    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    // 401 错误处理：自动刷新 token 并重试（仅在已登录或管理路径下处理）
    const authStore = useAuthStoreSafe()
    const shouldHandle401 = error.response?.status === 401 && !originalRequest._retry &&
      (authStore?.isAuthenticated || isAdminRoute())

    if (shouldHandle401) {
      if (isRefreshing) {
        // 如果正在刷新 token，将请求加入队列
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            return request(originalRequest)
          })
          .catch((err) => {
            return Promise.reject(err)
          })
      }

      originalRequest._retry = true
      isRefreshing = true

      const authStore = useAuthStore()

      try {
        // 调用刷新 token 接口
        const response = await axios.post('/api/v1/auth/refresh', {
          refresh_token: authStore.refreshToken,
        }, { withCredentials: true })

        const { access_token, refresh_token } = response.data.data

        // 更新 token
        authStore.updateTokens(access_token, refresh_token)

        // 处理队列中的请求
        processQueue(null, access_token)

        // 重试原始请求
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }
        return request(originalRequest)
      } catch (refreshError) {
        // 刷新 token 失败，清空队列并登出
        processQueue(refreshError as Error, null)
        authStore.logout()
        if (isAdminRoute()) {
          window.location.href = '/admin/login'
        }
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default request
