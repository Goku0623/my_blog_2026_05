import axios, { AxiosError, type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useGuestStore } from '@/stores/guest'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

const isAdminRoute = () => window.location.pathname.startsWith('/admin')

const useAuthStoreSafe = () => {
  try {
    return useAuthStore()
  } catch {
    return null
  }
}

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

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

request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore()
    const guestStore = useGuestStore()

    if (authStore.isAuthenticated && authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }

    if (guestStore.guestToken) {
      config.headers['X-Guest-Token'] = guestStore.guestToken
    }

    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response) => {
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    const authStore = useAuthStoreSafe()
    const shouldHandle401 = error.response?.status === 401 && !originalRequest._retry &&
      !!authStore?.isAuthenticated &&
      !!authStore?.refreshToken

    if (shouldHandle401) {
      if (isRefreshing) {
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
        const response = await axios.post('/api/v1/auth/refresh', {
          refresh_token: authStore.refreshToken,
        }, { withCredentials: true })

        const { access_token, refresh_token } = response.data.data

        authStore.updateTokens(access_token, refresh_token)

        processQueue(null, access_token)

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }
        return request(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError as Error, null)
        await authStore.logout(false)
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
