const BASE = '/api'

export function getToken() {
  return localStorage.getItem('doc_token') || ''
}

export function setToken(t) {
  localStorage.setItem('doc_token', t)
}

export function clearToken() {
  localStorage.removeItem('doc_token')
}

async function request(method, path, body) {
  const headers = { 'Content-Type': 'application/json' }
  const t = getToken()
  if (t) headers.Authorization = 'Bearer ' + t
  let res
  try {
    res = await fetch(BASE + path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (e) {
    throw new Error('无法连接服务器，请确认后端已启动')
  }
  if (res.status === 401) {
    clearToken()
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    throw new Error('登录已过期，请重新登录')
  }
  const text = await res.text()
  let data = null
  try { data = JSON.parse(text) } catch (e) { data = text }
  if (!res.ok) throw new Error((data && data.detail) || `请求失败(${res.status})`)
  return data
}

export const api = {
  get: (p) => request('GET', p),
  post: (p, b) => request('POST', p, b),
  put: (p, b) => request('PUT', p, b),
  patch: (p, b) => request('PATCH', p, b),
  del: (p) => request('DELETE', p),
}

export async function exportCsv() {
  const headers = { 'Content-Type': 'application/json' }
  const t = getToken()
  if (t) headers.Authorization = 'Bearer ' + t
  const res = await fetch(BASE + '/export', { method: 'POST', headers })
  if (!res.ok) throw new Error('导出失败')
  const blob = await res.blob()
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `doc-keeper-${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  link.remove()
}