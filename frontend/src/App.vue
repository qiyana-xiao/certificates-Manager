<template>
  <router-view />
  <Toast />
  <DailyPopup />
</template>
<script setup>
import Toast from './components/Toast.vue'
import DailyPopup from './components/DailyPopup.vue'
</script>