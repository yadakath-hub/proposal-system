<template>
  <footer class="h-12 bg-white border-t px-6 flex items-center justify-between">
    <div class="flex items-center gap-8">
      <div class="flex items-center gap-2">
        <span class="text-2xl font-bold text-green-600">{{ stats.completed }}</span>
        <span class="text-sm text-gray-500">已完成</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-2xl font-bold text-blue-600">{{ stats.generating }}</span>
        <span class="text-sm text-gray-500">生成中</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-2xl font-bold text-gray-400">{{ stats.pending }}</span>
        <span class="text-sm text-gray-500">未開始</span>
      </div>
    </div>

    <div class="flex items-center gap-2 bg-gray-800 text-white px-4 py-2 rounded-lg">
      <el-icon><Document /></el-icon>
      <span>估計總頁數</span>
      <span class="text-xl font-bold">{{ stats.estimatedPages.toFixed(1) }}</span>
      <span>頁</span>
    </div>
  </footer>
</template>

<script setup>
import { Document } from '@element-plus/icons-vue'

defineProps({
  stats: {
    type: Object,
    default: () => ({
      completed: 0,
      generating: 0,
      pending: 0,
      estimatedPages: 0
    })
  }
})
</script>
