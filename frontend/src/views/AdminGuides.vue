<template>
  <div class="page narrow" style="max-width:900px">
    <div class="page-head">
      <div><h1>续办指南维护</h1><p>内容面向大众，请务必核对后填写；来源与更新日期必填</p></div>
      <button class="primary" @click="open()">＋ 新建指南</button>
    </div>

    <div v-if="list.length===0" class="card empty"><div class="big">🛠️</div><p>暂无指南，点击右上角新建。</p></div>

    <div class="alist">
      <div v-for="g in list" :key="g.id" class="rowitem">
        <div class="gi">{{ g.type_icon || '🪪' }}</div>
        <div class="grow">
          <div class="rt">
            <b>{{ g.title }}</b>
            <span class="tag tag-blue">{{ g.type_name }}</span>
            <span class="tag" :class="g.region_code ? 'tag-green' : 'tag-gray'">{{ g.region_name || '全国通用' }}</span>
            <span class="tag tag-gray">{{ modeName(g.link_mode) }}</span>
          </div>
          <div class="tiny muted" style="margin-top:5px">来源：{{ g.source }} · 更新于 {{ g.updated_at }}</div>
        </div>
        <a v-if="g.official_url" class="link-open" :href="normUrl(g.official_url)" target="_blank" rel="noopener">官方入口 ↗</a>
        <button class="ghost small" @click="open(g, true)">复制为本省版</button>
        <button class="ghost small" @click="open(g)">编辑</button>
        <button class="ghost small danger" @click="remove(g)">删除</button>
      </div>
    </div>

    <!-- 编辑/新建弹窗 -->
    <transition name="fade">
      <div v-if="editing" class="modal-mask" @click.self="editing=null">
        <div class="modal card">
          <h3 style="margin:0 0 6px">{{ editing.id ? '编辑指南' : '新建指南' }}</h3>
          <div class="tiny muted" v-if="editing.id">最后更新：{{ f.updated_at }}</div>

          <div class="sec" style="margin-top:16px">
            <div class="sec-title">基本信息</div>
            <div class="twin">
              <label class="field"><span>关联证件类型</span>
                <select v-model="f.document_type_id">
                  <option v-for="t in types" :key="t.id" :value="t.id">{{ t.icon }} {{ t.name }}</option>
                </select>
              </label>
              <label class="field"><span>标题</span><input v-model="f.title" placeholder="例如：居民身份证到期换领"></label>
            </div>
            <div class="twin">
              <label class="field"><span>适用范围</span>
                <select v-model="f.region_code">
                  <option value="">全国通用</option>
                  <option v-for="p in provinces" :key="p.code" :value="p.code">仅 {{ p.name }}</option>
                </select>
              </label>
              <label class="field"><span>官方入口如何生成</span>
                <select v-model="f.link_mode">
                  <option value="FIXED">固定链接（全国统一打开同一地址）</option>
                  <option value="PROVINCE_PORTAL">按省份 → 本省政务服务网</option>
                  <option value="PROVINCE_JTW">按省份 → 本省交管12123平台</option>
                </select>
              </label>
            </div>
            <label class="field"><span>材料清单（每行一条）</span>
              <textarea rows="3" v-model="materialsText" placeholder="原居民身份证原件&#10;居民户口簿"></textarea>
            </label>
            <label class="field"><span>办理地点</span><input v-model="f.location" placeholder="去哪办"></label>
          </div>

          <div class="sec">
            <div class="sec-title">办理信息</div>
            <div class="twin">
              <label class="field"><span>费用</span><input v-model="f.fee" placeholder="例如：换领 20 元/证"></label>
              <label class="field"><span>办结时限</span><input v-model="f.duration" placeholder="例如：7-15 个工作日"></label>
            </div>
            <label class="field"><span>官方入口 URL <template v-if="f.link_mode==='FIXED'">（用户直接打开）</template><template v-else>（未设置省份 / 本省链接未收录时的回退地址）</template></span>
              <div class="urlrow">
                <input v-model="f.official_url" placeholder="https://……" style="flex:1">
                <a v-if="f.official_url" class="link-open" :href="normUrl(f.official_url)"
                   target="_blank" rel="noopener noreferrer">打开 ↗</a>
              </div>
            </label>
            <div v-if="f.link_mode!=='FIXED' && sampleEntry" class="calc-result">
              <span>👁️</span>
              <span>示例（广东用户点击将打开）：<b class="sample-url">{{ sampleEntry }}</b></span>
            </div>
          </div>

          <div class="sec" style="margin-bottom:4px">
            <div class="sec-title">来源核实</div>
            <div class="twin">
              <label class="field"><span>来源 *</span><input v-model="f.source" placeholder="例如：广东省政务服务网办事指南"></label>
              <label class="field"><span>更新日期</span><input v-model="f.updated_at" type="date"></label>
            </div>
            <label class="field" style="margin-bottom:8px"><span>免责提示（展示给用户）</span>
              <input v-model="f.disclaimer"></label>
          </div>

          <div v-if="err" class="notice danger">{{ err }}</div>
          <div class="row" style="justify-content:flex-end">
            <button class="ghost" @click="editing=null">取消</button>
            <button class="primary" @click="save">保存指南</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { toastOk, toastErr } from '../store/toast'
import { region, loadLinks } from '../store/links'

const list = ref([])
const types = ref([])
const editing = ref(null)
const f = ref({})
const materialsText = ref('')
const err = ref('')
const provinces = computed(() => region.provinces)

const todayStr = () => new Date().toISOString().slice(0, 10)
function normUrl(u) { return /^https?:\/\//i.test(u) ? u : 'https://' + u }
function modeName(m) {
  return { FIXED: '固定链接', PROVINCE_PORTAL: '按省→政务网', PROVINCE_JTW: '按省→交管12123' }[m] || m
}

// 以广东为示例，实时预览按省份生成的链接
const sampleEntry = computed(() => {
  const gd = region.provinces.find(p => p.code === 'GD')
  if (!gd) return ''
  if (f.value.link_mode === 'PROVINCE_JTW') return `https://${gd.jtw_code}.122.gov.cn/`
  if (f.value.link_mode === 'PROVINCE_PORTAL') return gd.portal_url || '（该省链接待收录，回退全国平台）'
  return ''
})

function open(g, duplicate = false) {
  if (g) {
    f.value = { ...g }
    if (duplicate) { f.value.id = null; f.value.region_code = '' }
    materialsText.value = (g.materials || []).join('\n')
    editing.value = duplicate ? { id: null } : g
  } else {
    editing.value = { id: null }
    f.value = { document_type_id: types.value[0]?.id, title: '', region_code: '', link_mode: 'FIXED',
      location: '', fee: '', duration: '', official_url: '', source: '',
      updated_at: todayStr(), disclaimer: '以当地窗口实际要求为准，办理前请核实最新政策。' }
    materialsText.value = ''
  }
  err.value = ''
}

async function save() {
  err.value = ''
  if (!f.value.title.trim()) { err.value = '请填写标题'; return }
  if (!f.value.source.trim()) { err.value = '来源必填，用于说明信息可靠性'; return }
  const body = {
    document_type_id: f.value.document_type_id,
    title: f.value.title.trim(),
    region_code: f.value.region_code || null,
    link_mode: f.value.link_mode,
    materials: materialsText.value.split('\n').map(s => s.trim()).filter(Boolean),
    location: f.value.location,
    fee: f.value.fee,
    duration: f.value.duration,
    official_url: (f.value.official_url || '').trim(),
    source: f.value.source.trim(),
    updated_at: f.value.updated_at || todayStr(),
    disclaimer: f.value.disclaimer,
  }
  try {
    if (editing.value.id) await api.put(`/guides/${editing.value.id}`, body)
    else await api.post('/guides', body)
    toastOk(editing.value.id ? '指南已更新' : '指南已创建')
    editing.value = null
    await loadLinks()
    load()
  } catch (e) { toastErr(e.message) }
}
async function remove(g) {
  if (!confirm('删除指南「' + g.title + '」？此操作会同步影响用户端展示。')) return
  try { await api.del(`/guides/${g.id}`); toastOk('已删除'); await loadLinks(); load() } catch (e) { toastErr(e.message) }
}
async function load() {
  const [g, t] = await Promise.all([api.get('/guides'), api.get('/document-types')])
  list.value = g
  types.value = t
}
onMounted(load)
</script>

<style scoped>
.alist { display: grid; gap: 11px; }
.rowitem {
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--r-md);
  box-shadow: var(--shadow-s); padding: 14px 16px;
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}
.gi { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 12px; background: var(--brand-soft); font-size: 21px; }
.rt { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.modal-mask { position: fixed; inset: 0; background: rgba(13, 18, 33, .48); display: flex; align-items: center; justify-content: center; z-index: 60; padding: 20px; backdrop-filter: blur(3px); }
.modal { width: 640px; max-height: 92vh; overflow: auto; padding: 26px; }
.twin { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.urlrow { display: flex; gap: 8px; align-items: center; }
.sample-url { font-family: ui-monospace, Consolas, monospace; font-size: 12.5px; word-break: break-all; }
button.small, .link-open { font-size: 13px; }
.fade-enter-active,.fade-leave-active{transition:opacity .15s}
.fade-enter-from,.fade-leave-to{opacity:0}
@media (max-width:640px){ .twin{grid-template-columns:1fr} }
</style>
