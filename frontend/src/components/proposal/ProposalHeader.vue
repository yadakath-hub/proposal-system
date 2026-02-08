<template>
  <header class="editor-header">
    <!-- Left: Back + project name -->
    <div class="header-left">
      <el-button text :icon="ArrowLeft" @click="$router.push('/projects')">
        返回
      </el-button>
      <el-divider direction="vertical" />
      <div class="project-info">
        <el-icon :size="20" class="text-blue-500"><Document /></el-icon>
        <span class="project-title">標案建議書生成系統</span>
        <span class="project-name">{{ project?.name || '未命名專案' }}</span>
      </div>
    </div>

    <!-- Right: Actions -->
    <div class="header-right">
      <el-button type="primary" :icon="Upload" @click="$emit('import-structure')">
        匯入章節架構
      </el-button>

      <el-button type="warning" :icon="Search" @click="$emit('analyze-requirements')">
        分析招標需求
      </el-button>

      <div class="progress-section">
        <span class="progress-label">完成進度</span>
        <el-progress
          :percentage="progress"
          :stroke-width="8"
          :show-text="false"
          class="progress-bar"
        />
        <span class="progress-value">{{ progress }}%</span>
      </div>

      <el-button :icon="Download" @click="$emit('export')">
        匯出
      </el-button>
    </div>
  </header>
</template>

<script setup>
import { ArrowLeft, Document, Upload, Download, Search } from '@element-plus/icons-vue'

defineProps({
  project: Object,
  progress: { type: Number, default: 0 }
})

defineEmits(['import-structure', 'toggle-mode', 'export', 'analyze-requirements'])
</script>

<style scoped>
.editor-header {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid var(--border-color);
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.project-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.project-title {
  font-weight: 600;
  font-size: 16px;
  white-space: nowrap;
}

.project-name {
  color: var(--text-secondary);
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.project-name::before {
  content: '|';
  margin-right: 8px;
  color: #d9d9d9;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.progress-section {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
}

.progress-label {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.progress-bar {
  width: 120px;
}

.progress-value {
  font-size: 13px;
  font-weight: 600;
  min-width: 36px;
}

@media (max-width: 1280px) {
  .progress-section {
    display: none;
  }

  .project-title {
    display: none;
  }
}
</style>
