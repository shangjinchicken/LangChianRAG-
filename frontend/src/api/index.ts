import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// 请求拦截器：自动带上 JWT Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理 401 未授权
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    }
    return Promise.reject(error)
  }
)

// === Auth API ===
export const authAPI = {
  register: (data: { username: string; password: string; email?: string }) =>
    api.post('/auth/register', data),
  login: (data: { username: string; password: string }) =>
    api.post('/auth/login', data),
  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post('/auth/change-password', data),
  getMe: () => api.get('/auth/me'),
}

// === Conversations API ===
export const conversationAPI = {
  list: () => api.get('/conversations'),
  create: (data?: { title?: string }) => api.post('/conversations', data || {}),
  update: (id: string, data: { title: string }) => api.patch(`/conversations/${id}`, data),
  delete: (id: string) => api.delete(`/conversations/${id}`),
  getMessages: (id: string, params?: { limit?: number; offset?: number }) =>
    api.get(`/conversations/${id}/messages`, { params }),
}

// === Knowledge API ===
export const knowledgeAPI = {
  listDocuments: (params?: { page?: number; pageSize?: number }) =>
    api.get('/knowledge/documents', { params }),
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteDocument: (id: string) => api.delete(`/knowledge/documents/${id}`),
  reprocess: (id: string) => api.post(`/knowledge/documents/${id}/reprocess`),
  getStats: () => api.get('/knowledge/stats'),
}

export default api
