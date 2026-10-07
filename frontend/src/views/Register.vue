<template>
  <div class="auth-wrap">
    <div class="auth-brand">
      <div class="ab-in">
        <div class="ab-logo"><span>🪪</span> 证件管家</div>
        <h1>一次录入<br/>从此不忘任何一张证</h1>
        <ul class="ab-list">
          <li><span class="ab-ico">🗂️</span>身份证、驾驶证、护照、社保卡……统一管理</li>
          <li><span class="ab-ico">👨‍👩‍👦</span>为家里老人、孩子分别建档，各自提醒</li>
          <li><span class="ab-ico">🔐</span>证件号码加密存储，仅脱敏展示</li>
        </ul>
        <div class="ab-foot">注册即可使用全部功能</div>
      </div>
    </div>
    <div class="auth-panel">
      <div class="auth-card">
        <h2>创建账号</h2>
        <p class="muted small">只需用户名和密码，10 秒完成</p>
        <form @submit.prevent="submit">
          <label class="field"><span>用户名</span>
            <input v-model="username" maxlength="20" placeholder="2-20 位，字母/数字/中文" required>
          </label>
          <label class="field"><span>密码</span>
            <input v-model="password" type="password" maxlength="64" placeholder="至少 8 位" required>
          </label>
          <div v-if="err" class="notice danger">{{ err }}</div>
          <button class="primary" style="width:100%; padding:11px" :disabled="busy || password.length < 8">{{ busy ? '注册中…' : '注册并进入' }}</button>
        </form>
        <div class="mt center small muted">已有账号？<router-link to="/login">去登录</router-link></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { saveSession, fetchMe } from '../store/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const err = ref('')
const busy = ref(false)

async function submit() {
  if (password.value.length < 8) { err.value = '密码至少 8 位'; return }
  err.value = ''
  busy.value = true
  try {
    const data = await api.post('/auth/register', { username: username.value, password: password.value })
    saveSession(data.access_token, data.refresh_token)
    await fetchMe()
    router.push('/documents/new')
  } catch (e) {
    err.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.auth-wrap { min-height: 100vh; display: flex; }
.auth-brand {
  flex: 1.15; position: relative; overflow: hidden;
  background: linear-gradient(160deg, #232c52 0%, #1a2140 45%, #12172d 100%);
  display: flex; align-items: center; justify-content: center;
}
.auth-brand::before {
  content: ""; position: absolute; inset: -30%;
  background:
    radial-gradient(520px 380px at 18% 22%, rgba(91, 124, 250, .34), transparent 62%),
    radial-gradient(460px 360px at 82% 78%, rgba(124, 92, 240, .3), transparent 60%);
}
.ab-in { position: relative; max-width: 430px; padding: 48px 40px; color: #c7d0e8; }
.ab-logo {
  display: inline-flex; align-items: center; gap: 10px; color: #fff;
  font-weight: 700; font-size: 17px; letter-spacing: .5px; margin-bottom: 34px;
}
.ab-logo span {
  display: grid; place-items: center; width: 38px; height: 38px; border-radius: 12px;
  background: var(--grad); font-size: 19px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.25), 0 8px 18px -6px rgba(91,124,250,.6);
}
.ab-in h1 { color: #fff; font-size: 30px; line-height: 1.45; letter-spacing: -.5px; margin: 0 0 26px; font-weight: 700; }
.ab-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 14px; }
.ab-list li { display: flex; gap: 12px; align-items: flex-start; font-size: 14px; line-height: 1.65; }
.ab-ico { font-size: 17px; flex: 0 0 auto; margin-top: 1px; }
.ab-foot { margin-top: 40px; font-size: 12px; color: #6d7896; letter-spacing: .5px; }
.auth-panel { flex: 1; display: flex; align-items: center; justify-content: center; padding: 32px; }
.auth-card { width: 380px; max-width: 100%; padding: 38px 34px; border-radius: 20px; }
h2 { margin: 0 0 4px; font-size: 22px; letter-spacing: -.3px; }
@media (max-width: 860px) {
  .auth-wrap { flex-direction: column; }
  .auth-brand { min-height: 300px; }
  .ab-in { padding: 36px 26px; }
  .ab-in h1 { font-size: 24px; margin-bottom: 18px; }
  .ab-foot { margin-top: 24px; }
}
</style>
