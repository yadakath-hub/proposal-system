<template>
  <footer class="editor-footer">
    <div class="stats-left">
      <div class="stat-item stat-completed">
        <span class="stat-value">{{ stats.completed }}</span>
        <span class="stat-label">已完成</span>
      </div>
      <div class="stat-item stat-generating">
        <span class="stat-value">{{ stats.generating }}</span>
        <span class="stat-label">生成中</span>
      </div>
      <div class="stat-item stat-pending">
        <span class="stat-value">{{ stats.pending }}</span>
        <span class="stat-label">未開始</span>
      </div>
    </div>

    <div class="page-estimate">
      <el-icon><Document /></el-icon>
      <span>估計總頁數</span>
      <span class="page-count">{{ stats.estimatedPages.toFixed(1) }}</span>
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

<style scoped>
.editor-footer {
  height: 48px;
  background: #fff;
  border-top: 1px solid var(--border-color);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.stats-left {
  display: flex;
  gap: 32px;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-completed .stat-value {
  color: #52c41a;
}

.stat-generating .stat-value {
  color: #1890ff;
}

.stat-pending .stat-value {
  color: var(--text-secondary);
}

.page-estimate {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #262626;
  color: #fff;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
}

.page-count {
  font-size: 20px;
  font-weight: 600;
}
</style>
