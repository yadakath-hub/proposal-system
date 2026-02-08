<template>
  <el-container class="min-h-screen">
    <template v-if="!isFullscreen">
      <AppSidebar />
      <el-container>
        <AppHeader />
        <el-main class="bg-gray-50">
          <router-view />
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
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

const route = useRoute()
const isFullscreen = computed(() => route.meta.fullscreen)
</script>
