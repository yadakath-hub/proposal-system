<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">儀表板</h1>
    <p class="text-gray-500">歡迎回來，{{ authStore.userName }}！</p>
    <p class="text-gray-400 mt-4">專案列表將在 Phase 7-2 實作...</p>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
</script>
