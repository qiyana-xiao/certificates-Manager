<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>你好，{{ auth.user?.username || '朋友' }}</h1>
        <p v-if="stats">{{ todayLabel }} · 未来 30 天内 {{ stats.next30 }} 项到期<span v-if="stats.expired">，{{ stats.expired }} 项已过期</span></p>
      </div>
      <button class="primary" @click="$router.push('/documents/new')">＋ 添加证件</button>
    </div>

    <div class="stat-grid" v-if="stats">
      <button class="card stat" :class="{on: filter==='active'}" type="button" @click="toggleFilter('active')">
        <span class="icon-tile s44">🗂️</span>
        <span class="s-mid"><span class="num c-slate">{{ stats.total_active }}</span><span class="lbl">在管证件</span></span>
        <span class="chev" aria-hidden="true">{{ filter==='active' ? '×' : '▾' }}</span>
      </button>
      <button class="card stat" :class="{on: filter==='next30'}" type="button" @click="toggleFilter('next30')">
        <span class="icon-tile s44 t-amber">⏳</span>
        <span class="s-mid"><span class="num c-amber">{{ stats.next30 }}</span><span class="lbl">未来 30 天到期</span></span>
        <span class="chev" aria-hidden="true">{{ filter==='next30' ? '×' : '▾' }}</span>
      </button>
      <button class="card stat" :class="{on: filter==='today'}" type="button" @click="toggleFilter('today')">
        <span class="icon-tile s44 t-amber">⏰</span>
        <span class="s-mid"><span class="num c-amber">{{ stats.due_today }}</span><span class="lbl">今天到期</span></span>
        <span class="chev" aria-hidden="true">{{ filter==='today' ? '×' : '▾' }}</span>
      </button>
      <button class="card stat" :class="{on: filter==='expired'}" type="button" @click="toggleFilter('expired')">
        <span class="icon-tile s44 t-red">⚠️</span>
        <span class="s-mid"><span class="num c-red">{{ stats.expired }}</span><span class="lbl">已过期</span></span>
        <span class="chev" aria-hidden="true">{{ filter==='expired' ? '×' : '▾' }}</span>
      </button>
      <p class="stat-hint">▸ 点上方卡片可切换下面显示哪类证件，再点一次恢复显示全部</p>
    </div>

    <div v-if="docs.length === 0" class="card empty">
      <div class="big">🪪</div>
      <h3>还没有证件档案</h3>
      <p>把会过期的证、卡录进来，到期前我会提前提醒你。</p>
      <button class="primary mt" @click="$router.push('/documents/new')">添加第一张证件（30 秒）</button>
    </div>

    <template v-else>
      <div class="sec-title stat-title mt" style="margin-bottom:14px">
        <span>{{ viewLabel }}<i class="count">{{ filteredDocs.length }}</i></span>
        <button v-if="filter!=='all'" class="clear-f" type="button" @click="filter='all'">× 显示全部</button>
      </div>

      <div v-if="filteredDocs.length === 0" class="card empty small">
        <div class="big">🔍</div>
        <h3>这个分类下暂时没有证件</h3>
        <p>换个分类看看，或点右上角「显示全部」查看所有证件。</p>
      </div>

      <div v-else class="grid-docs">
        <div v-for="d in filteredDocs" :key="d.id" class="doc-card" :class="cardClass(d)">
          <span v-if="d.member_name" class="member-tag" :style="{background:d.member_color}">{{ d.member_name }}</span>
          <div class="top">
            <span class="big-icon">{{ d.type_icon || '🪪' }}</span>
            <div>
              <div class="name">{{ d.title }}</div>
              <div class="type"><span class="dot" :class="d.status"></span>{{ statusText(d.status) }} · {{ d.type_name || '自定义' }}</div>
            </div>
          </div>
          <div class="days">
            <template v-if="d.status==='EXPIRED'"><b class="status-expired">已过期 {{ -d.days_left }} 天</b></template>
            <template v-else-if="d.status==='ARCHIVED'"><span class="muted">已归档</span></template>
            <template v-else>还有 <b :class="'status-'+statusClass(d)">{{ d.days_left }}</b> 天 · {{ d.expire_date }}</template>
          </div>
          <div class="vbar" :class="barClass(d)"><i :style="{width: barWidth(d)}"></i></div>
          <div class="actions">
            <a v-if="entryOf(d)" class="link-open" :href="entryOf(d).url" target="_blank" rel="noopener noreferrer">
              官方入口 <span class="arr">↗</span></a>
            <span class="spacer" style="flex:1"></span>
            <button class="outline small" @click="goGuide(d)">📖 怎么办</button>
            <button class="ghost small" @click="$router.push({path:'/documents/'+d.id+'/edit'})">编辑</button>
          </div>
        </div>
      </div>
    </template>

    <div class="notice info mt" v-if="docs.length>0">提示：提醒提前天数可在「我的证件 → 编辑」里调整。</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { auth } from '../store/auth'
import { loadLinks, resolveEntry } from '../store/links'

const router = useRouter()
const docs = ref([])
const stats = ref(null)
const filter = ref('all')
loadLinks()

const VIEWS = {
  all: '全部证件', active: '在管证件', next30: '未来 30 天到期',
  today: '今天到期', expired: '已过期',
}
const viewLabel = computed(() => VIEWS[filter.value] || '全部证件')

// 与后端 /api/dashboard 的统计口径保持一致
function isActive(d) { return d.status !== 'ARCHIVED' }
const filteredDocs = computed(() =>
  docs.value.filter((d) => {
    switch (filter.value) {
      case 'active': return isActive(d)
      case 'next30': return isActive(d) && d.days_left >= 0 && d.days_left <= 30
      case 'today': return isActive(d) && d.days_left === 0
      case 'expired': return d.status === 'EXPIRED'
      default: return true
    }
  }),
)
function toggleFilter(k) { filter.value = filter.value === k ? 'all' : k }

const todayLabel = computed(() => {
  const w = ['日', '一', '二', '三', '四', '五', '六'][new Date().getDay()]
  return `今天是 ${new Date().toLocaleDateString('zh-CN')} 星期${w}`
})

async function load() {
  try {
    const [d, s] = await Promise.all([api.get('/documents'), api.get('/dashboard')])
    docs.value = d
    stats.value = s
  } catch (e) {}
}

function statusText(s) {
  return { VALID: '正常', EXPIRING: '临期', EXPIRED: '已过期', ARCHIVED: '已归档' }[s] || s
}
function statusClass(d) {
  const m = d.days_left
  if (m <= 7) return 'expired'
  if (m <= 90) return 'expiring'
  return 'valid'
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
  const p = Math.min(100, Math.max(5, (d.days_left / 180) * 100))
  return p + '%'
}
function entryOf(d) { return d.document_type_id ? resolveEntry(d.document_type_id) : null }
function goGuide(d) {
  router.push({ path: '/guides', query: d.document_type_id ? { type: d.document_type_id } : {} })
}

onMounted(load)
</script>
