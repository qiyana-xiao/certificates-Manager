<template>
  <div class="page narrow">
    <div class="page-head"><div><h1>设置</h1><p>账号、省份与数据管理</p></div></div>

    <div class="card mb setting-row">
      <div class="icon-tile s46">📍</div>
      <div class="grow">
        <div class="st">我所在的省份</div>
        <p class="sd">
          <template v-if="myProv">已选择 <b>{{ myProv.name }}</b>，续办指南与官方入口将按本省直达。
            <template v-if="myProv.portal_url">
              本省平台：<a :href="myProv.portal_url" target="_blank" rel="noopener noreferrer">{{ myProv.portal_name }} ↗</a>
            </template>
            <template v-else>该省专属直达链接待收录，将回退到国家政务服务平台。</template>
          </template>
          <template v-else>选择省份后，身份证、驾驶证等业务的官方入口将直达本省政务/交管平台。</template>
        </p>
      </div>
      <RegionPicker :provinces="region.provinces" v-model="provSel" @change="saveProv" />
    </div>

    <div class="card mb setting-row">
      <div class="icon-tile s46 t-slate">👤</div>
      <div class="grow">
        <div class="st">账号</div>
        <p class="sd">用户名：<b>{{ auth.user?.username }}</b> · 角色：<b>{{ auth.user?.role === 'admin' ? '管理员' : '普通用户' }}</b></p>
      </div>
      <button class="ghost danger" @click="logout">退出登录</button>
    </div>

    <div class="card mb setting-row">
      <div class="icon-tile s46 t-green">📦</div>
      <div class="grow">
        <div class="st">数据备份 / 导出</div>
        <p class="sd">导出全部证件为 CSV（号码自动脱敏），可离线保存或迁移。</p>
      </div>
      <button class="outline" @click="doExport" :disabled="busy">{{ busy ? '导出中…' : '导出 CSV' }}</button>
    </div>

    <div class="card setting-row">
      <div class="icon-tile s46 t-amber">💡</div>
      <div class="grow">
        <div class="st">关于证件管家</div>
        <p class="sd">大众证件/卡券到期提醒工具。续办指南来自公开的政务办事指南，仅供参考，办理以当地窗口实际要求为准。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { exportCsv } from '../api'
import { auth, clearSession } from '../store/auth'
import { region, loadLinks, myProvince, setMyProvince } from '../store/links'
import RegionPicker from '../components/RegionPicker.vue'
import { toastOk } from '../store/toast'

const router = useRouter()
const busy = ref(false)
loadLinks()

const myProv = computed(() => myProvince())
const provSel = ref('')
watch(() => auth.user?.province_code, v => { provSel.value = v || '' }, { immediate: true })

async function saveProv() {
  try {
    await setMyProvince(provSel.value || null)
    toastOk(provSel.value ? '已保存，官方入口将按本省直达' : '已清除省份设置')
  } catch (e) { /* 下次重试 */ }
}
async function doExport() {
  busy.value = true
  try { await exportCsv() } catch (e) { alert(e.message) } finally { busy.value = false }
}
function logout() { clearSession(); router.push('/login') }
</script>

<style scoped>
.setting-row { display: flex; align-items: center; gap: 15px; padding: 18px 20px; flex-wrap: wrap; }
.st { font-weight: 650; font-size: 14.5px; }
.sd { margin: 5px 0 0; font-size: 13px; color: var(--muted); line-height: 1.7; }
.sd b { color: var(--text); }
.prov-select { width: auto; min-width: 140px; font-weight: 500; }
</style>
