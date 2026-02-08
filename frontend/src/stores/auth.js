import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const refreshToken = ref(localStorage.getItem('refreshToken') || null)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || null)
  const isAdmin = computed(() => user.value?.role === 'Admin')
  const userName = computed(() => user.value?.full_name || user.value?.email || '')

  // Actions
  async function login(email, password) {
    const response = await authApi.login(email, password)
    const data = response.data

    // Backend returns { user: {...}, tokens: { access_token, refresh_token } }
    token.value = data.tokens.access_token
    refreshToken.value = data.tokens.refresh_token
    user.value = data.user

    localStorage.setItem('token', data.tokens.access_token)
    localStorage.setItem('refreshToken', data.tokens.refresh_token)

    return data
  }

  async function register(userData) {
    const response = await authApi.register(userData)
    return response.data
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const response = await authApi.getMe()
      user.value = response.data
    } catch {
      logout()
    }
  }

  async function doRefreshToken() {
    if (!refreshToken.value) throw new Error('No refresh token')

    const response = await authApi.refreshToken(refreshToken.value)
    const data = response.data

    token.value = data.access_token
    refreshToken.value = data.refresh_token

    localStorage.setItem('token', data.access_token)
    localStorage.setItem('refreshToken', data.refresh_token)

    return data
  }

  function logout() {
    user.value = null
    token.value = null
    refreshToken.value = null

    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')

    router.push('/login')
  }

  // Fetch user info on init if we have a token
  if (token.value) {
    fetchUser()
  }

  return {
    user,
    token,
    refreshToken,
    isAuthenticated,
    userRole,
    isAdmin,
    userName,
    login,
    register,
    fetchUser,
    doRefreshToken,
    logout
  }
})
