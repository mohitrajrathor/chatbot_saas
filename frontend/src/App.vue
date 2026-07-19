<script setup>
import Toast from 'primevue/toast'
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 font-sans">
    <Toast position="bottom-right" />
    <router-view />
  </div>
</template>
