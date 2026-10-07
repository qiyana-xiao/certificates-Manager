import { reactive } from 'vue'
import { api } from '../api'
import { auth } from './auth'

// 全国统一入口（各省未收录专属链接时的回退）
export const NATIONAL_PORTAL = {
  name: '国家政务服务平台',
  url: 'https://gjzwfw.www.gov.cn/',
}

export const region = reactive({
  provinces: [],
  guides: [],
  loaded: false,
})

export async function loadLinks() {
  if (region.loaded) return
  try {
    const [p, g] = await Promise.all([api.get('/provinces'), api.get('/guides')])
    region.provinces = p
    region.guides = g
    region.loaded = true
  } catch (e) { /* 静默失败：相关页面自行降级 */ }
}

export function provinceByCode(code) {
  return region.provinces.find(p => p.code === code) || null
}

export function myProvince() {
  return provinceByCode(auth.user?.province_code)
}

// 最佳指南：本省版优先，其次全国版
export function bestGuide(typeId) {
  if (!typeId) return null
  const pc = auth.user?.province_code
  const mine = region.guides.find(g => g.document_type_id === typeId && g.region_code === pc)
  const national = region.guides.find(g => g.document_type_id === typeId && !g.region_code)
  return mine || national || null
}

// 官方入口一键直达：按指南的 link_mode + 用户省份解析出真实链接
export function resolveEntry(typeId) {
  const g = bestGuide(typeId)
  if (!g) return null
  const prov = myProvince()

  // 本省专属指南：链接本身就是该省入口
  if (g.region_code) {
    return g.official_url
      ? { url: g.official_url, label: `${g.region_name}官方入口`, note: '本省版指南' }
      : null
  }
  if (g.link_mode === 'PROVINCE_JTW') {
    if (prov?.jtw_code) {
      return { url: `https://${prov.jtw_code}.122.gov.cn/`, label: `${prov.name}交管12123平台`, note: '本省平台直达，按当前所选省份打开' }
    }
    return g.official_url
      ? { url: g.official_url, label: '交管12123平台', note: '设置省份后可直达本省平台' }
      : null
  }
  if (g.link_mode === 'PROVINCE_PORTAL') {
    if (prov?.portal_url) {
      return { url: prov.portal_url, label: prov.portal_name || `${prov.name}政务服务网`, note: '本省政务网 · 内含各地/市分厅入口' }
    }
    if (prov) {
      return g.official_url
        ? { url: g.official_url, label: NATIONAL_PORTAL.name, note: `${prov.name}专属链接待收录，已打开全国平台` }
        : null
    }
    return g.official_url
      ? { url: g.official_url, label: NATIONAL_PORTAL.name, note: '设置省份后直达本省平台' }
      : null
  }
  return g.official_url ? { url: g.official_url, label: '官方办理入口', note: '全国统一入口' } : null
}

export async function setMyProvince(code) {
  const u = await api.put('/auth/me', { province_code: code || null })
  auth.user = { ...auth.user, ...u }
}
