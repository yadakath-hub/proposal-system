<template>
  <el-header class="bg-white border-b border-gray-200 flex items-center justify-between px-6">
    <div class="flex items-center">
      <el-button
        :icon="uiStore.sidebarCollapsed ? Expand : Fold"
        text
        @click="uiStore.toggleSidebar"
      />
      <el-breadcrumb separator="/" class="ml-4">
        <el-breadcrumb-item :to="{ path: '/dashboard' }">首頁</el-breadcrumb-item>
        <el-breadcrumb-item v-if="route.meta.title">
          {{ route.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="flex items-center gap-4">
      <el-dropdown trigger="click">
        <span class="flex items-center cursor-pointer">
          <el-avatar :size="32" class="bg-blue-500">
            {{ authStore.userName?.charAt(0)?.toUpperCase() || 'U' }}
          </el-avatar>
          <span class="ml-2 text-gray-700">{{ authStore.userName }}</span>
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
  </el-header>
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
