<template>
  <div class="page">
    <div class="page-head">
      <div><h1>我的证件</h1><p>卡片按到期日期从近到远排序，快到期总在最上面</p></div>
      <button class="primary" @click="$router.push('/documents/new')">＋ 添加证件</button>
    </div>

    <div class="row mb">
      <input v-model="q" class="grow" placeholder="搜索证件名 / 类型 / 归属成员…" style="max-width:340px">
      <select v-model="statusF" style="width:auto">
        <option value="">全部状态</option>
        <option value="VALID">正常</option>
        <option value="EXPIRING">临期</option>
        <option value="EXPIRED">已过期</option>
        <option value="ARCHIVED">已归档</option>
      </select>
    </div>

    <div v-if="filtered.length === 0" class="card empty">
      <div class="big">🗂️</div>
      <h3 v-if="docs.length===0">还没有证件</h3>
      <p v-if="docs.length===0">点选常用类型、自动算到期日，30 秒添加第一张。</p>
      <p v-else class="muted">没有符合筛选的结果</p>
      <button v-if="docs.length===0" class="primary mt" @click="$router.push('/documents/new')">＋ 添加证件</button>
    </div>

    <div class="grid-docs">
      <div v-for="d in filtered" :key="d.id" class="doc-card" :class="cardClass(d)">
        <span v-if="d.member_name" class="member-tag" :style="{background:d.member_color}">{{ d.member_name }}</span>
        <div class="top">
          <span class="big-icon" :class="'ic-'+chipClass(d)">{{ d.type_icon || '🪪' }}</span>
          <div class="ttl">
            <div class="name">{{ d.title }}</div>
            <span class="chip" :class="'chip-'+chipClass(d)"><i class="pdot"></i>{{ statusText(d.status) }}</span>
          </div>
        </div>

        <div class="days">
          <template v-if="d.status==='EXPIRED'"><b class="c-expired">已过期 {{ -d.days_left }} 天</b></template>
          <template v-else-if="d.status==='ARCHIVED'"><span class="muted">已归档</span></template>
          <template v-else>
            <div class="num-line">还有 <b :class="'c-'+numClass(d)">{{ d.days_left }}</b> 天</div>
            <div class="apx">{{ approx(d.days_left) }} · {{ d.expire_date }} 到期</div>
          </template>
        </div>

        <div class="bar-row">
          <div class="vbar" :class="barClass(d)"><i :style="{width: barWidth(d)}"></i></div>
          <span class="pct" :class="'c-'+numClass(d)">{{ barPct(d) }}</span>
        </div>

        <div class="meta">
          <span v-if="d.doc_number_masked" class="mnum">🪪 {{ d.doc_number_masked }}</span>
          <span v-else class="mnum miss" @click="$router.push({path:'/documents/'+d.id+'/edit'})">🪪 未填号码 <i class="cta">去完善 →</i></span>
          <span v-if="d.valid_years" class="mnum">⏳ 有效期 {{ d.valid_years }} 年</span>
        </div>

        <div class="actions">
          <a v-if="entryOf(d)" class="btn-portal" :href="entryOf(d).url" target="_blank" rel="noopener noreferrer">
            官方入口 <span class="arr">↗</span></a>
          <button class="ghost small" @click="goGuide(d)">📖 怎么办</button>
          <span style="flex:1"></span>
          <button class="ghost small" @click="$router.push({path:'/documents/'+d.id+'/edit'})">✏️ 编辑</button>
          <button v-if="d.status!=='ARCHIVED'" class="ghost small muted" @click="archive(d)">归档</button>
          <button class="ghost small danger" @click="remove(d)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { toastOk } from '../store/toast'
import { loadLinks, resolveEntry } from '../store/links'

const router = useRouter()
const docs = ref([])
const q = ref('')
const statusF = ref('')
loadLinks()

async function load() { docs.value = await api.get('/documents') }

const filtered = computed(() => {
  return docs.value.filter(d => {
    const hitQ = !q.value || (d.title + ' ' + d.type_name + ' ' + d.member_name).toLowerCase().includes(q.value.toLowerCase())
    const hitS = !statusF.value || d.status === statusF.value
    return hitQ && hitS
  })
})

function statusText(s) {
  return { VALID: '正常', EXPIRING: '临期', EXPIRED: '已过期', ARCHIVED: '已归档' }[s] || s
}
function chipClass(d) {
  return ({ VALID: 'valid', EXPIRING: 'expiring', EXPIRED: 'expired', ARCHIVED: 'archived' }[d.status] || 'valid')
}
function numClass(d) { return chipClass(d) }
function statusClass(d) {
  const m = d.days_left
  if (m <= 7) return 'expired'
  if (m <= 90) return 'expiring'
  return 'valid'
}
function approx(n) {
  if (!n || n <= 0) return ''
  const y = Math.floor(n / 365)
  const m = Math.round((n % 365) / 30)
  if (y > 0) return m > 0 ? `约${y}年${m}个月` : `约${y}年`
  return m > 0 ? `约${m}个月` : `约${n}天`
}
function barPct(d) {
  if (d.status === 'EXPIRED' || d.days_left <= 0) return '已到期'
  return Math.min(100, Math.max(5, Math.round((d.days_left / 180) * 100))) + '%'
}
function cardClass(d) {
  if (d.status === 'EXPIRED') return 'bad'
  if (d.status === 'EXPIRING') return 'warn'
  return ''
}
function barClass(d) {
  if (d.status === 'EXPIRED') return 'vbar-bad'
  if (d.days_left <= 30 || d.status === 'EXPIRING') return 'vbar-warn'
  return 'vbar-ok'
}
function barWidth(d) {
  if (d.status === 'EXPIRED' || d.days_left <= 0) return '100%'
  return Math.min(100, Math.max(5, (d.days_left / 180) * 100)) + '%'
}
function entryOf(d) { return d.document_type_id ? resolveEntry(d.document_type_id) : null }
async function archive(d) {
  if (!confirm('确定归档「' + d.title + '」？归档后不再参与到期提醒。')) return
  await api.post(`/documents/${d.id}/archive`)
  toastOk('已归档')
  load()
}
async function remove(d) {
  if (!confirm('确定彻底删除「' + d.title + '」？该操作不可恢复。')) return
  await api.del(`/documents/${d.id}`)
  toastOk('已删除')
  load()
}
function goGuide(d) {
  router.push({ path: '/guides', query: d.document_type_id ? { type: d.document_type_id } : {} })
}
onMounted(load)
</script>
