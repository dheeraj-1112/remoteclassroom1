import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('rc_token')
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

export function unwrapList(data) {
  return Array.isArray(data) ? data : (data?.results || [])
}

export function errorMessage(error) {
  const data = error?.response?.data
  if (!data) return error?.message || 'Something went wrong. Please try again.'
  if (typeof data.detail === 'string') return data.detail
  const first = Object.values(data)[0]
  if (Array.isArray(first)) return first[0]
  if (typeof first === 'string') return first
  return 'Please check the information and try again.'
}

export default api
