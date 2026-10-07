<template>
  <div class="toast-wrap">
    <div v-for="t in toasts.list" :key="t.id" class="toast" :class="t.type">
      <span>{{ t.type === 'err' ? '⚠️' : '✅' }}</span><span>{{ t.message }}</span>
    </div>
  </div>
</template>
<script setup>
import { toasts } from '../store/toast'
</script>