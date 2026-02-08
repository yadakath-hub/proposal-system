<template>
  <el-card
    shadow="hover"
    class="project-card"
    @click="$emit('click', project)"
  >
    <div class="card-header">
      <div class="project-info">
        <h3 class="project-name">{{ project.name }}</h3>
        <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
      </div>
      <el-dropdown trigger="click" @click.stop>
        <el-button :icon="More" text size="small" />
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :icon="Edit" @click.stop="$emit('edit', project)">
              編輯
            </el-dropdown-item>
            <el-dropdown-item :icon="EditPen" @click.stop="goToEditor">
              進入編輯器
            </el-dropdown-item>
            <el-dropdown-item :icon="Delete" divided @click.stop="$emit('delete', project)">
              刪除
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <p class="project-desc">{{ project.description || '暫無描述' }}</p>

    <div class="card-footer">
      <div class="stats">
        <span v-if="project.tender_number" class="stat-item">
          {{ project.tender_number }}
        </span>
        <span class="stat-item">
          <el-icon><Clock /></el-icon>
          {{ formatDate(project.updated_at) }}
        </span>
      </div>
      <el-button type="primary" text size="small" @click.stop="goToEditor">
        開始編輯 &rarr;
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { More, Edit, EditPen, Delete, Clock } from '@element-plus/icons-vue'

const props = defineProps({
  project: { type: Object, required: true }
})

defineEmits(['click', 'edit', 'delete'])

const router = useRouter()

const STATUS_MAP = {
  Draft: { text: '草稿', type: 'info' },
  InProgress: { text: '進行中', type: 'warning' },
  Completed: { text: '已完成', type: 'success' },
  Archived: { text: '已封存', type: '' }
}

const statusType = computed(() => STATUS_MAP[props.project.status]?.type || 'info')
const statusText = computed(() => STATUS_MAP[props.project.status]?.text || props.project.status)

function goToEditor() {
  router.push(`/projects/${props.project.id}/editor`)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-TW')
}
</script>

<style scoped>
.project-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.project-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 42px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
