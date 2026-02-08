<template>
  <div class="p-6">
    <!-- Page title + actions -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">專案管理</h1>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">
        新增專案
      </el-button>
    </div>

    <!-- Search & filter -->
    <el-card class="mb-6">
      <div class="flex flex-wrap gap-4">
        <el-input
          v-model="filters.search"
          placeholder="搜尋專案名稱..."
          :prefix-icon="Search"
          clearable
          class="w-64"
          @input="debouncedFetch"
        />
        <el-select v-model="filters.status" placeholder="狀態" clearable class="w-32" @change="fetchData">
          <el-option label="草稿" value="Draft" />
          <el-option label="進行中" value="InProgress" />
          <el-option label="已完成" value="Completed" />
          <el-option label="已封存" value="Archived" />
        </el-select>
        <el-button :icon="Refresh" @click="fetchData">重新整理</el-button>
      </div>
    </el-card>

    <!-- Project grid -->
    <div v-loading="loading">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ProjectCard
          v-for="project in filteredProjects"
          :key="project.id"
          :project="project"
          @click="goToProject(project)"
          @edit="showEditDialog(project)"
          @delete="confirmDelete(project)"
        />
      </div>

      <el-empty v-if="!loading && filteredProjects.length === 0" description="尚無專案">
        <el-button type="primary" @click="showCreateDialog">建立第一個專案</el-button>
      </el-empty>
    </div>

    <!-- Create/Edit Dialog -->
    <ProjectForm
      v-model:visible="dialogVisible"
      :project="editingProject"
      @saved="onProjectSaved"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'
import ProjectCard from '@/components/project/ProjectCard.vue'
import ProjectForm from '@/components/project/ProjectForm.vue'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { useDebounceFn } from '@vueuse/core'

const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)
const dialogVisible = ref(false)
const editingProject = ref(null)

const filters = reactive({
  search: '',
  status: ''
})

const filteredProjects = computed(() => {
  let list = projectStore.projects
  if (filters.search) {
    const q = filters.search.toLowerCase()
    list = list.filter(p => p.name.toLowerCase().includes(q))
  }
  if (filters.status) {
    list = list.filter(p => p.status === filters.status)
  }
  return list
})

const debouncedFetch = useDebounceFn(() => {
  // Client-side filtering; no server call needed
}, 300)

async function fetchData() {
  loading.value = true
  try {
    await projectStore.fetchProjects()
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  editingProject.value = null
  dialogVisible.value = true
}

function showEditDialog(project) {
  editingProject.value = { ...project }
  dialogVisible.value = true
}

async function confirmDelete(project) {
  try {
    await ElMessageBox.confirm(
      `確定要刪除專案「${project.name}」嗎？此操作無法復原。`,
      '刪除確認',
      { type: 'warning', confirmButtonText: '刪除', cancelButtonText: '取消' }
    )
    await projectStore.deleteProject(project.id)
    ElMessage.success('專案已刪除')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('刪除失敗')
  }
}

function onProjectSaved() {
  fetchData()
}

function goToProject(project) {
  router.push(`/projects/${project.id}`)
}

onMounted(() => {
  fetchData()
})
</script>
