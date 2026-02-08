<template>
  <div class="h-full flex flex-col" v-loading="loading">
    <!-- Toolbar -->
    <div class="bg-white border-b px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <div>
          <h1 class="text-lg font-bold">
            {{ section?.chapter_number }} {{ section?.title }}
          </h1>
          <p class="text-sm text-gray-500">{{ project?.name }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <el-tag v-if="hasUnsavedChanges" type="warning" size="small">未儲存</el-tag>
        <el-tag v-else type="success" size="small">已儲存</el-tag>
        <el-button type="primary" :loading="saving" @click="saveContent">
          <el-icon class="mr-1"><Check /></el-icon>
          儲存
        </el-button>
      </div>
    </div>

    <!-- Editor area -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left: content editor -->
      <div class="flex-1 p-4 overflow-auto">
        <el-card class="h-full">
          <template #header>
            <div class="flex justify-between items-center">
              <span>內容編輯</span>
              <div class="text-sm text-gray-500">
                {{ contentLength }} 字
              </div>
            </div>
          </template>
          <el-input
            v-model="content"
            type="textarea"
            :rows="25"
            placeholder="在此輸入章節內容..."
            @input="onContentChange"
          />
        </el-card>
      </div>

      <!-- Right: AI assistant panel + version history -->
      <div class="w-96 border-l bg-gray-50 p-4 overflow-auto">
        <el-card>
          <template #header>
            <div class="flex items-center gap-2">
              <el-icon><MagicStick /></el-icon>
              <span>AI 助手</span>
            </div>
          </template>
          <el-empty description="AI 助手功能將在 Phase 7-3 實作" :image-size="80" />
        </el-card>

        <!-- Version history -->
        <el-card class="mt-4">
          <template #header>
            <div class="flex items-center gap-2">
              <el-icon><Clock /></el-icon>
              <span>版本歷史</span>
            </div>
          </template>
          <el-timeline v-if="versions.length > 0">
            <el-timeline-item
              v-for="version in versions.slice(0, 5)"
              :key="version.id"
              :timestamp="formatDate(version.created_at)"
              placement="top"
            >
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-medium">版本 {{ version.version_number }}</p>
                  <p class="text-xs text-gray-500">{{ version.source_type }}</p>
                </div>
                <el-button
                  v-if="section?.current_version_id !== version.id"
                  size="small"
                  @click="restoreVersion(version)"
                >
                  還原
                </el-button>
                <el-tag v-else size="small" type="success">目前</el-tag>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="尚無版本記錄" :image-size="60" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { sectionApi } from '@/api/sections'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Check, MagicStick, Clock } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.projectId)
const sectionId = computed(() => route.params.sectionId)

const loading = ref(false)
const saving = ref(false)
const content = ref('')
const originalContent = ref('')
const versions = ref([])

const project = computed(() => projectStore.currentProject)
const section = computed(() => projectStore.currentSection)
const contentLength = computed(() => content.value?.length || 0)
const hasUnsavedChanges = computed(() => content.value !== originalContent.value)

async function fetchData() {
  loading.value = true
  try {
    if (!projectStore.currentProject) {
      await projectStore.fetchProject(projectId.value)
    }
    await projectStore.fetchSection(sectionId.value)

    // Load current version content
    if (section.value?.current_version_id) {
      await loadVersionContent(section.value.current_version_id)
    } else {
      content.value = ''
      originalContent.value = ''
    }

    // Load version history
    try {
      const response = await sectionApi.getVersions(sectionId.value)
      versions.value = response.data || []
    } catch {
      versions.value = []
    }
  } finally {
    loading.value = false
  }
}

async function loadVersionContent(versionId) {
  // Find content from versions list, or load all versions
  const versionsResp = await sectionApi.getVersions(sectionId.value)
  versions.value = versionsResp.data || []
  const ver = versions.value.find(v => v.id === versionId)
  if (ver) {
    content.value = ver.content || ''
    originalContent.value = content.value
  }
}

function onContentChange() {
  // Could add autosave logic here
}

async function saveContent() {
  saving.value = true
  try {
    // Create a new version with the content
    const response = await sectionApi.createVersion(sectionId.value, {
      content: content.value,
      source_type: 'Human'
    })
    originalContent.value = content.value

    // Update versions list
    versions.value.unshift(response.data)

    // Set as current version
    await sectionApi.setCurrentVersion(sectionId.value, response.data.id)
    await projectStore.fetchSection(sectionId.value)

    ElMessage.success('儲存成功')
  } catch {
    ElMessage.error('儲存失敗')
  } finally {
    saving.value = false
  }
}

async function restoreVersion(version) {
  try {
    await ElMessageBox.confirm(
      `確定要還原到版本 ${version.version_number} 嗎？`,
      '還原確認',
      { type: 'warning' }
    )
    content.value = version.content || ''
    await sectionApi.setCurrentVersion(sectionId.value, version.id)
    await projectStore.fetchSection(sectionId.value)
    originalContent.value = content.value
    ElMessage.success('已還原')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('還原失敗')
  }
}

function goBack() {
  if (hasUnsavedChanges.value) {
    ElMessageBox.confirm('有未儲存的變更，確定要離開嗎？', '提示', {
      confirmButtonText: '離開',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      router.push(`/projects/${projectId.value}`)
    }).catch(() => {})
  } else {
    router.push(`/projects/${projectId.value}`)
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-TW')
}

onMounted(() => {
  fetchData()
})

watch([projectId, sectionId], () => {
  if (projectId.value && sectionId.value) {
    fetchData()
  }
})
</script>
