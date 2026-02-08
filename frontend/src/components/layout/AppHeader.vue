<template>
  <div class="header-content">
    <div class="header-left">
      <el-button
        :icon="uiStore.sidebarCollapsed ? Expand : Fold"
        text
        @click="uiStore.toggleSidebar"
      />
      <el-breadcrumb separator="/" class="ml-3">
        <el-breadcrumb-item :to="{ path: '/dashboard' }">首頁</el-breadcrumb-item>
        <el-breadcrumb-item v-if="route.meta.title">
          {{ route.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="header-right">
      <el-dropdown trigger="click">
        <span class="user-dropdown">
          <el-avatar :size="32" class="bg-blue-500">
            {{ authStore.userName?.charAt(0)?.toUpperCase() || 'U' }}
          </el-avatar>
          <span class="user-name">{{ authStore.userName }}</span>
          <el-icon class="ml-1"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :icon="User">個人資料</el-dropdown-item>
            <el-dropdown-item :icon="Setting">設定</el-dropdown-item>
            <el-dropdown-item divided :icon="SwitchButton" @click="handleLogout">
              登出
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { Fold, Expand, ArrowDown, User, Setting, SwitchButton } from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()
const uiStore = useUiStore()

function handleLogout() {
  authStore.logout()
}
</script>

<style scoped>
.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 100%;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.user-dropdown:hover {
  background: #f5f5f5;
}

.user-name {
  margin-left: 8px;
  color: var(--text-primary);
  font-size: 14px;
}
</style>
