import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const loading = ref(false)
  const error = ref('')

  const isAuthenticated = computed(() => !!accessToken.value)

  async function login(email, password) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.post('/auth/login', { email, password })
      accessToken.value = response.data.access_token
      refreshToken.value = response.data.refresh_token
      localStorage.setItem('access_token', accessToken.value)
      localStorage.setItem('refresh_token', refreshToken.value)
      await fetchMe()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Login failed. Please check your credentials.'
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(email, password) {
    loading.value = true
    error.value = ''
    try {
      const response = await api.post('/auth/register', { email, password })
      accessToken.value = response.data.access_token
      refreshToken.value = response.data.refresh_token
      localStorage.setItem('access_token', accessToken.value)
      localStorage.setItem('refresh_token', refreshToken.value)
      await fetchMe()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Registration failed.'
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!accessToken.value) return null
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      return user.value
    } catch (err) {
      user.value = null
      return null
    }
  }

  function logout() {
    user.value = null
    accessToken.value = ''
    refreshToken.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    error,
    isAuthenticated,
    login,
    register,
    fetchMe,
    logout,
  }
})
