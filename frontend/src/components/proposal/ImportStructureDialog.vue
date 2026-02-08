<template>
  <el-dialog
    :model-value="visible"
    title="匯入章節架構"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <!-- 步驟指示器 -->
    <el-steps :active="currentStep" finish-status="success" class="mb-6">
      <el-step title="選擇來源" />
      <el-step title="AI 解析" />
      <el-step title="確認匯入" />
    </el-steps>

    <!-- 步驟 1: 選擇來源 -->
    <div v-show="currentStep === 0">
      <el-tabs v-model="sourceType" class="mb-4">
        <el-tab-pane label="上傳截圖" name="image">
          <div
            class="upload-area border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
            :class="dragover ? 'border-blue-500 bg-blue-50' : 'border-gray-300'"
            @click="triggerUpload('image')"
            @dragover.prevent="dragover = true"
            @dragleave="dragover = false"
            @drop.prevent="handleDrop"
          >
            <input
              ref="imageInputRef"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleFileSelect"
            />

            <template v-if="!previewUrl">
              <el-icon :size="48" class="text-gray-400 mb-4"><Picture /></el-icon>
              <p class="text-gray-600">拖放招標文件截圖到此處，或點擊選擇</p>
              <p class="text-gray-400 text-sm mt-2">支援 PNG、JPG、GIF 格式</p>
            </template>

            <template v-else>
              <img :src="previewUrl" class="max-h-64 mx-auto rounded" />
              <el-button class="mt-4" @click.stop="clearFile">重新選擇</el-button>
            </template>
          </div>
        </el-tab-pane>

        <el-tab-pane label="上傳 PDF" name="pdf">
          <div
            class="upload-area border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-blue-500"
            @click="triggerUpload('pdf')"
          >
            <input
              ref="pdfInputRef"
              type="file"
              accept=".pdf"
              class="hidden"
              @change="handleFileSelect"
            />

            <template v-if="!selectedFile || sourceType !== 'pdf'">
              <el-icon :size="48" class="text-gray-400 mb-4"><Document /></el-icon>
              <p class="text-gray-600">點擊選擇招標文件 PDF</p>
            </template>

            <template v-else>
              <el-icon :size="48" class="text-green-500 mb-4"><DocumentChecked /></el-icon>
              <p class="text-gray-800 font-medium">{{ selectedFile.name }}</p>
              <p class="text-gray-400 text-sm">{{ formatFileSize(selectedFile.size) }}</p>
              <el-button class="mt-4" @click.stop="clearFile">重新選擇</el-button>
            </template>
          </div>
        </el-tab-pane>

        <el-tab-pane label="貼上文字" name="text">
          <el-input
            v-model="textContent"
            type="textarea"
            :rows="10"
            placeholder="請貼上招標文件中的章節架構文字，例如：

1. 專案說明
  1.1 專案背景
  1.2 專案目標
2. 技術規劃
  2.1 系統架構
  2.2 技術規格
..."
          />
        </el-tab-pane>

        <el-tab-pane label="使用範本" name="template">
          <div v-loading="loadingTemplates">
            <div
              v-for="template in templates"
              :key="template.id"
              class="template-card border rounded-lg p-4 mb-3 cursor-pointer hover:border-blue-500 transition-colors"
              :class="selectedTemplate === template.id ? 'border-blue-500 bg-blue-50' : ''"
              @click="selectedTemplate = template.id"
            >
              <div class="flex items-center gap-3">
                <el-radio :model-value="selectedTemplate" :value="template.id" />
                <div>
                  <p class="font-medium">{{ template.name }}</p>
                  <p class="text-sm text-gray-500">{{ template.sections.length }} 個章節</p>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 步驟 2: AI 解析中 -->
    <div v-show="currentStep === 1" class="text-center py-8">
      <el-icon :size="64" class="text-blue-500 mb-4 is-loading"><Loading /></el-icon>
      <p class="text-lg font-medium">AI 正在解析章節架構...</p>
      <p class="text-gray-500 mt-2">這可能需要 10-30 秒，請稍候</p>
    </div>

    <!-- 步驟 3: 確認匯入 -->
    <div v-show="currentStep === 2">
      <el-alert
        v-if="parsedSections.length > 0"
        :title="`成功解析出 ${parsedSections.length} 個章節`"
        type="success"
        show-icon
        class="mb-4"
      />

      <el-alert
        v-else
        title="未能解析出章節，請檢查上傳的內容"
        type="warning"
        show-icon
        class="mb-4"
      />

      <!-- 章節預覽與編輯 -->
      <div class="max-h-96 overflow-auto border rounded-lg">
        <el-table :data="parsedSections" size="small">
          <el-table-column label="編號" width="100">
            <template #default="{ row }">
              <el-input v-model="row.chapter_number" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="標題" min-width="200">
            <template #default="{ row }">
              <div :style="{ paddingLeft: `${row.depth_level * 20}px` }">
                <el-input v-model="row.title" size="small" />
              </div>
            </template>
          </el-table-column>
          <el-table-column label="層級" width="80">
            <template #default="{ row }">
              <el-tag size="small">L{{ row.depth_level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ $index }">
              <el-button
                text
                type="danger"
                size="small"
                :icon="Delete"
                @click="removeSection($index)"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 新增章節 -->
      <div class="mt-4 flex gap-2 items-center">
        <el-button :icon="Plus" @click="addSection">新增章節</el-button>
        <el-checkbox v-model="clearExisting" class="ml-4">
          清除現有章節（全部取代）
        </el-checkbox>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-between">
        <el-button v-if="currentStep > 0 && currentStep !== 1" @click="prevStep">上一步</el-button>
        <div v-else></div>

        <div>
          <el-button @click="handleClose">取消</el-button>
          <el-button
            v-if="currentStep === 0"
            type="primary"
            :disabled="!canProceed"
            @click="startParse"
          >
            開始解析
          </el-button>
          <el-button
            v-if="currentStep === 2"
            type="primary"
            :disabled="parsedSections.length === 0"
            :loading="importing"
            @click="handleImport"
          >
            確認匯入 ({{ parsedSections.length }} 個章節)
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { structureApi } from '@/api/structure'
import { ElMessage } from 'element-plus'
import { Picture, Document, DocumentChecked, Loading, Delete, Plus } from '@element-plus/icons-vue'

const props = defineProps({
  visible: Boolean,
  projectId: [String, Number]
})

const emit = defineEmits(['update:visible', 'imported'])

// State
const currentStep = ref(0)
const sourceType = ref('image')
const selectedFile = ref(null)
const previewUrl = ref(null)
const textContent = ref('')
const selectedTemplate = ref(null)
const templates = ref([])
const loadingTemplates = ref(false)
const dragover = ref(false)

const parsedSections = ref([])
const clearExisting = ref(false)
const importing = ref(false)

// Refs
const imageInputRef = ref()
const pdfInputRef = ref()

// Computed
const canProceed = computed(() => {
  switch (sourceType.value) {
    case 'image':
      return !!selectedFile.value && selectedFile.value.type?.startsWith('image/')
    case 'pdf':
      return !!selectedFile.value
    case 'text':
      return textContent.value.trim().length > 10
    case 'template':
      return !!selectedTemplate.value
    default:
      return false
  }
})

// Load templates
async function loadTemplates() {
  loadingTemplates.value = true
  try {
    const response = await structureApi.getTemplates()
    templates.value = response.data
  } catch {
    console.error('Failed to load templates')
  } finally {
    loadingTemplates.value = false
  }
}

// File handling
function triggerUpload(type) {
  if (type === 'image') {
    imageInputRef.value?.click()
  } else {
    pdfInputRef.value?.click()
  }
}

function handleFileSelect(e) {
  const file = e.target.files?.[0]
  if (!file) return

  selectedFile.value = file

  if (file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (ev) => {
      previewUrl.value = ev.target.result
    }
    reader.readAsDataURL(file)
  }
}

function handleDrop(e) {
  dragover.value = false
  const file = e.dataTransfer.files?.[0]
  if (file && file.type.startsWith('image/')) {
    selectedFile.value = file
    const reader = new FileReader()
    reader.onload = (ev) => {
      previewUrl.value = ev.target.result
    }
    reader.readAsDataURL(file)
  }
}

function clearFile() {
  selectedFile.value = null
  previewUrl.value = null
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// Parse
async function startParse() {
  currentStep.value = 1

  try {
    if (sourceType.value === 'template') {
      const template = templates.value.find(t => t.id === selectedTemplate.value)
      if (template) {
        parsedSections.value = template.sections.map(s => ({ ...s }))
        currentStep.value = 2
        return
      }
    }

    let response
    if (sourceType.value === 'image' || sourceType.value === 'pdf') {
      response = await structureApi.parse(
        props.projectId,
        sourceType.value,
        selectedFile.value
      )
    } else if (sourceType.value === 'text') {
      response = await structureApi.parse(
        props.projectId,
        'text',
        null,
        textContent.value
      )
    }

    if (response.data.success) {
      parsedSections.value = response.data.sections
      currentStep.value = 2
    } else {
      throw new Error(response.data.message || '解析失敗')
    }
  } catch (e) {
    ElMessage.error('解析失敗: ' + (e.response?.data?.detail || e.message))
    currentStep.value = 0
  }
}

// Edit sections
function addSection() {
  const lastSection = parsedSections.value[parsedSections.value.length - 1]
  const newNumber = lastSection
    ? String(parseInt(lastSection.chapter_number.split('.')[0]) + 1)
    : '1'

  parsedSections.value.push({
    chapter_number: newNumber,
    title: '新章節',
    depth_level: 0
  })
}

function removeSection(index) {
  parsedSections.value.splice(index, 1)
}

// Import
async function handleImport() {
  importing.value = true

  try {
    const response = await structureApi.import(
      props.projectId,
      parsedSections.value,
      clearExisting.value
    )

    if (response.data.success) {
      ElMessage.success(response.data.message)
      emit('imported')
      handleClose()
    } else {
      throw new Error(response.data.message)
    }
  } catch (e) {
    ElMessage.error('匯入失敗: ' + (e.response?.data?.detail || e.message))
  } finally {
    importing.value = false
  }
}

// Navigation
function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function handleClose() {
  currentStep.value = 0
  selectedFile.value = null
  previewUrl.value = null
  textContent.value = ''
  selectedTemplate.value = null
  parsedSections.value = []
  clearExisting.value = false
  emit('update:visible', false)
}

// Watch for dialog open
watch(() => props.visible, (val) => {
  if (val) {
    loadTemplates()
  }
})
</script>

<style scoped>
.upload-area {
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
