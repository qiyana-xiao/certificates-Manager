<template>
  <div class="page">
    <div class="page-head">
      <div><h1>到期日历</h1><p>把"到期"当日程看，绿色正常 · 黄色临期 · 红色已过期</p></div>
      <div class="seg">
        <button @click="shift(-12)" title="上一年">‹‹</button>
        <button @click="shift(-1)" title="上月">‹</button>
        <button class="ym" type="button" @click="openPicker">📆 {{ year }} 年 {{ month }} 月 ▾</button>
        <button @click="shift(1)" title="下月">›</button>
        <button @click="shift(12)" title="下一年">››</button>
      </div>
    </div>

    <div v-if="showPicker" class="pick-mask" @click.self="closePicker">
      <div class="picker">
        <div class="pk-head">
          <button type="button" class="ghost small" @click="yearJump(-1)">‹ 上一年</button>
          <span>{{ pickYear }} 年</span>
          <button type="button" class="ghost small" @click="yearJump(1)">下一年 ›</button>
        </div>
        <div class="pk-mid">
          <label>跳转到<input type="month" v-model="pickMonth" @change="applyMonth"></label>
        </div>
        <div class="pk-months">
          <button v-for="m in 12" :key="m" type="button" class="pk-m"
                  :class="{on: pickYear===year && m===month}"
                  @click="jumpTo(pickYear, m)">{{ m }} 月</button>
        </div>
        <div class="pk-foot">
          <button type="button" class="ghost small" @click="backToday">回到今天</button>
          <button type="button" class="primary small" @click="closePicker">关闭</button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="week">
        <span v-for="w in ['一','二','三','四','五','六','日']" :key="w">{{ w }}</span>
      </div>
      <div class="grid">
        <div v-for="(cell, i) in cells" :key="i"
             class="day" :class="{blank: !cell, today: cell && cell.isToday, 'has-doc': cell && cell.hasDoc}">
          <template v-if="cell">
            <div class="dhead">
              <span class="date-chip" :class="cell.hasDoc ? cell.kind : ''">{{ cell.day }}</span>
              <span v-if="cell.hasDoc" class="dot" :class="cell.kind"></span>
            </div>
            <div class="evts">
              <div v-for="item in cell.items" :key="item.id" class="evt"
                   :class="'evt-'+item.status"
                   :title="item.title" @click="goGuide(item)">{{ item.title }}</div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const now = new Date()
const year = ref(now.getFullYear())
const month = ref(now.getMonth() + 1)
const items = ref([])
const showPicker = ref(false)
const pickYear = ref(now.getFullYear())
const pickMonth = ref('')

async function load() {
  const data = await api.get(`/calendar?year=${year.value}&month=${month.value}`)
  items.value = data.items
}
function shift(d) {
  const y0 = year.value
  const m0 = month.value
  let total = y0 * 12 + (m0 - 1) + d
  year.value = Math.floor(total / 12)
  month.value = (total % 12) + 1
  if (month.value < 1) { month.value = 12; year.value-- }
  load()
}
function openPicker() {
  pickYear.value = year.value
  pickMonth.value = `${year.value}-${String(month.value).padStart(2, '0')}`
  showPicker.value = true
}
function closePicker() { showPicker.value = false }
function yearJump(d) { pickYear.value += d }
function jumpTo(y, m) { year.value = y; month.value = m; showPicker.value = false; load() }
function applyMonth() {
  const parts = String(pickMonth.value).split('-')
  if (parts.length === 2) { year.value = +parts[0]; month.value = +parts[1] }
  showPicker.value = false; load()
}
function backToday() {
  year.value = now.getFullYear(); month.value = now.getMonth() + 1
  showPicker.value = false; load()
}
const cells = computed(() => {
  const first = new Date(year.value, month.value - 1, 1)
  // 周一为一周第一天
  let offset = (first.getDay() + 6) % 7
  const daysInMonth = new Date(year.value, month.value, 0).getDate()
  let res = []
  for (let i = 0; i < offset; i++) res.push(null)
  const today = new Date()
  for (let d = 1; d <= daysInMonth; d++) {
    const isToday = today.getFullYear() === year.value && today.getMonth() === month.value - 1 && today.getDate() === d
    const dayItems = items.value.filter(x => Number(x.expire_date.split('-')[2]) === d)
    res.push({
      day: d,
      isToday,
      hasDoc: dayItems.length > 0,
      kind: dayKind(dayItems),
      items: dayItems,
    })
  }
  return res
})
// 当天颜色按最紧急的一条状态定：已过期红 > 临期黄 > 正常绿
const SEVERITY = { EXPIRED: 2, EXPIRING: 1, VALID: 0 }
function dayKind(dayItems) {
  let best = -1
  for (const it of dayItems) {
    const s = SEVERITY[it.status]
    if (s === undefined) continue
    if (s > best) best = s
  }
  return best === 2 ? 'evt-EXPIRED' : best === 1 ? 'evt-EXPIRING' : 'evt-VALID'
}
function goGuide() { router.push('/guides') }
onMounted(load)
</script>

<style scoped>
.week { display: grid; grid-template-columns: repeat(7,1fr); color: var(--muted); font-size: 12.5px; margin-bottom: 10px; }
.week span { text-align: center; padding: 6px 0; font-weight: 500; }
.grid { display: grid; grid-template-columns: repeat(7,1fr); gap: 7px; }
.day {
  min-height: 88px; border: 1px solid var(--line); border-radius: 12px; padding: 7px;
  background: #fff; font-size: 12px; overflow: hidden; transition: box-shadow .16s ease, border-color .16s ease;
}
.day:hover { box-shadow: var(--shadow-s); }
.day.blank { background: transparent; border-color: transparent; }
.day.today { border-color: var(--brand); box-shadow: 0 0 0 2.5px rgba(79,107,247,.14); }
.dhead { display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px; }
/* 普通日期：保持白色、中性灰数字 */
.date-chip {
  display: inline-grid; place-items: center; min-width: 24px; height: 24px; padding: 0 4px;
  border-radius: 8px; font-weight: 600; font-variant-numeric: tabular-nums;
  color: var(--muted); background: transparent; font-size: 12px;
}
.day.today .date-chip { color: var(--brand-dark); font-weight: 700; }
/* 有证件日期：按最紧急状态上色（浅色底 + 加深数字），配旁边的状态圆点 */
.date-chip.evt-VALID { background: var(--green-soft); color: var(--green); font-weight: 700; }
.date-chip.evt-EXPIRING { background: var(--amber-soft); color: var(--amber-dark, #8a5a06); font-weight: 700; }
.date-chip.evt-EXPIRED { background: var(--red-soft); color: var(--red); font-weight: 800; }
.dot { width: 8px; height: 8px; border-radius: 50%; flex: 0 0 auto; box-shadow: 0 0 0 3px rgba(255,255,255,.6); }
.dot.evt-VALID { background: var(--green); }
.dot.evt-EXPIRING { background: var(--amber); }
.dot.evt-EXPIRED { background: var(--red); }
/* 证件条目：改成纤细的小药丸，而非粗横线 */
.evts { display: flex; flex-direction: column; gap: 3px; }
.evt { border-radius: 7px; padding: 3px 7px; font-size: 11.5px; line-height: 1.3;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; font-weight: 500; }
.evt-VALID { background: var(--green-soft); color: var(--green); }
.evt-EXPIRING { background: var(--amber-soft); color: #9a6609; }
.evt-EXPIRED { background: var(--red-soft); color: var(--red); }
.evt-ARCHIVED { background: var(--slate-soft); color: var(--muted); }
.ym {
  align-self: center; min-width: 128px; text-align: center; font-weight: 600; font-size: 13.5px;
  color: var(--text); padding: 7px 10px; border-radius: 10px; cursor: pointer;
  border: 1px solid transparent; background: transparent; transition: all .16s ease;
}
.ym:hover { background: var(--brand-soft); border-color: rgba(79,107,247,.25); color: var(--brand-dark); }
.pick-mask {
  position: fixed; inset: 0; z-index: 900; background: rgba(17,23,46,.4);
  backdrop-filter: blur(2px); -webkit-backdrop-filter: blur(2px);
  display: grid; place-items: center; padding: 20px;
}
.picker {
  width: min(430px, 94vw); background: #fff; border-radius: 18px;
  box-shadow: 0 24px 60px -18px rgba(15,20,40,.45); padding: 18px 20px 16px;
}
.pk-head { display: flex; align-items: center; justify-content: space-between; font-weight: 650; color: var(--text); }
.pk-mid { margin: 12px 0 6px; }
.pk-mid label { font-size: 12.5px; color: var(--muted); display: flex; align-items: center; gap: 8px; }
.pk-mid input { width: auto; }
.pk-months { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.pk-m {
  padding: 9px 0; border: 1px solid var(--line); border-radius: 10px; background: #fff;
  font-size: 13px; color: var(--text-2); cursor: pointer; transition: all .14s ease;
}
.pk-m:hover { border-color: var(--brand); color: var(--brand-dark); }
.pk-m.on { background: var(--grad); color: #fff; border-color: transparent; font-weight: 600; }
.pk-foot { margin-top: 14px; display: flex; justify-content: space-between; gap: 10px; }
</style>
