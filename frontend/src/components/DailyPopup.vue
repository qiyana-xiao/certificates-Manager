<template>
  <div v-if="showing" class="pop-mask" @click.self="snooze">
    <div class="pop">
      <div class="pop-ico">🔔</div>
      <div class="pop-title">到期提醒</div>
      <div class="pop-doc">
        <span class="pop-badge">{{ showing.type_name || '证件' }}</span>
        <b>{{ showing.document_title }}</b>
      </div>
      <p class="pop-msg">{{ showing.content }}</p>
      <p class="pop-sub">
        <template v-if="showing.doc_status === 'EXPIRED'">已过期 {{ -showing.days_left }} 天</template>
        <template v-else>还有 {{ showing.days_left }} 天到期</template>
        · 今日提醒（每天 1 次）
      </p>
      <div class="pop-actions">
        <button class="primary small" @click="goHandle">去处理</button>
        <button class="ghost small" @click="snooze">知道了，明天再提醒</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { api, getToken } from '../api'

const router = useRouter()
const queue = ref([])
const showing = ref(null)
const done = new Set() // 本次会话已处理过的通知 id，防止重复弹
let timer = null
let active = false

async function poll() {
  if (!active || !getToken()) return
  try {
    const items = await api.get('/reminders/daily')
    for (const it of items) {
      if (!done.has(it.id)) queue.value.push(it)
    }
    // 只保留尚未展示的
    queue.value = queue.value.filter(q => !done.has(q.id))
    if (!showing.value && queue.value.length) {
      showing.value = queue.value.shift()
      done.add(showing.value.id)
    }
  } catch (e) { /* 静默：断网/未登录时忽略 */ }
}

async function dismiss(id) {
  try { await api.post(`/reminders/daily/${id}/dismiss`) } catch (e) {}
}

function next() {
  showing.value = null
  if (queue.value.length) {
    showing.value = queue.value.shift()
    done.add(showing.value.id)
  }
}

async function goHandle() {
  if (showing.value) dismiss(showing.value.id)
  next()
  router.push('/reminders')
}

async function snooze() {
  if (showing.value) dismiss(showing.value.id)
  next()
}

onMounted(() => {
  active = true
  setTimeout(poll, 400) // 进入页面稍候再查，避免抢在高亮前
  timer = setInterval(poll, 60000)
})
onBeforeUnmount(() => { active = false; clearInterval(timer) })
</script>

<style scoped>
.pop-mask {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(17, 23, 46, .45);
  backdrop-filter: blur(3px); -webkit-backdrop-filter: blur(3px);
  display: grid; place-items: center; padding: 20px;
}
.pop {
  width: min(420px, 94vw); background: #fff; border-radius: 20px;
  padding: 24px 26px; box-shadow: 0 24px 60px -20px rgba(15, 20, 40, .5);
  animation: popup .22s ease;
  text-align: center;
}
.pop-ico { font-size: 38px; }
.pop-title { font-size: 18px; font-weight: 700; color: var(--text); margin-top: 8px; }
.pop-doc { margin-top: 12px; display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap; }
.pop-badge {
  background: var(--brand-soft); color: var(--brand-dark);
  font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px;
}
.pop-msg { margin: 12px auto 4px; color: var(--text-2); font-size: 14px; line-height: 1.62; }
.pop-sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
.pop-actions { margin-top: 18px; display: flex; gap: 10px; justify-content: center; }
@keyframes popup { from { opacity: 0; transform: translateY(10px) scale(.97); } to { opacity: 1; transform: none; } }
</style>