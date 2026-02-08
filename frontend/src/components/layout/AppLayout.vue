<template>
  <el-container class="min-h-screen">
    <AppSidebar />
    <el-container>
      <AppHeader />
      <el-main class="bg-gray-50">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
</script>
