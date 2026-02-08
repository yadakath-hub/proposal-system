<template>
  <div class="section-tree h-full flex flex-col">
    <!-- 搜尋框 -->
    <div class="p-3 border-b">
      <el-input
        v-model="searchText"
        placeholder="搜尋章節..."
        :prefix-icon="Search"
        clearable
        size="small"
      />
    </div>

    <!-- 新增章節按鈕 -->
    <div class="p-3 border-b">
      <el-button type="primary" :icon="Plus" class="w-full" @click="$emit('add')">
        新增章節
      </el-button>
    </div>

    <!-- 提示文字 -->
    <div class="px-3 py-2 bg-blue-50 text-blue-600 text-xs flex items-center gap-1">
      <el-icon><InfoFilled /></el-icon>
      <span>拖曳可調整順序，點擊編輯或刪除章節</span>
    </div>

    <!-- 章節樹 -->
    <div class="flex-1 overflow-auto p-2">
      <el-tree
        ref="treeRef"
        :data="filteredSections"
        :props="treeProps"
        node-key="id"
        :current-node-key="currentSection?.id"
        :highlight-current="true"
        :expand-on-click-node="false"
        :default-expand-all="true"
        draggable
        @node-click="handleNodeClick"
        @node-drop="handleNodeDrop"
      >
        <template #default="{ node, data }">
          <div class="section-node flex items-center justify-between w-full py-1 pr-2 group">
            <div class="flex items-center gap-2 min-w-0">
              <el-icon class="drag-handle text-gray-400 cursor-move opacity-0 group-hover:opacity-100">
                <Rank />
              </el-icon>
              <span class="section-number bg-blue-500 text-white text-xs px-2 py-0.5 rounded">
                {{ data.chapter_number || node.level }}
              </span>
              <span class="truncate">{{ data.title }}</span>
            </div>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100">
              <el-tag
                v-if="data.status"
                :type="getStatusType(data.status)"
                size="small"
              >
                {{ getStatusText(data.status) }}
              </el-tag>
              <el-button
                text
                size="small"
                :icon="Delete"
                class="text-red-500"
                @click.stop="$emit('delete', data)"
              />
            </div>
          </div>
        </template>
      </el-tree>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Search, Plus, Rank, Delete, InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  sections: { type: Array, default: () => [] },
  currentSection: Object
})

const emit = defineEmits(['select', 'reorder', 'add', 'delete'])

const searchText = ref('')
const treeRef = ref()

const treeProps = {
  children: 'children',
  label: 'title'
}

const filteredSections = computed(() => {
  if (!searchText.value) return props.sections

  const search = searchText.value.toLowerCase()
  const filterNodes = (nodes) => {
    return nodes.filter(node => {
      const match = node.title?.toLowerCase().includes(search)
      if (node.children?.length) {
        const children = filterNodes(node.children)
        if (children.length) {
          return true
        }
      }
      return match
    }).map(node => ({
      ...node,
      children: node.children?.length ? filterNodes(node.children) : []
    }))
  }
  return filterNodes(props.sections)
})

function handleNodeClick(data) {
  emit('select', data)
}

function handleNodeDrop() {
  // Collect new ordering from tree data
  const collectItems = (nodes, result = [], index = { value: 0 }) => {
    nodes.forEach(n => {
      result.push({ id: n.id, sort_order: index.value++ })
      if (n.children?.length) collectItems(n.children, result, index)
    })
    return result
  }
  const items = collectItems(props.sections)
  emit('reorder', items)
}

function getStatusType(status) {
  const map = {
    Approved: 'success',
    Writing: 'warning',
    Review: '',
    NotStarted: 'info',
    Locked: 'danger'
  }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = {
    Approved: '已完成',
    Writing: '撰寫中',
    Review: '審核中',
    NotStarted: '未開始',
    Locked: '已鎖定'
  }
  return map[status] || '未開始'
}
</script>

<style scoped>
:deep(.el-tree-node__content) {
  height: auto;
  padding: 4px 0;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: #e6f7ff;
}

.section-node:hover {
  background-color: #f5f5f5;
}
</style>
