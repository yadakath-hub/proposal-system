import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import router from '@/router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor — attach token
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const authStore = useAuthStore()

    if (error.response?.status === 401) {
      // Token expired — try refresh
      if (!error.config._retry && authStore.refreshToken) {
        error.config._retry = true
        try {
          await authStore.doRefreshToken()
          error.config.headers.Authorization = `Bearer ${authStore.token}`
          return api(error.config)
        } catch {
          authStore.logout()
          router.push('/login')
          ElMessage.error('登入已過期，請重新登入')
        }
      } else {
        authStore.logout()
        router.push('/login')
      }
    } else if (error.response?.status === 403) {
      ElMessage.error('權限不足')
    } else if (error.response?.status >= 500) {
      ElMessage.error('伺服器錯誤，請稍後再試')
    } else if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    }

    return Promise.reject(error)
  }
)

export default api
