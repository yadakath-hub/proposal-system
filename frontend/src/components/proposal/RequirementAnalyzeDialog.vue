<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="招標需求分析"
    width="800px"
    :close-on-click-modal="false"
  >
    <!-- Step 1: Select document -->
    <div v-if="step === 1">
      <el-alert type="info" :closable="false" class="mb-4">
        選擇一份已上傳的招標文件，AI 將自動分析並提取需求項目，並嘗試對應至現有章節。
      </el-alert>

      <el-form label-position="top">
        <el-form-item label="選擇招標文件">
          <el-select
            v-model="selectedDocumentId"
            placeholder="請選擇文件"
            class="w-full"
            :loading="loadingDocs"
          >
            <el-option
              v-for="doc in documents"
              :key="doc.id"
              :label="doc.original_name || doc.file_name"
              :value="doc.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="autoLink">自動關聯至對應章節</el-checkbox>
        </el-form-item>
      </el-form>
    </div>

    <!-- Step 2: Analyzing -->
    <div v-else-if="step === 2" class="text-center py-8">
      <el-icon class="is-loading mb-4" :size="48" color="#409EFF"><Loading /></el-icon>
      <p class="text-lg font-medium">AI 正在分析招標文件...</p>
      <p class="text-gray-400 mt-2">這可能需要 30-60 秒，請耐心等候</p>
    </div>

    <!-- Step 3: Results -->
    <div v-else-if="step === 3">
      <el-alert v-if="analysisResult" type="success" :closable="false" class="mb-4">
        <template #title>
          分析完成 — 共提取 {{ analysisResult.total_requirements }} 個需求
        </template>
        <p v-if="analysisResult.summary">{{ analysisResult.summary }}</p>
      </el-alert>

      <!-- Key points -->
      <div v-if="analysisResult?.key_points?.length" class="mb-4">
        <h4 class="font-medium mb-2">重點摘要</h4>
        <ul class="list-disc list-inside text-sm text-gray-600 space-y-1">
          <li v-for="(point, i) in analysisResult.key_points" :key="i">{{ point }}</li>
        </ul>
      </div>

      <!-- Requirements table -->
      <el-table
        :data="analysisResult?.requirements || []"
        max-height="400"
        size="small"
        stripe
      >
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column prop="content" label="需求內容" min-width="200" show-overflow-tooltip />
        <el-table-column label="類型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getTypeTagType(row.requirement_type)">
              {{ getTypeLabel(row.requirement_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="優先級" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getPriorityType(row.priority)">
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="suggested_section" label="建議章節" width="100" />
      </el-table>
    </div>

    <!-- Error state -->
    <div v-else-if="step === 4" class="text-center py-8">
      <el-icon :size="48" color="#F56C6C"><CircleCloseFilled /></el-icon>
      <p class="text-lg font-medium mt-4">分析失敗</p>
      <p class="text-gray-400 mt-2">{{ errorMessage }}</p>
    </div>

    <template #footer>
      <div class="flex justify-between">
        <div>
          <el-button v-if="step === 3 || step === 4" @click="resetDialog">
            重新分析
          </el-button>
        </div>
        <div class="flex gap-2">
          <el-button @click="$emit('update:visible', false)">
            {{ step === 3 ? '關閉' : '取消' }}
          </el-button>
          <el-button
            v-if="step === 1"
            type="primary"
            :disabled="!selectedDocumentId"
            @click="startAnalysis"
          >
            開始分析
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Loading, CircleCloseFilled } from '@element-plus/icons-vue'
import { requirementsApi } from '@/api/requirements'
import api from '@/api/index'

const props = defineProps({
  visible: Boolean,
  projectId: [String, Object]
})

const emit = defineEmits(['update:visible', 'analyzed'])

const step = ref(1)
const documents = ref([])
const loadingDocs = ref(false)
const selectedDocumentId = ref(null)
const autoLink = ref(true)
const analysisResult = ref(null)
const errorMessage = ref('')

watch(() => props.visible, async (val) => {
  if (val) {
    resetDialog()
    await loadDocuments()
  }
})

async function loadDocuments() {
  loadingDocs.value = true
  try {
    const resp = await api.get(`/api/v1/documents/project/${props.projectId}`)
    documents.value = resp.data.documents || resp.data || []
  } catch {
    documents.value = []
  } finally {
    loadingDocs.value = false
  }
}

async function startAnalysis() {
  step.value = 2
  try {
    const resp = await requirementsApi.analyze(
      props.projectId,
      selectedDocumentId.value,
      autoLink.value
    )
    analysisResult.value = resp.data
    step.value = 3
    emit('analyzed', resp.data)
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || '分析過程中發生錯誤'
    step.value = 4
  }
}

function resetDialog() {
  step.value = 1
  analysisResult.value = null
  errorMessage.value = ''
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
