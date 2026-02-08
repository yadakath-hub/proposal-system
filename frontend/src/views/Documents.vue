<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">文件管理</h1>
      <el-select v-model="selectedProjectId" placeholder="選擇專案" class="w-64">
        <el-option
          v-for="project in projects"
          :key="project.id"
          :label="project.name"
          :value="project.id"
        />
      </el-select>
    </div>

    <el-card v-if="selectedProjectId" class="mb-6">
      <template #header>上傳文件</template>
      <DocumentUpload :project-id="selectedProjectId" @uploaded="fetchDocuments" />
    </el-card>

    <el-card v-if="selectedProjectId">
      <template #header>
        <div class="flex justify-between items-center">
          <span>文件列表</span>
          <el-button text :icon="Refresh" @click="fetchDocuments">重新整理</el-button>
        </div>
      </template>
      <DocumentTable
        :documents="documents"
        :loading="loading"
        @refresh="fetchDocuments"
      />
    </el-card>

    <el-empty v-if="!selectedProjectId" description="請先選擇專案" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import { documentApi } from '@/api/documents'
import DocumentUpload from '@/components/document/DocumentUpload.vue'
import DocumentTable from '@/components/document/DocumentTable.vue'
import { Refresh } from '@element-plus/icons-vue'

const projectStore = useProjectStore()

const selectedProjectId = ref(null)
const documents = ref([])
const loading = ref(false)
const projects = ref([])

async function fetchProjects() {
  await projectStore.fetchProjects()
  projects.value = projectStore.projects
}

async function fetchDocuments() {
  if (!selectedProjectId.value) return

  loading.value = true
  try {
    const response = await documentApi.getDocuments(selectedProjectId.value)
    documents.value = response.data || []
  } catch {
    documents.value = []
  } finally {
    loading.value = false
  }
}

watch(selectedProjectId, () => {
  fetchDocuments()
})

onMounted(() => {
  fetchProjects()
})
</script>
