<template>
  <div class="page narrow">
    <div class="page-head">
      <div><h1>{{ isEdit ? '编辑证件' : '添加证件' }}</h1>
        <p>{{ isEdit ? '调整信息与提醒档位' : '全部点选完成，几乎不用打字' }}</p></div>
    </div>

    <div class="card">
      <!-- ① 证件类型 -->
      <div class="sec">
        <div class="sec-title">① 证件类型（点一下自动带出信息）</div>
        <div class="type-grid">
          <button v-for="t in types" :key="t.id" type="button" class="type-tile"
                  :class="{on: form.document_type_id===t.id}" @click="pickType(t)">
            <span class="tt-ico">{{ t.icon }}</span>
            <span class="tt-name">{{ t.name }}</span>
            <span class="tt-sub">{{ t.valid_years ? `常见有效期 ${t.valid_years} 年` : (t.desc || ' ') }}</span>
          </button>
          <button type="button" class="type-tile" :class="{on: customType}" @click="pickCustom">
            <span class="tt-ico">✏️</span>
            <span class="tt-name">自定义</span>
            <span class="tt-sub">健身卡 / 培训卡 / 其他</span>
          </button>
        </div>
        <label v-if="customType" class="field mt"><span>证件 / 卡券名称 *</span>
          <input v-model="form.title" maxlength="80" placeholder="例如：健身房年卡" required>
        </label>
      </div>

      <!-- ② 有效期 -->
      <div class="sec">
        <div class="sec-title">② 有效期</div>
        <div class="seg">
          <button type="button" :class="{on: mode==='auto'}" @click="mode='auto'">🧮 签发日期 + 年限（自动算到期）</button>
          <button type="button" :class="{on: mode==='direct'}" @click="mode='direct'">📅 直接填到期日</button>
        </div>

        <template v-if="mode==='auto'">
          <label class="field" style="max-width:280px; margin-top:14px"><span>签发日期（证件上印着的日期）</span>
            <input v-model="start" type="date">
          </label>
          <div class="chips">
            <button v-for="y in yearOptions" :key="y" type="button" class="chip"
                    :class="{on: validYears===y}" @click="validYears=y">{{ y }} 年</button>
          </div>
          <div v-if="computedExpire" class="calc-result">
            <span>🧮</span><span>到期日期自动计算为 <b>{{ computedExpire }}</b>，无需手填</span>
          </div>
          <div v-else class="hint">选好「签发日期 + 年限」即可自动算出到期日。</div>
        </template>

        <template v-else>
          <label class="field" style="max-width:280px; margin-top:14px"><span>到期日期</span>
            <input v-model="dateOnly" type="date">
          </label>
        </template>
      </div>

      <!-- ③ 归属成员 -->
      <div class="sec" v-if="members.length">
        <div class="sec-title">③ 归属成员</div>
        <div class="chips">
          <button type="button" class="chip" :class="{on: !form.member_id}" @click="form.member_id=null">👤 我自己</button>
          <button v-for="m in members" :key="m.id" type="button" class="chip"
                  :class="{on: form.member_id===m.id}" @click="form.member_id=m.id">
            <span class="mdot" :style="{background:m.member_color}"></span>{{ m.member_name }}
          </button>
        </div>
      </div>

      <!-- ④ 提醒档位 -->
      <div class="sec">
        <div class="sec-title">④ 到期前提醒</div>
        <div class="chips">
          <button v-for="a in aheadOptions" :key="a" type="button" class="chip"
                  :class="{on: aheadSelected===a}" @click="toggleAhead(a)">{{ a }} 天前</button>
        </div>
        <div class="hint">只选一个档位：到达 {{ aheadSelected }} 天前起，每天会弹一次提醒，直到你处理完毕。</div>
      </div>

      <!-- 可选信息 -->
      <details class="optional">
        <summary>选填：证件号码（加密保存）/ 备注</summary>
        <div class="twin mt">
          <label class="field"><span>证件号码</span>
            <input v-model="form.doc_number" maxlength="64" placeholder="加密存储，仅脱敏展示">
          </label>
          <label class="field"><span>备注</span>
            <input v-model="form.note" maxlength="300" placeholder="例如：绑定的手机号、剩余余额">
          </label>
        </div>
      </details>

      <div v-if="err" class="notice danger">{{ err }}</div>

      <div class="row" style="justify-content:flex-end; margin-top:6px">
        <button type="button" class="ghost" @click="$router.back()">取消</button>
        <button type="button" class="primary" @click="save" :disabled="busy">
          {{ busy ? '保存中…' : (isEdit ? '保存修改' : '添加证件') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { toastOk } from '../store/toast'

const route = useRoute()
const router = useRouter()
const types = ref([])
const members = ref([])
const isEdit = computed(() => !!route.params.id)
const docId = computed(() => route.params.id)

const form = ref({ document_type_id: null, member_id: null, title: '', doc_number: '', note: '' })
const customType = ref(false)
const mode = ref('auto')
const start = ref('')
const validYears = ref(null)
const dateOnly = ref('')
const aheadSelected = ref(90)
const aheadOptions = [1, 7, 30, 60, 90, 180]
const err = ref('')
const busy = ref(false)

// 各证件类型的常见有效期（年），点选即可，无需手输
const YEAR_OPTIONS = {
  resident_id: [5, 10, 20],
  driving_license: [6, 10, 20],
  passport: [5, 10],
  hm_pass: [5],
  residence_permit: [1],
  social_insurance_card: [10],
  vehicle_inspection: [1, 2],
}
const FALLBACK_YEARS = [1, 2, 3, 5, 10, 20]

const pickedType = computed(() => types.value.find(t => t.id === form.value.document_type_id) || null)
const yearOptions = computed(() => {
  const t = pickedType.value
  if (!t) return FALLBACK_YEARS
  const opts = YEAR_OPTIONS[t.code]
  if (opts) return opts
  if (t.valid_years) return [t.valid_years]
  return FALLBACK_YEARS
})

const computedExpire = computed(() => {
  if (mode.value !== 'auto' || !start.value || !validYears.value) return ''
  const d = new Date(start.value)
  if (isNaN(d)) return ''
  d.setFullYear(d.getFullYear() + validYears.value)
  return d.toISOString().slice(0, 10)
})

function pickType(t) {
  customType.value = false
  form.value.document_type_id = t.id
  form.value.title = t.name
  aheadSelected.value = (t.default_ahead_days && t.default_ahead_days.length)
    ? Math.max(...t.default_ahead_days) : 90
  // 年限默认值：类型明确给了就用它，否则不预选（如身份证 5/10/20 视年龄而定）
  validYears.value = t.valid_years || null
}
function pickCustom() {
  customType.value = true
  form.value.document_type_id = null
  validYears.value = null
  aheadSelected.value = 30
}
function toggleAhead(a) {
  aheadSelected.value = a // 单选：再次点击仍是该项
}

async function save() {
  err.value = ''
  if (!form.value.title.trim() && !customType.value && !pickedType.value) {
    err.value = '请先选择证件类型，或选「自定义」填写名称'; return
  }
  if (customType.value && !form.value.title.trim()) { err.value = '请填写证件名称'; return }
  const expire_date = mode.value === 'auto' ? (computedExpire.value || null) : (dateOnly.value || null)
  if (!expire_date) {
    err.value = mode.value === 'auto' ? '请选好签发日期和年限，或切换为直接填到期日' : '请填写到期日期'
    return
  }
  const body = {
    document_type_id: form.value.document_type_id,
    member_id: form.value.member_id || null,
    title: (customType.value ? form.value.title : (form.value.title || pickedType.value?.name || '')).trim(),
    doc_number: form.value.doc_number.trim() || '',
    note: form.value.note.trim(),
    expire_date,
    start_date: mode.value === 'auto' ? (start.value || null) : null,
    valid_years: mode.value === 'auto' ? (validYears.value || null) : null,
  }
  busy.value = true
  try {
    let doc
    if (isEdit.value) {
      doc = await api.patch(`/documents/${docId.value}`, body)
    } else {
      doc = await api.post('/documents', body)
    }
    await api.put(`/documents/${doc.id}/rules`, [{ ahead_days: aheadSelected.value, enabled: true }])
    toastOk(isEdit.value ? '证件已更新' : '证件已添加')
    router.push('/documents')
  } catch (e) { err.value = e.message } finally { busy.value = false }
}

onMounted(async () => {
  types.value = await api.get('/document-types')
  try { members.value = await api.get('/family') } catch (e) {}
  if (isEdit.value) {
    const docs = await api.get('/documents')
    const d = docs.find(x => String(x.id) === String(docId.value))
    if (d) {
      form.value.title = d.title
      form.value.document_type_id = d.document_type_id
      form.value.member_id = d.member_id
      form.value.note = d.note
      if (d.start_date && d.valid_years) {
        mode.value = 'auto'
        start.value = d.start_date
        validYears.value = d.valid_years
      } else {
        mode.value = 'direct'
        dateOnly.value = d.expire_date
      }
      customType.value = !d.document_type_id
    }
    const rules = await api.get(`/documents/${docId.value}/rules`)
    const enabled = rules.filter(r => r.enabled).map(r => r.ahead_days)
    aheadSelected.value = enabled.length ? Math.max(...enabled) : 90
  }
})
</script>

<style scoped>
.twin { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width:640px){ .twin { grid-template-columns: 1fr; } }
</style>
