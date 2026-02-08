<template>
  <div class="p-6" v-loading="loading">
    <!-- Back + project title -->
    <div class="flex items-center gap-4 mb-6">
      <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
      <div class="flex-1">
        <h1 class="text-2xl font-bold">{{ project?.name }}</h1>
        <p class="text-gray-500">{{ project?.description }}</p>
      </div>
      <el-dropdown trigger="click">
        <el-button :icon="More">操作</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :icon="Edit" @click="showEditProject">編輯專案</el-dropdown-item>
            <el-dropdown-item :icon="Download" @click="showExportDialog">匯出建議書</el-dropdown-item>
            <el-dropdown-item :icon="Delete" divided @click="confirmDeleteProject">
              刪除專案
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- Project info cards -->
    <el-row :gutter="20" class="mb-6">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="章節數" :value="sections.length" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="Token 用量" :value="project?.used_tokens || 0" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="截止日期" :value="deadlineText" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #title>
            <span class="text-sm text-gray-500">狀態</span>
          </template>
          <el-tag :type="statusType" size="large">{{ statusText }}</el-tag>
        </el-card>
      </el-col>
    </el-row>

    <!-- 進入編輯器按鈕 -->
    <el-card class="mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="font-bold text-lg">建議書編輯器</h3>
          <p class="text-gray-500 text-sm mt-1">三欄式專業編輯介面，支援章節樹瀏覽、即時編輯與內容預覽</p>
        </div>
        <el-button type="primary" size="large" @click="enterEditor">
          <el-icon class="mr-2"><Edit /></el-icon>
          進入建議書編輯器
        </el-button>
      </div>
    </el-card>

    <!-- Section list -->
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <span class="font-bold">章節列表</span>
          <el-button type="primary" :icon="Plus" @click="showCreateSection">
            新增章節
          </el-button>
        </div>
      </template>

      <SectionList
        :sections="sections"
        @edit="showEditSection"
        @delete="confirmDeleteSection"
        @click="goToSection"
        @reorder="handleReorder"
      />

      <el-empty v-if="sections.length === 0" description="尚無章節">
        <el-button type="primary" @click="showCreateSection">建立第一個章節</el-button>
      </el-empty>
    </el-card>

    <!-- Project edit dialog -->
    <ProjectForm
      v-model:visible="projectDialogVisible"
      :project="project"
      @saved="onProjectSaved"
    />

    <!-- Section edit dialog -->
    <SectionForm
      v-model:visible="sectionDialogVisible"
      :section="editingSection"
      :projectId="projectId"
      @saved="onSectionSaved"
    />

    <!-- Export dialog -->
    <ExportDialog
      v-model:visible="exportDialogVisible"
      :projectId="projectId"
      :sections="sections"
      @exported="fetchData"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'
import ProjectForm from '@/components/project/ProjectForm.vue'
import SectionList from '@/components/section/SectionList.vue'
import SectionForm from '@/components/section/SectionForm.vue'
import ExportDialog from '@/components/export/ExportDialog.vue'
import { ArrowLeft, Plus, Edit, Delete, Download, More } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.projectId)
const loading = ref(false)
const projectDialogVisible = ref(false)
const sectionDialogVisible = ref(false)
const editingSection = ref(null)
const exportDialogVisible = ref(false)

const project = computed(() => projectStore.currentProject)
const sections = computed(() => projectStore.sortedSections)

const STATUS_MAP = {
  Draft: { text: '草稿', type: 'info' },
  InProgress: { text: '進行中', type: 'warning' },
  Completed: { text: '已完成', type: 'success' },
  Archived: { text: '已封存', type: '' }
}

const statusType = computed(() => STATUS_MAP[project.value?.status]?.type || 'info')
const statusText = computed(() => STATUS_MAP[project.value?.status]?.text || project.value?.status)

const deadlineText = computed(() => {
  if (!project.value?.deadline) return '未設定'
  return new Date(project.value.deadline).toLocaleDateString('zh-TW')
})

async function fetchData() {
  loading.value = true
  try {
    await projectStore.fetchProject(projectId.value)
    await projectStore.fetchSections(projectId.value)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/projects')
}

function showEditProject() {
  projectDialogVisible.value = true
}

function showCreateSection() {
  editingSection.value = null
  sectionDialogVisible.value = true
}

function showEditSection(section) {
  editingSection.value = { ...section }
  sectionDialogVisible.value = true
}

async function confirmDeleteSection(section) {
  try {
    await ElMessageBox.confirm(
      `確定要刪除章節「${section.title}」嗎？`,
      '刪除確認',
      { type: 'warning' }
    )
    await projectStore.deleteSection(section.id)
    ElMessage.success('章節已刪除')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('刪除失敗')
  }
}

async function confirmDeleteProject() {
  try {
    await ElMessageBox.confirm(
      `確定要刪除專案「${project.value?.name}」嗎？此操作無法復原。`,
      '刪除確認',
      { type: 'warning' }
    )
    await projectStore.deleteProject(projectId.value)
    ElMessage.success('專案已刪除')
    router.push('/projects')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('刪除失敗')
  }
}

function goToSection(section) {
  router.push(`/projects/${projectId.value}/sections/${section.id}`)
}

async function handleReorder(items) {
  try {
    await projectStore.reorderSections(items)
    ElMessage.success('排序已更新')
  } catch {
    ElMessage.error('排序更新失敗')
    fetchData()
  }
}

function onProjectSaved() {
  fetchData()
}

function onSectionSaved() {
  projectStore.fetchSections(projectId.value)
}

function showExportDialog() {
  exportDialogVisible.value = true
}

function enterEditor() {
  router.push(`/projects/${projectId.value}/editor`)
}

onMounted(() => {
  fetchData()
})

watch(projectId, () => {
  if (projectId.value) fetchData()
})
</script>
