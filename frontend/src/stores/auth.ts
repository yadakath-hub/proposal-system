import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { login as apiLogin, getMe } from '../api/auth'
import type { User } from '../types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(
    () => !!user.value && !!localStorage.getItem('access_token')
  )

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const { data } = await apiLogin({ email, password })
      localStorage.setItem('access_token', data.tokens.access_token)
      localStorage.setItem('refresh_token', data.tokens.refresh_token)
      user.value = data.user
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    try {
      const { data } = await getMe()
      user.value = data
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { user, loading, isAuthenticated, login, fetchUser, logout }
})
