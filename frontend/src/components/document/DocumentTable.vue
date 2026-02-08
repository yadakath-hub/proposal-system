<template>
  <div class="document-list">
    <el-table :data="documents" v-loading="loading">
      <el-table-column label="檔案名稱" min-width="200">
        <template #default="{ row }">
          <div class="flex items-center gap-2">
            <el-icon :size="20"><Document /></el-icon>
            <span>{{ row.original_filename }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="大小" width="100">
        <template #default="{ row }">
          {{ formatSize(row.file_size) }}
        </template>
      </el-table-column>

      <el-table-column label="狀態" width="120">
        <template #default="{ row }">
          <el-tag :type="row.is_parsed ? 'success' : 'info'" size="small">
            {{ row.is_parsed ? `已處理 (${row.chunk_count} 段)` : '待處理' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="上傳時間" width="160">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="!row.is_parsed"
            text
            size="small"
            type="primary"
            :loading="row._processing"
            @click="handleProcess(row)"
          >
            處理
          </el-button>
          <el-button text size="small" @click="handleDownload(row)">
            下載
          </el-button>
          <el-button text size="small" type="danger" @click="handleDelete(row)">
            刪除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && documents.length === 0" description="尚無文件" />
  </div>
</template>

<script setup>
import { documentApi } from '@/api/documents'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document } from '@element-plus/icons-vue'

defineProps({
  documents: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['refresh'])

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-TW')
}

async function handleProcess(doc) {
  doc._processing = true
  try {
    await documentApi.processDocument(doc.id)
    ElMessage.success('文件處理完成')
    emit('refresh')
  } catch (e) {
    ElMessage.error('處理失敗: ' + (e.response?.data?.detail || e.message))
  } finally {
    doc._processing = false
  }
}

async function handleDownload(doc) {
  try {
    const response = await documentApi.downloadDocument(doc.id)
    const url = window.URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = doc.original_filename
    a.click()
    window.URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下載失敗')
  }
}

async function handleDelete(doc) {
  try {
    await ElMessageBox.confirm(`確定要刪除「${doc.original_filename}」嗎？`, '刪除確認', {
      type: 'warning'
    })
    await documentApi.deleteDocument(doc.id)
    ElMessage.success('文件已刪除')
    emit('refresh')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('刪除失敗')
  }
}
</script>
