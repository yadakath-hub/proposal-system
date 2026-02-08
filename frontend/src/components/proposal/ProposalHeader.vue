<template>
  <header class="h-14 bg-white border-b px-4 flex items-center justify-between">
    <!-- 左側：返回 + 專案名稱 -->
    <div class="flex items-center gap-4">
      <el-button text :icon="ArrowLeft" @click="$router.push('/projects')">
        返回
      </el-button>
      <div class="flex items-center gap-2">
        <el-icon :size="20" class="text-blue-500"><Document /></el-icon>
        <span class="font-bold text-lg">標案建議書生成系統</span>
        <el-divider direction="vertical" />
        <span class="text-gray-500">{{ project?.name || '未命名專案' }}</span>
      </div>
    </div>

    <!-- 右側：操作按鈕 -->
    <div class="flex items-center gap-3">
      <el-button type="primary" :icon="Upload" @click="$emit('import-structure')">
        匯入章節架構
      </el-button>

      <el-button type="warning" :icon="Search" @click="$emit('analyze-requirements')">
        分析招標需求
      </el-button>

      <el-button :icon="Edit" @click="$emit('toggle-mode')">
        編輯模式
      </el-button>

      <div class="flex items-center gap-2 px-4">
        <span class="text-sm text-gray-500">完成進度</span>
        <el-progress
          :percentage="progress"
          :stroke-width="8"
          :show-text="false"
          class="w-32"
        />
        <span class="text-sm font-medium">{{ progress }}%</span>
      </div>

      <el-button :icon="Download" @click="$emit('export')">
        匯出 JSON
      </el-button>
    </div>
  </header>
</template>

<script setup>
import { ArrowLeft, Document, Upload, Edit, Download, Search } from '@element-plus/icons-vue'

defineProps({
  project: Object,
  progress: { type: Number, default: 0 }
})

defineEmits(['import-structure', 'toggle-mode', 'export', 'analyze-requirements'])
</script>
