<template>
  <div class="page narrow" style="max-width:860px">
    <div class="page-head">
      <div><h1>家庭提醒</h1><p>给家里老人、孩子各建一个成员，只需填名字，颜色自动分配</p></div>
      <button class="primary" @click="showAdd = true">＋ 添加成员</button>
    </div>

    <div v-if="members.length === 0" class="card empty">
      <div class="big">👨‍👩‍👦</div>
      <h3>还没有家庭成员</h3>
      <p>添加后，给证件选择"归属成员"就能分清谁的证快到期。</p>
      <button class="primary mt" @click="showAdd = true">添加第一个成员</button>
    </div>

    <div class="mem-list">
      <div v-for="m in members" :key="m.id" class="card mem">
        <span class="avatar" :style="{background:m.member_color}">{{ m.member_name[0] }}</span>
        <div class="grow">
          <div style="font-weight:650">{{ m.member_name }}</div>
          <div class="small muted">{{ m.doc_count }} 张在管证件</div>
        </div>
        <button class="ghost small muted" @click="remove(m)">删除</button>
      </div>
    </div>

    <div class="notice info mt">提示：在「我的证件 → 添加证件」里点选归属成员，其到期状态会以该成员颜色显示在卡片角标上。</div>

    <div v-if="showAdd" class="modal-mask" @click.self="showAdd=false">
      <div class="modal card">
        <h3 style="margin:0 0 4px">添加家庭成员</h3>
        <p class="hint" style="margin:0 0 14px">只填一个名字就够了</p>
        <label class="field"><span>称呼 / 姓名</span>
          <input v-model="name" maxlength="40" placeholder="例如：奶奶 / 小宝" @keyup.enter="save">
        </label>
        <div class="row" style="justify-content:flex-end">
          <button class="ghost" @click="showAdd=false">取消</button>
          <button class="primary" @click="save" :disabled="!name.trim()">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { toastOk } from '../store/toast'

const members = ref([])
const showAdd = ref(false)
const name = ref('')

// 颜色自动轮换分配，无需手动挑选
const PALETTE = ['#4f6bf7', '#149957', '#d97706', '#dc2626', '#8b5cf6', '#0891b2', '#db2777', '#475569']

async function load() { members.value = await api.get('/family') }
async function save() {
  const color = PALETTE[members.value.length % PALETTE.length]
  await api.post('/family', { member_name: name.value.trim(), member_color: color })
  name.value = ''
  showAdd.value = false
  toastOk('成员已添加')
  load()
}
async function remove(m) {
  if (!confirm('删除成员「' + m.member_name + '」？其证件会变为"我自己"。')) return
  await api.del(`/family/${m.id}`)
  toastOk('已删除')
  load()
}
onMounted(load)
</script>

<style scoped>
.mem-list { display: grid; gap: 12px; }
.mem { display: flex; align-items: center; gap: 14px; padding: 16px 18px; }
.avatar {
  width: 44px; height: 44px; border-radius: 14px; color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 650; font-size: 17px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.25);
}
.modal-mask { position: fixed; inset: 0; background: rgba(13, 18, 33, .48); display: flex; align-items: center; justify-content: center; z-index: 50; backdrop-filter: blur(3px); }
.modal { width: 380px; padding: 24px; }
</style>
