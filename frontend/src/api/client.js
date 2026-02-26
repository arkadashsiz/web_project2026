import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

let isRefreshing = false
let waitQueue = []

function flushQueue(error, token = null) {
  waitQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token)
  })
  waitQueue = []
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error?.config
    const status = error?.response?.status

    if (!originalRequest || status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    const refresh = localStorage.getItem('refresh')
    if (!refresh) {
      localStorage.removeItem('access')
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        waitQueue.push({ resolve, reject })
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`
        return api(originalRequest)
      })
    }

    originalRequest._retry = true
    isRefreshing = true
    try {
      const res = await axios.post('/api/auth/refresh/', { refresh })
      const newAccess = res.data?.access
      if (!newAccess) {
        throw new Error('No access token in refresh response')
      }
      localStorage.setItem('access', newAccess)
      flushQueue(null, newAccess)
      originalRequest.headers.Authorization = `Bearer ${newAccess}`
      return api(originalRequest)
    } catch (refreshError) {
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      flushQueue(refreshError, null)
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)

export default api
