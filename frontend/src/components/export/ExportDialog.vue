<template>
  <el-dialog
    :model-value="visible"
    title="匯出建議書"
    width="500px"
    @close="$emit('update:visible', false)"
  >
    <el-form label-width="100px">
      <el-form-item label="匯出格式">
        <el-radio-group v-model="form.format">
          <el-radio-button value="docx">
            <el-icon class="mr-1"><Document /></el-icon>
            DOCX
          </el-radio-button>
          <el-radio-button value="pdf">
            <el-icon class="mr-1"><Document /></el-icon>
            PDF
          </el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="匯出範圍">
        <el-radio-group v-model="form.scope">
          <el-radio value="all">全部章節</el-radio>
          <el-radio value="selected">選擇章節</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="form.scope === 'selected'" label="選擇章節">
        <el-checkbox-group v-model="form.sectionIds">
          <el-checkbox
            v-for="section in sections"
            :key="section.id"
            :value="section.id"
          >
            {{ section.chapter_number }} {{ section.title }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <el-form-item label="包含選項">
        <el-checkbox v-model="form.includeToc">自動目錄</el-checkbox>
        <el-checkbox v-model="form.includeCover">封面頁</el-checkbox>
      </el-form-item>

      <el-form-item label="公司名稱">
        <el-input v-model="form.companyName" placeholder="封面頁顯示的公司名稱" />
      </el-form-item>
    </el-form>

    <!-- Export progress -->
    <div v-if="exporting" class="mt-4">
      <el-progress :percentage="progress" :status="progressStatus" />
      <p class="text-sm text-gray-500 mt-2 text-center">{{ statusText }}</p>
    </div>

    <!-- Export result -->
    <div v-if="exportResult" class="mt-4 p-3 bg-green-50 rounded-lg text-sm">
      <p>匯出完成！</p>
      <p>格式: {{ exportResult.file_format.toUpperCase() }} | 大小: {{ formatSize(exportResult.file_size) }} | 頁數: {{ exportResult.page_count }}</p>
      <p>耗時: {{ exportResult.export_time_ms }}ms</p>
    </div>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">關閉</el-button>
      <el-button
        type="primary"
        :loading="exporting"
        :disabled="form.scope === 'selected' && form.sectionIds.length === 0"
        @click="handleExport"
      >
        開始匯出
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { exportApi } from '@/api/exports'
import { ElMessage } from 'element-plus'
import { Document } from '@element-plus/icons-vue'

const props = defineProps({
  visible: Boolean,
  projectId: String,
  sections: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible', 'exported'])

const form = reactive({
  format: 'docx',
  scope: 'all',
  sectionIds: [],
  includeToc: true,
  includeCover: true,
  companyName: ''
})

const exporting = ref(false)
const progress = ref(0)
const progressStatus = ref('')
const statusText = ref('')
const exportResult = ref(null)

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

async function handleExport() {
  exporting.value = true
  exportResult.value = null
  progress.value = 30
  statusText.value = '正在生成文件...'

  try {
    const response = await exportApi.startExport({
      project_id: props.projectId,
      format: form.format,
      section_ids: form.scope === 'selected' ? form.sectionIds : null,
      include_toc: form.includeToc,
      include_cover: form.includeCover,
      company_name: form.companyName
    })

    const result = response.data
    exportResult.value = result
    progress.value = 100
    progressStatus.value = 'success'
    statusText.value = '匯出完成！正在下載...'

    // Download the file via blob
    const downloadResp = await exportApi.downloadExport(result.id)
    const url = window.URL.createObjectURL(downloadResp.data)
    const a = document.createElement('a')
    a.href = url
    a.download = result.file_name
    a.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('匯出並下載完成')
    emit('exported')
  } catch (e) {
    ElMessage.error('匯出失敗: ' + (e.response?.data?.detail || e.message))
    progressStatus.value = 'exception'
    statusText.value = '匯出失敗'
  } finally {
    exporting.value = false
  }
}

watch(() => props.visible, (val) => {
  if (val) {
    form.sectionIds = []
    progress.value = 0
    progressStatus.value = ''
    statusText.value = ''
    exportResult.value = null
  }
})
</script>
