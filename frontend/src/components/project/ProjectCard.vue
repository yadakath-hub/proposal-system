<template>
  <el-card
    shadow="hover"
    class="cursor-pointer transition-transform hover:scale-[1.02]"
    @click="$emit('click', project)"
  >
    <template #header>
      <div class="flex justify-between items-start">
        <div class="flex-1 min-w-0">
          <h3 class="font-bold text-lg truncate">{{ project.name }}</h3>
          <el-tag :type="statusType" size="small" class="mt-1">{{ statusText }}</el-tag>
        </div>
        <el-dropdown trigger="click" @click.stop>
          <el-button :icon="More" text size="small" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item :icon="Edit" @click.stop="$emit('edit', project)">
                編輯
              </el-dropdown-item>
              <el-dropdown-item :icon="Delete" @click.stop="$emit('delete', project)">
                刪除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </template>

    <p class="text-gray-500 text-sm mb-4 line-clamp-2">
      {{ project.description || '無描述' }}
    </p>

    <div class="flex justify-between text-sm text-gray-400">
      <span v-if="project.tender_number">
        {{ project.tender_number }}
      </span>
      <span v-else>&nbsp;</span>
      <span>{{ formatDate(project.updated_at) }}</span>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { More, Edit, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  project: { type: Object, required: true }
})

defineEmits(['click', 'edit', 'delete'])

const STATUS_MAP = {
  Draft: { text: '草稿', type: 'info' },
  InProgress: { text: '進行中', type: 'warning' },
  Completed: { text: '已完成', type: 'success' },
  Archived: { text: '已封存', type: '' }
}

const statusType = computed(() => STATUS_MAP[props.project.status]?.type || 'info')
const statusText = computed(() => STATUS_MAP[props.project.status]?.text || props.project.status)

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-TW')
}
</script>
