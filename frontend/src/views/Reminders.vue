<template>
  <div class="page narrow" style="max-width:840px">
    <div class="page-head">
      <div><h1>提醒中心</h1><p>到点生成的提醒都在这里，处理后可清账</p></div>
    </div>

    <div v-if="list.length === 0" class="card empty">
      <div class="big">🔔</div>
      <h3>暂时没有提醒</h3>
      <p>给证件设置好提前天数，到点会自动出现。</p>
    </div>

    <div v-for="r in list" :key="r.id" class="card rem" :class="{pending: r.status==='PENDING'}">
      <div class="l">
        <span class="big-icon">{{ r.type_icon || '🪪' }}</span>
        <div class="info">
          <div class="t">{{ r.doc_title }}</div>
          <div class="m muted small">
            提前 {{ r.ahead_days }} 天提醒 · 到期 {{ r.expire_date }}
            <span :class="r.days_left >= 0 ? 'status-expiring' : 'status-expired'">
              （{{ r.days_left >= 0 ? '还有 ' + r.days_left + ' 天' : '已过期 ' + (-r.days_left) + ' 天' }}）
            </span>
          </div>
        </div>
      </div>
      <div class="r">
        <template v-if="r.status==='PENDING'">
          <button class="primary small" @click="renew(r)">已办新证</button>
          <button class="ghost small" @click="$router.push('/guides')">看怎么办</button>
          <button class="ghost small" @click="dismiss(r)">忽略</button>
        </template>
        <span v-else class="tag tag-gray">已处理</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const list = ref([])

async function load() { list.value = await api.get('/reminders') }
async function dismiss(r) {
  await api.post(`/reminders/${r.id}/dismiss`)
  load()
}
function renew(r) {
  // 新证引导：原证自动归档由后端 renew 完成；此处跳转添加新证
  router.push('/documents/new')
}
onMounted(load)
</script>

<style scoped>
.rem {
  display: flex; align-items: center; justify-content: space-between; gap: 14px;
  margin-bottom: 11px; padding: 15px 18px; flex-wrap: wrap;
}
.rem.pending { border-left: 3px solid var(--brand); }
.rem .l { display: flex; gap: 13px; align-items: center; }
.rem .big-icon { font-size: 28px; }
.rem .info .t { font-weight: 650; font-size: 14.5px; }
.rem .info .m { margin-top: 3px; }
.rem .r { display: flex; gap: 8px; align-items: center; }
</style>
