<template>
  <div
    class="flex items-center gap-4 p-4 bg-white border rounded-lg mb-3 hover:shadow-md transition-shadow cursor-pointer"
    @click="$emit('click', section)"
  >
    <div class="drag-handle cursor-move text-gray-400 hover:text-gray-600">
      <el-icon :size="20"><Rank /></el-icon>
    </div>

    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2">
        <span class="font-mono text-gray-500 text-sm">{{ section.chapter_number }}</span>
        <span class="font-medium">{{ section.title }}</span>
        <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
        <el-tag v-if="section.locked_by" type="danger" size="small">
          <el-icon class="mr-1"><Lock /></el-icon>已鎖定
        </el-tag>
      </div>
      <p class="text-sm text-gray-500 mt-1" :class="{ 'pl-4': section.depth_level > 0 }">
        {{ section.requirement_text ? section.requirement_text.substring(0, 80) + '...' : '尚無需求描述' }}
      </p>
    </div>

    <div class="text-sm text-gray-400 whitespace-nowrap">
      {{ section.estimated_pages || 1 }} 頁
    </div>

    <el-dropdown trigger="click" @click.stop>
      <el-button :icon="More" text size="small" />
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item :icon="Edit" @click.stop="$emit('edit', section)">
            編輯
          </el-dropdown-item>
          <el-dropdown-item :icon="Delete" @click.stop="$emit('delete', section)">
            刪除
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Rank, More, Edit, Delete, Lock } from '@element-plus/icons-vue'

const props = defineProps({
  section: { type: Object, required: true }
})

defineEmits(['click', 'edit', 'delete'])

const STATUS_MAP = {
  NotStarted: { text: '未開始', type: 'info' },
  Writing: { text: '撰寫中', type: 'warning' },
  Review: { text: '審核中', type: '' },
  Approved: { text: '已核准', type: 'success' },
  Locked: { text: '已鎖定', type: 'danger' }
}

const statusType = computed(() => STATUS_MAP[props.section.status]?.type || 'info')
const statusText = computed(() => STATUS_MAP[props.section.status]?.text || props.section.status)
</script>
