import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../api'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<any>(null)
  const token = ref<string | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // 从 localStorage 恢复登录状态
  function restoreSession() {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    if (savedToken && savedUser) {
      try {
        const parsed = JSON.parse(savedUser)
        // 确保解析出的是有效的用户对象（修复之前后端漏返回 user 导致存储无效数据的问题）
        if (parsed && typeof parsed === 'object' && parsed.id && parsed.role) {
          token.value = savedToken
          user.value = parsed
        } else {
          clearSession()
        }
      } catch {
        clearSession()
      }
    }
  }

  function clearSession() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function login(username: string, password: string) {
    const res = await authAPI.login({ username, password })
    const data = res.data
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    return data
  }

  async function register(username: string, password: string, email?: string) {
    const res = await authAPI.register({ username, password, email })
    return res.data
  }

  function logout() {
    clearSession()
    router.push('/login')
  }

  // 初始化时恢复会话
  restoreSession()

  return { user, token, isLoggedIn, isAdmin, login, register, logout, restoreSession, clearSession }
})
