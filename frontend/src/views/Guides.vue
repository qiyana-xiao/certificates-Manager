<template>
  <div class="page">
    <div class="page-head">
      <div><h1>续办指南</h1><p>材料、地点、费用、时限一目了然；官方入口按你的省份直达</p></div>
    </div>

    <!-- 省份设置条 -->
    <div class="card prov-bar">
      <div class="pb-l">
        <span class="icon-tile s46">📍</span>
        <div>
          <div class="pb-t">我所在的省份</div>
          <div class="pb-s">
            <template v-if="provSel">
              已选择 <b>{{ provName }}</b>，指南与官方入口按本省显示
              <span v-if="provPortal" class="pb-link">· 本省平台：
                <a :href="provPortal.portal_url" target="_blank" rel="noopener noreferrer">{{ provPortal.portal_name }} ↗</a>
              </span>
            </template>
            <template v-else>选择省份后，官方入口将直达本省政务/交管平台</template>
          </div>
        </div>
      </div>
      <RegionPicker :provinces="region.provinces" v-model="provSel" @change="saveProv" />
    </div>

    <div class="row mb">
      <div class="pill-grid">
        <button class="pill" :class="{active: !typeFilter}" @click="typeFilter=null">全部</button>
        <button v-for="t in guidedTypes" :key="t.id" class="pill" :class="{active: typeFilter===t.id}"
                @click="typeFilter=t.id">{{ t.icon }} {{ t.name }}</button>
      </div>
    </div>

    <div v-if="shown.length === 0" class="card empty"><div class="big">📖</div><p>当前分类下暂无指南，可切换分类查看。</p></div>

    <div class="guide-grid">
      <div v-for="item in shown" :key="item.g.id" class="guide">
        <div class="ghead">
          <div class="gi">{{ item.g.type_icon || '🪪' }}</div>
          <div class="gt">
            <div class="gtt">{{ item.g.title }}</div>
            <div class="gtag">
              <span class="tag tag-blue">{{ item.g.type_name || '通用' }}</span>
              <span v-if="item.g.region_code" class="tag tag-green">{{ item.g.region_name }}版</span>
              <span class="tiny muted">更新于 {{ item.g.updated_at }}</span>
            </div>
          </div>
        </div>

        <div class="gridx">
          <div class="it" v-if="item.g.materials?.length"><span class="k">📋 材料清单</span>
            <ul><li v-for="(m,i) in item.g.materials" :key="i">{{ m }}</li></ul></div>
          <div class="it" v-if="item.g.location"><span class="k">📍 办理地点</span><p>{{ item.g.location }}</p></div>
          <div class="it" v-if="item.g.fee"><span class="k">💰 费用</span><p class="strong">{{ item.g.fee }}</p></div>
          <div class="it" v-if="item.g.duration"><span class="k">⏱️ 时限</span><p>{{ item.g.duration }}</p></div>
        </div>

        <div class="gfoot">
          <a v-if="item.entry" class="link-open" :href="item.entry.url" target="_blank" rel="noopener noreferrer">
            前往{{ item.entry.label }} <span class="arr">↗</span></a>
          <button v-else-if="isAdmin()" class="ghost small" @click="$router.push('/admin/guides')">补全官方入口</button>
          <span class="spacer"></span>
          <button class="ghost small" title="复制说明" @click="copyGuide(item.g)">⧉ 复制说明</button>
        </div>
        <div v-if="item.entry?.note" class="entry-note">{{ item.entry.note }}</div>

        <div class="notice warn tiny" style="padding:9px 12px; margin-top:12px">
          <span v-if="item.g.source">来源：{{ item.g.source }}。</span>{{ item.g.disclaimer }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { toastOk } from '../store/toast'
import { isAdmin, auth } from '../store/auth'
import { region, loadLinks, myProvince, bestGuide, resolveEntry, setMyProvince } from '../store/links'
import RegionPicker from '../components/RegionPicker.vue'

const route = useRoute()
const typeFilter = ref(null)
const provSel = ref('')

watch(() => auth.user?.province_code, v => { provSel.value = v || '' }, { immediate: true })

const provName = computed(() => myProvince()?.name || '')
const provPortal = computed(() => { const p = myProvince(); return p?.portal_url ? p : null })

// 有指南的证件类型（作为分类筛选）
const guidedTypes = computed(() => {
  const seen = new Set()
  const res = []
  for (const g of region.guides) {
    if (!seen.has(g.document_type_id)) {
      seen.add(g.document_type_id)
      res.push({ id: g.document_type_id, icon: g.type_icon, name: g.type_name })
    }
  }
  return res
})

// 每个类型解析出最佳指南（本省版 > 全国版）+ 一键直达入口
const resolved = computed(() => {
  const seen = new Set()
  const out = []
  for (const g of region.guides) {
    if (seen.has(g.document_type_id)) continue
    seen.add(g.document_type_id)
    const best = bestGuide(g.document_type_id)
    if (best) out.push({ g: best, entry: resolveEntry(g.document_type_id) })
  }
  return out
})

const shown = computed(() => {
  return resolved.value.filter(item => !typeFilter.value || item.g.document_type_id === typeFilter.value)
})

async function saveProv() {
  try {
    await setMyProvince(provSel.value || null)
    toastOk(provSel.value ? '已切换到 ' + provName.value + '，入口将直达本省' : '已清除省份设置')
  } catch (e) { /* 保留选择，下次再试 */ }
}

function copyGuide(g) {
  const txt = [g.title, '材料：' + (g.materials || []).join('、'), (g.location ? '地点：' + g.location : ''),
    (g.fee ? '费用：' + g.fee : ''), (g.duration ? '时限：' + g.duration : ''),
    (g.official_url ? '官方入口：' + g.official_url : ''), '来源：' + g.source].filter(Boolean).join('\n')
  navigator.clipboard && navigator.clipboard.writeText(txt)
  toastOk('已复制指南说明')
}

onMounted(async () => {
  await loadLinks()
  const qt = Number(route.query.type)
  if (qt) typeFilter.value = qt
})
</script>

<style scoped>
.prov-bar { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 16px 20px; margin-bottom: 16px; }
.pb-l { display: flex; align-items: center; gap: 13px; min-width: 0; }
.pb-t { font-weight: 650; font-size: 14.5px; }
.pb-s { font-size: 12.5px; color: var(--muted); margin-top: 3px; }
.pb-s b { color: var(--brand-dark); }
.pb-link a { font-weight: 500; }
.prov-select { width: auto; min-width: 150px; font-weight: 500; }
.guide-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(370px, 1fr)); gap: 16px; }
.guide {
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--r-md);
  box-shadow: var(--shadow-s); padding: 18px; display: flex; flex-direction: column;
  transition: box-shadow .18s ease, transform .18s ease;
}
.guide:hover { box-shadow: var(--shadow-l); transform: translateY(-2px); }
.ghead { display: flex; gap: 12px; align-items: center; margin-bottom: 10px; }
.gi { display: grid; place-items: center; width: 44px; height: 44px; border-radius: 13px; background: var(--brand-soft); font-size: 22px; flex: 0 0 auto; }
.gtt { font-weight: 650; font-size: 15px; letter-spacing: -.2px; }
.gtag { margin-top: 5px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.tiny { font-size: 11px; }
.gridx { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 14px; }
.it { margin-top: 6px; }
.it .k { display: block; color: var(--muted); font-size: 12px; margin-bottom: 3px; font-weight: 600; }
.it p, .it ul { margin: 2px 0 0; font-size: 13px; line-height: 1.65; color: var(--text-2); }
.it ul { padding-left: 16px; }
.it p.strong { color: var(--text); font-weight: 600; }
.gfoot { display: flex; align-items: center; gap: 10px; margin-top: 16px; flex-wrap: wrap; }
.spacer { flex: 1; }
.entry-note { font-size: 11.5px; color: var(--muted); margin-top: 8px; padding-left: 2px; }
@media (max-width:760px){ .gridx{ grid-template-columns: 1fr; } .prov-bar { flex-direction: column; align-items: stretch; } }
</style>
