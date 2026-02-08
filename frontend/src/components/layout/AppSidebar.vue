<template>
  <el-aside
    :width="uiStore.sidebarCollapsed ? '64px' : '200px'"
    class="bg-gray-800 transition-all duration-300"
  >
    <div class="h-14 flex items-center justify-center border-b border-gray-700">
      <span v-if="!uiStore.sidebarCollapsed" class="text-white font-bold text-lg">
        BPA System
      </span>
      <span v-else class="text-white font-bold text-lg">B</span>
    </div>

    <el-menu
      :default-active="route.path"
      :collapse="uiStore.sidebarCollapsed"
      :collapse-transition="false"
      background-color="#1f2937"
      text-color="#9ca3af"
      active-text-color="#ffffff"
      router
    >
      <el-menu-item index="/dashboard">
        <el-icon><HomeFilled /></el-icon>
        <template #title>儀表板</template>
      </el-menu-item>

      <el-menu-item index="/projects">
        <el-icon><Folder /></el-icon>
        <template #title>專案管理</template>
      </el-menu-item>

      <el-menu-item index="/documents">
        <el-icon><Document /></el-icon>
        <template #title>文件管理</template>
      </el-menu-item>

      <el-menu-item index="/templates">
        <el-icon><Collection /></el-icon>
        <template #title>範本庫</template>
      </el-menu-item>

      <el-menu-item index="/settings">
        <el-icon><Setting /></el-icon>
        <template #title>系統設定</template>
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { HomeFilled, Folder, Document, Setting, Collection } from '@element-plus/icons-vue'

const route = useRoute()
const uiStore = useUiStore()
</script>
