<template>
  <div class="shell">
    <aside class="side">
      <div class="brand">
        <span class="logo">🪪</span>
        <div class="bt">
          <div class="t">证件管家</div>
          <div class="s">到期提醒 · 续办直达</div>
        </div>
      </div>
      <nav>
        <div class="group">概览</div>
        <router-link to="/" exact-active-class="on" class="nav"><span class="ico">🏠</span> 首页仪表盘</router-link>
        <div class="group">管理</div>
        <router-link to="/documents" active-class="on" class="nav"><span class="ico">🗂️</span> 我的证件</router-link>
        <router-link to="/calendar" active-class="on" class="nav"><span class="ico">📅</span> 到期日历</router-link>
        <router-link to="/reminders" active-class="on" class="nav"><span class="ico">🔔</span> 提醒中心
          <span v-if="unread" class="unread">{{ unread }}</span></router-link>
        <router-link to="/family" active-class="on" class="nav"><span class="ico">👨‍👩‍👦</span> 家庭提醒</router-link>
        <div class="group">帮助</div>
        <router-link to="/guides" active-class="on" class="nav"><span class="ico">📖</span> 续办指南</router-link>
        <router-link v-if="isAdmin()" to="/admin/guides" active-class="on" class="nav"><span class="ico">🛠️</span> 指南维护</router-link>
        <router-link to="/settings" active-class="on" class="nav"><span class="ico">⚙️</span> 设置</router-link>
      </nav>
      <div class="user">
        <div class="uavatar">{{ (auth.user?.username || '?')[0] }}</div>
        <div class="uname">
          <div class="t">{{ auth.user?.username || '朋友' }}</div>
          <div class="s">{{ auth.user?.role === 'admin' ? '管理员' : (myProvince()?.name || '未设置省份') }}</div>
        </div>
        <button class="logout" title="退出登录" @click="doLogout">⏻</button>
      </div>
    </aside>
    <main class="main">
      <div class="topbar">
        <span class="crumb">证件管家</span><span class="sep">/</span><span class="cur">{{ title }}</span>
      </div>
      <router-view class="page-enter" @refresh-unread="loadUnread" />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { clearSession, isAdmin, auth } from '../store/auth'
import { loadLinks, myProvince } from '../store/links'

const route = useRoute()
const router = useRouter()
const unread = ref(0)
const title = computed(() => route.meta.title || '证件管家')

async function loadUnread() {
  try {
    const rem = await api.get('/reminders')
    unread.value = rem.filter(r => r.status === 'PENDING').length
  } catch (e) { unread.value = 0 }
}
function doLogout() {
  clearSession(); router.push('/login')
}
let timer = null
onMounted(() => { loadUnread(); loadLinks(); timer = setInterval(loadUnread, 60000) })
onBeforeUnmount(() => clearInterval(timer))
</script>

<style scoped>
.shell { display: flex; min-height: 100vh; }
.side {
  width: 236px; flex: 0 0 236px;
  background: linear-gradient(180deg, #1a2340 0%, #11172e 100%);
  color: #b9c3d9; display: flex; flex-direction: column;
  position: sticky; top: 0; height: 100vh;
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, .035), 1px 0 30px -18px rgba(15, 20, 40, .55);
  z-index: 10;
}
.brand { display: flex; align-items: center; gap: 11px; padding: 22px 20px 18px; }
.logo {
  display: grid; place-items: center; width: 38px; height: 38px; border-radius: 12px;
  background: var(--grad); font-size: 19px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.25), 0 6px 14px -4px rgba(91,124,250,.5);
}
.bt .t { color: #fff; font-weight: 700; font-size: 16px; letter-spacing: .5px; }
.bt .s { color: #6d7896; font-size: 10.5px; margin-top: 1px; letter-spacing: .5px; }
nav { flex: 1; padding: 2px 12px 12px; overflow-y: auto; }
nav::-webkit-scrollbar-thumb { border: 2px solid #10162b; background: #2a3352; }
.group { font-size: 10.5px; color: #5d6883; margin: 16px 12px 6px; letter-spacing: 2px; }
.nav {
  display: flex; align-items: center; gap: 11px; color: #aab5cf;
  padding: 9px 12px; border-radius: 11px; margin-bottom: 2px; font-size: 13.5px;
  transition: all .16s ease; position: relative;
}
.nav:hover { background: rgba(255,255,255,.06); color: #fff; }
.nav.on {
  background: var(--grad); color: #fff; font-weight: 600;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.2), 0 8px 16px -6px rgba(91,124,250,.55);
}
.ico { width: 18px; text-align: center; font-size: 15px; }
.unread {
  margin-left: auto; background: #ef4444; color: #fff; border-radius: 999px;
  font-size: 10.5px; padding: 1px 7px; min-width: 18px; text-align: center; font-weight: 600;
}
.user {
  margin: 10px 14px 16px; padding: 12px; border-radius: 14px;
  background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.07);
  display: flex; align-items: center; gap: 10px;
}
.uavatar {
  width: 36px; height: 36px; border-radius: 11px; background: var(--grad);
  color: #fff; display: grid; place-items: center; font-weight: 700; flex: 0 0 auto;
}
.uname { flex: 1; min-width: 0; }
.uname .t { color: #fff; font-size: 13px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.uname .s { color: #7d89a8; font-size: 11px; margin-top: 1px; }
.logout { background: transparent; border: 0; color: #7d89a8; font-size: 16px; padding: 6px; border-radius: 9px; }
.logout:hover { color: #fff; background: rgba(255,255,255,.1); }
.main {
  flex: 1; min-width: 0;
  /* 由深色侧栏向浅色内容自然过渡：左侧一道渐变淡入 */
  background: linear-gradient(90deg, rgba(17, 23, 46, .035) 0%, rgba(17, 23, 46, 0) 52px), transparent;
}
.topbar {
  position: sticky; top: 0; z-index: 20;
  display: flex; align-items: center; gap: 9px;
  padding: 16px 38px;
  font-size: 12.5px; color: var(--muted);
  background: linear-gradient(180deg, rgba(248, 250, 253, .9), rgba(248, 250, 253, .72));
  backdrop-filter: blur(12px) saturate(1.2); -webkit-backdrop-filter: blur(12px) saturate(1.2);
  border-bottom: 1px solid rgba(230, 234, 242, .75);
}
.topbar .sep { color: #c6cddc; }
.topbar .cur { color: var(--text); font-weight: 600; }
</style>
