<template>
  <el-container class="app-layout">
    <template v-if="!isFullscreen">
      <!-- Sidebar -->
      <el-aside
        :width="uiStore.sidebarCollapsed ? '64px' : '200px'"
        class="app-sidebar"
      >
        <AppSidebar />
      </el-aside>

      <!-- Main content -->
      <el-container class="main-container">
        <el-header class="app-header" height="56px">
          <AppHeader />
        </el-header>

        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </template>
    <template v-else>
      <router-view />
    </template>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

const route = useRoute()
const uiStore = useUiStore()

const isFullscreen = computed(() => route.meta.fullscreen)
</script>

<style scoped>
.app-layout {
  height: 100vh;
  overflow: hidden;
}

.app-sidebar {
  background: linear-gradient(180deg, #001529 0%, #002140 100%);
  transition: width 0.3s ease;
  overflow: hidden;
}

.main-container {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-header {
  background: #fff;
  border-bottom: 1px solid var(--border-color);
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.app-main {
  flex: 1;
  padding: 0;
  background: #f0f2f5;
  overflow: auto;
}

@media (max-width: 1024px) {
  .app-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 1000;
  }
}
</style>
