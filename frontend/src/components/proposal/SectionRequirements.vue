<template>
  <el-card shadow="never">
    <template #header>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <el-icon class="text-orange-500"><List /></el-icon>
          <span>關聯需求</span>
          <el-badge :value="requirements.length" :hidden="requirements.length === 0" />
        </div>
        <el-button text type="primary" size="small" @click="showLinkDialog = true">
          + 關聯需求
        </el-button>
      </div>
    </template>

    <!-- Linked requirements -->
    <div v-if="loading" class="text-center py-4">
      <el-icon class="is-loading"><Loading /></el-icon>
    </div>
    <div v-else-if="requirements.length === 0" class="text-gray-400 text-sm text-center py-4">
      尚未關聯任何需求
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="req in requirements"
        :key="req.link_id"
        class="flex items-start gap-2 p-2 rounded border text-sm"
        :class="req.is_addressed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'"
      >
        <el-checkbox
          :model-value="req.is_addressed"
          @change="(val) => toggleAddressed(req.link_id, val)"
        />
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="font-mono text-xs text-gray-500">{{ req.requirement_key }}</span>
            <el-tag size="small" :type="getTypeTagType(req.requirement_type)">
              {{ getTypeLabel(req.requirement_type) }}
            </el-tag>
            <el-tag size="small" :type="getPriorityType(req.priority)">
              {{ getPriorityLabel(req.priority) }}
            </el-tag>
          </div>
          <p class="text-gray-700 truncate">{{ req.content }}</p>
          <p v-if="req.source_text" class="text-gray-400 text-xs mt-1 truncate">
            原文：{{ req.source_text }}
          </p>
        </div>
        <el-button
          text
          type="danger"
          size="small"
          @click="handleUnlink(req.link_id)"
        >
          移除
        </el-button>
      </div>
    </div>

    <!-- Link dialog -->
    <el-dialog
      v-model="showLinkDialog"
      title="關聯需求至此章節"
      width="600px"
      append-to-body
    >
      <el-input
        v-model="searchQuery"
        placeholder="搜尋需求..."
        class="mb-4"
        clearable
        @input="handleSearch"
      />

      <el-table
        :data="searchResults"
        max-height="300"
        size="small"
        @selection-change="selectedReqs = $event"
      >
        <el-table-column type="selection" width="40" />
        <el-table-column prop="requirement_key" label="ID" width="90" />
        <el-table-column prop="content" label="需求內容" show-overflow-tooltip />
        <el-table-column label="類型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getTypeTagType(row.requirement_type)">
              {{ getTypeLabel(row.requirement_type) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="showLinkDialog = false">取消</el-button>
        <el-button type="primary" :disabled="selectedReqs.length === 0" @click="handleLink">
          關聯 {{ selectedReqs.length }} 個需求
        </el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import { List, Loading } from '@element-plus/icons-vue'
import { requirementsApi } from '@/api/requirements'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  sectionId: [String, Object],
  projectId: [String, Object]
})

const requirements = ref([])
const loading = ref(false)
const showLinkDialog = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const selectedReqs = ref([])

watch(() => props.sectionId, (val) => {
  if (val) loadRequirements()
}, { immediate: true })

async function loadRequirements() {
  if (!props.sectionId) return
  loading.value = true
  try {
    const resp = await requirementsApi.getSectionRequirements(props.sectionId)
    requirements.value = resp.data.requirements || []
  } catch {
    requirements.value = []
  } finally {
    loading.value = false
  }
}

async function toggleAddressed(linkId, val) {
  try {
    await requirementsApi.markAddressed(linkId, val)
    await loadRequirements()
  } catch {
    ElMessage.error('更新失敗')
  }
}

async function handleUnlink(linkId) {
  try {
    await ElMessageBox.confirm('確定要移除此需求關聯嗎？', '提示', { type: 'warning' })
    await requirementsApi.unlinkRequirement(linkId)
    await loadRequirements()
    ElMessage.success('已移除關聯')
  } catch {
    // cancelled or error
  }
}

async function handleSearch() {
  if (!searchQuery.value.trim()) {
    // Show all project requirements
    try {
      const resp = await requirementsApi.getProjectRequirements(props.projectId)
      searchResults.value = resp.data.requirements || []
    } catch {
      searchResults.value = []
    }
    return
  }
  try {
    const resp = await requirementsApi.search(props.projectId, searchQuery.value, 20)
    searchResults.value = resp.data.results || []
  } catch {
    searchResults.value = []
  }
}

watch(showLinkDialog, (val) => {
  if (val) {
    searchQuery.value = ''
    selectedReqs.value = []
    handleSearch()
  }
})

async function handleLink() {
  try {
    const ids = selectedReqs.value.map(r => r.id)
    await requirementsApi.linkRequirements(props.sectionId, ids)
    showLinkDialog.value = false
    await loadRequirements()
    ElMessage.success(`已關聯 ${ids.length} 個需求`)
  } catch {
    ElMessage.error('關聯失敗')
  }
}

function getTypeTagType(type) {
  const map = {
    functional: '',
    technical: 'success',
    security: 'danger',
    management: 'warning',
    qualification: 'info',
    deliverable: '',
    timeline: 'warning',
    other: 'info'
  }
  return map[type] || 'info'
}

function getTypeLabel(type) {
  const map = {
    functional: '功能',
    technical: '技術',
    security: '資安',
    management: '管理',
    qualification: '資格',
    deliverable: '交付',
    timeline: '時程',
    other: '其他'
  }
  return map[type] || type
}

function getPriorityType(priority) {
  const map = { high: 'danger', medium: 'warning', low: 'info' }
  return map[priority] || 'info'
}

function getPriorityLabel(priority) {
  const map = { high: '高', medium: '中', low: '低' }
  return map[priority] || priority
}
</script>
