import { reactive } from 'vue'
import { api, getToken, setToken, clearToken } from '../api'

export const auth = reactive({
  token: getToken(),
  user: null,
})

export async function fetchMe() {
  if (!auth.token) return
  try {
    auth.user = await api.get('/auth/me')
  } catch (e) {
    auth.user = null
  }
}

export function saveSession(access, refresh) {
  setToken(access)
  auth.token = access
  localStorage.setItem('doc_refresh', refresh || '')
}

export function clearSession() {
  clearToken()
  auth.token = ''
  auth.user = null
  localStorage.removeItem('doc_refresh')
}

export function isAdmin() {
  return auth.user && auth.user.role === 'admin'
}