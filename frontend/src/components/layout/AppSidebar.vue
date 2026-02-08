<template>
  <div class="sidebar-container">
    <!-- Logo -->
    <div class="sidebar-logo">
      <el-icon :size="28" class="text-blue-400"><Document /></el-icon>
      <span v-show="!collapsed" class="logo-text">BPA System</span>
    </div>

    <!-- Menu -->
    <el-menu
      :default-active="currentRoute"
      :collapse="collapsed"
      :collapse-transition="false"
      background-color="transparent"
      text-color="#ffffffa6"
      active-text-color="#ffffff"
      router
      class="sidebar-menu"
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

    <!-- Collapse toggle -->
    <div class="sidebar-footer">
      <el-button
        text
        class="collapse-btn"
        @click="toggleCollapse"
      >
        <el-icon :size="18">
          <component :is="collapsed ? 'Expand' : 'Fold'" />
        </el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import {
  Document, HomeFilled, Folder, Collection,
  Setting, Expand, Fold
} from '@element-plus/icons-vue'

const route = useRoute()
const uiStore = useUiStore()

const collapsed = computed(() => uiStore.sidebarCollapsed)
const currentRoute = computed(() => route.path)

function toggleCollapse() {
  uiStore.toggleSidebar()
}
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  padding: 8px 0;
}

.sidebar-menu .el-menu-item {
  margin: 4px 8px;
  border-radius: 6px;
  height: 44px;
}

.sidebar-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.1) !important;
}

.sidebar-menu .el-menu-item.is-active {
  background: #1890ff !important;
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.collapse-btn {
  width: 100%;
  color: #ffffffa6;
}

.collapse-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}
</style>
