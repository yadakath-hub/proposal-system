<template>
  <div class="home-container">
    <n-card v-if="authStore.user" style="max-width: 600px; width: 100%">
      <n-space vertical size="large">
        <n-h2 style="margin: 0">智慧投標建議書生成系統</n-h2>
        <n-divider />
        <n-descriptions label-placement="left" bordered :column="1">
          <n-descriptions-item label="姓名">
            {{ authStore.user.full_name }}
          </n-descriptions-item>
          <n-descriptions-item label="信箱">
            {{ authStore.user.email }}
          </n-descriptions-item>
          <n-descriptions-item label="角色">
            <n-tag :type="roleTagType">{{ authStore.user.role }}</n-tag>
          </n-descriptions-item>
        </n-descriptions>
        <n-button type="error" block @click="handleLogout">登出</n-button>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const roleTagType = computed(() => {
  const map: Record<string, 'success' | 'info' | 'warning' | 'default'> = {
    Admin: 'success',
    Editor: 'info',
    Reviewer: 'warning',
  }
  return map[authStore.user?.role ?? ''] ?? 'default'
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
}
</style>
