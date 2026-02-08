<template>
  <div
    class="document-upload border-2 border-dashed rounded-lg p-8 text-center transition-colors"
    :class="isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <el-icon :size="48" class="text-gray-400 mb-4"><UploadFilled /></el-icon>
    <p class="text-gray-600 mb-2">拖放文件到此處，或</p>
    <el-upload
      :auto-upload="false"
      :show-file-list="false"
      :on-change="handleFileChange"
      accept=".pdf,.docx,.doc,.xlsx,.xls"
      multiple
    >
      <el-button type="primary">選擇文件</el-button>
    </el-upload>
    <p class="text-xs text-gray-400 mt-2">支援 PDF、Word、Excel 文件</p>

    <div v-if="uploadingFiles.length > 0" class="mt-4 text-left">
      <div
        v-for="file in uploadingFiles"
        :key="file.name"
        class="flex items-center gap-2 mb-2"
      >
        <el-icon><Document /></el-icon>
        <span class="flex-1 truncate">{{ file.name }}</span>
        <el-progress
          :percentage="file.progress"
          :status="file.status"
          :stroke-width="6"
          class="w-24"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { documentApi } from '@/api/documents'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document } from '@element-plus/icons-vue'

const props = defineProps({
  projectId: { type: String, required: true }
})

const emit = defineEmits(['uploaded'])

const isDragging = ref(false)
const uploadingFiles = ref([])

function handleDrop(e) {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files)
  uploadFiles(files)
}

function handleFileChange(uploadFile) {
  uploadFiles([uploadFile.raw])
}

async function uploadFiles(files) {
  for (const file of files) {
    const fileInfo = { name: file.name, progress: 0, status: '' }
    uploadingFiles.value.push(fileInfo)

    try {
      await documentApi.upload(props.projectId, file, (progress) => {
        fileInfo.progress = progress
      })
      fileInfo.progress = 100
      fileInfo.status = 'success'
      ElMessage.success(`${file.name} 上傳成功`)
      emit('uploaded')
    } catch {
      fileInfo.status = 'exception'
      ElMessage.error(`${file.name} 上傳失敗`)
    }
  }

  setTimeout(() => {
    uploadingFiles.value = uploadingFiles.value.filter(f => f.status !== 'success')
  }, 2000)
}
</script>
