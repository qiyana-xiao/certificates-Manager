<template>
  <div class="rp" @blur.capture="onBlur">
    <button type="button" class="trigger" :class="{open}" @click="open = !open">
      <span class="trig-ic">📍</span>
      <span class="trig-tx" :class="{ph: !modelValue}">{{ label }}</span>
      <span class="chev">▾</span>
    </button>

    <transition name="pop">
      <div v-if="open" class="panel">
        <div class="search">
          <span class="s-ic">🔍</span>
          <input ref="searchRef" v-model="query" type="text"
                 placeholder="搜索省份 / 拼音 / 首字母，如 gz" />
          <button v-if="query" type="button" class="clear" @click="query=''">✕</button>
        </div>

        <div class="likely" v-if="!query">
          <button type="button" class="opt all-hit" @click="choose('')">清除选择 · 未设置省份</button>
        </div>

        <div class="group-list" :class="{noscroll: searchHit.length < 5}">
          <template v-if="searchHit.length === 0">
            <div class="no-hit">没有匹配的省份，换个关键词试试</div>
          </template>
          <section v-for="grp in groups" :key="grp.name" class="group">
            <div v-if="grp.items.length" class="gtitle">{{ grp.name }}</div>
            <button v-for="p in grp.items" :key="p.code" type="button"
                    class="opt" :class="{sel: selectedCode === p.code}"
                    @click="choose(p.code)">
              <span class="ini">{{ pinyinOf(p).L }}</span>
              <span class="nm">{{ p.name }}</span>
              <span class="tick" v-if="selectedCode === p.code">✓</span>
            </button>
          </section>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { PINYIN_MAP, matchProvince } from '../utils/pinyin'

const props = defineProps({
  provinces: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'change'])

const open = ref(false)
const query = ref('')
const GROUP_ORDER = ['直辖市', '省', '自治区']

const selectedCode = computed(() => props.modelValue)
const label = computed(() => {
  const p = props.provinces.find(x => x.code === props.modelValue)
  return p ? p.name : '未设置省份'
})

function pinyinOf(p) {
  return PINYIN_MAP[p.code] || { L: '', I: '', P: '' }
}

// A-Z 索引条已移除（用户要求去掉字母索引），仅保留搜索过滤
const searchHit = computed(() => {
  return props.provinces.filter(p => matchProvince(p, query.value))
})

const groups = computed(() => {
  return GROUP_ORDER.map(name => ({
    name,
    items: searchHit.value.filter(p => (p.region_type || '省') === name),
  }))
})

function choose(code) {
  emit('update:modelValue', code)
  emit('change', code)
  open.value = false
  query.value = ''
}

function onBlur(e) {
  // 点击面板内部不关闭
  if (e.relatedTarget && e.currentTarget.contains(e.relatedTarget)) return
  open.value = false
}

function onDocClick(e) {
  if (open.value && !e.composedPath().some(n => n.classList && n.classList.contains('rp'))) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', onDocClick))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocClick))
</script>

<style scoped>
.rp { position: relative; display: inline-block; }
.trigger {
  display: inline-flex; align-items: center; gap: 7px;
  height: 40px; padding: 0 14px; border-radius: 12px;
  border: 1px solid var(--line); background: #fff; cursor: pointer;
  font-size: 13.5px; color: var(--text); font-weight: 500;
  box-shadow: 0 1px 2px rgba(23,30,46,.04); transition: all .16s ease; min-width: 190px;
}
.trigger:hover { border-color: rgba(79,107,247,.4); box-shadow: var(--shadow-s); }
.trigger.open { border-color: var(--brand); box-shadow: 0 0 0 3px rgba(79,107,247,.14); }
.trig-tx { flex: 1; text-align: left; }
.trig-tx.ph { color: var(--muted); font-weight: 400; }
.chev { color: var(--muted); font-size: 11px; }
.panel {
  position: absolute; top: calc(100% + 8px); right: 0; z-index: 960;
  width: min(340px, 90vw); background: #fff; border-radius: 16px;
  border: 1px solid var(--line); box-shadow: 0 20px 50px -14px rgba(15,20,40,.28);
  padding: 10px; max-height: 420px; display: flex; flex-direction: column;
}
.search { display: flex; align-items: center; gap: 6px; border: 1px solid var(--line);
  border-radius: 10px; padding: 6px 10px; background: #fafbfe; }
.search:focus-within { border-color: var(--brand); box-shadow: 0 0 0 3px rgba(79,107,247,.12); }
.s-ic { color: var(--muted); font-size: 13px; }
.search input { flex: 1; border: none; outline: none; background: transparent; font-size: 13px; }
.clear { border: none; background: transparent; color: var(--muted); cursor: pointer; font-size: 12px; }
.group-list { overflow: auto; flex: 1; min-height: 60px; }
.group-list.noscroll { overflow: visible; }
.gtitle { font-size: 11px; font-weight: 700; color: var(--muted); letter-spacing: .5px;
  margin: 8px 2px 4px; text-transform: uppercase; }
.opt {
  display: flex; align-items: center; gap: 8px; width: 100%; text-align: left;
  border: none; background: transparent; cursor: pointer;
  padding: 7px 9px; border-radius: 9px; font-size: 13.5px; color: var(--text);
  transition: background .12s ease;
}
.opt:hover { background: var(--brand-soft); color: var(--brand-dark); font-weight: 600; }
.opt.sel { background: var(--brand-soft); color: var(--brand-dark); font-weight: 700; box-shadow: inset 0 0 0 1px rgba(79,107,247,.18); }
.ini {
  width: 20px; height: 20px; display: grid; place-items: center; flex: 0 0 auto;
  border-radius: 6px; background: #eef1fb; color: var(--muted); font-size: 11px; font-weight: 700;
}
.opt.sel .ini, .opt:hover .ini { background: #fff; color: var(--brand-dark); }
.tick { margin-left: auto; color: var(--brand); font-weight: 800; font-size: 13px; }
.likely { padding: 0 2px; }
.all-hit { color: var(--muted); font-weight: 500; }
.all-hit:hover { color: var(--brand-dark); }
.no-hit { text-align: center; color: var(--muted); padding: 22px 0; font-size: 12.5px; }
.pop-enter-active, .pop-leave-active { transition: all .14s ease; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-4px); }
</style>