<template>
  <div class="page-container">
    <!-- Page header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">專案管理</h1>
        <p class="page-subtitle">管理您的建議書專案</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">
        新增專案
      </el-button>
    </div>

    <!-- Search & filter -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-row">
        <el-input
          v-model="filters.search"
          placeholder="搜尋專案名稱..."
          :prefix-icon="Search"
          clearable
          class="search-input"
          @input="debouncedFetch"
        />
        <el-select v-model="filters.status" placeholder="狀態" clearable class="status-select" @change="fetchData">
          <el-option label="草稿" value="Draft" />
          <el-option label="進行中" value="InProgress" />
          <el-option label="已完成" value="Completed" />
          <el-option label="已封存" value="Archived" />
        </el-select>
        <el-button :icon="Refresh" @click="fetchData">重新整理</el-button>
      </div>
    </el-card>

    <!-- Project grid -->
    <div v-loading="loading" class="projects-grid">
      <ProjectCard
        v-for="project in filteredProjects"
        :key="project.id"
        :project="project"
        @click="goToProject(project)"
        @edit="showEditDialog(project)"
        @delete="confirmDelete(project)"
      />

      <!-- Add card -->
      <el-card class="add-card" shadow="hover" @click="showCreateDialog">
        <div class="add-card-content">
          <el-icon :size="40" class="add-icon"><Plus /></el-icon>
          <span>新增專案</span>
        </div>
      </el-card>
    </div>

    <el-empty v-if="!loading && filteredProjects.length === 0" description="尚無專案">
      <el-button type="primary" @click="showCreateDialog">建立第一個專案</el-button>
    </el-empty>

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

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 4px 0 0;
}

.filter-card {
  margin-bottom: 20px;
  border: 1px solid var(--border-color);
}

.filter-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.search-input {
  width: 280px;
}

.status-select {
  width: 130px;
}

.projects-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
}

@media (min-width: 1536px) {
  .projects-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* Add card */
.add-card {
  cursor: pointer;
  border: 2px dashed #d9d9d9;
  background: #fafafa;
  transition: all 0.3s ease;
  min-height: 180px;
}

.add-card:hover {
  border-color: var(--primary-color);
  background: #e6f7ff;
}

.add-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 140px;
  color: var(--text-secondary);
  gap: 8px;
  font-size: 14px;
}

.add-card:hover .add-card-content {
  color: var(--primary-color);
}
</style>
