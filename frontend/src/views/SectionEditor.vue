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
        <el-button @click="searchDocuments">
          <el-icon class="mr-1"><Search /></el-icon>
          搜尋文件
        </el-button>
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
            :rows="30"
            placeholder="在此輸入章節內容，或使用右側 AI 助手生成..."
          />
        </el-card>
      </div>

      <!-- Right: AI assistant panel -->
      <div class="w-[420px] border-l bg-gray-50 p-4 overflow-auto">
        <AiAssistPanel
          ref="aiPanelRef"
          :project-id="projectId"
          :section-id="sectionId"
          :section-title="section?.title || ''"
          :current-content="content"
          section-level="L1"
          @apply="applyAiContent"
        />
      </div>
    </div>

    <!-- RAG search dialog -->
    <el-dialog v-model="searchDialogVisible" title="搜尋相關文件" width="600px">
      <RagSearch
        :project-id="projectId"
        @select="onRagSelect"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { sectionApi } from '@/api/sections'
import { ElMessage, ElMessageBox } from 'element-plus'
import AiAssistPanel from '@/components/editor/AiAssistPanel.vue'
import RagSearch from '@/components/document/RagSearch.vue'
import { ArrowLeft, Check, Search } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.projectId)
const sectionId = computed(() => route.params.sectionId)

const loading = ref(false)
const saving = ref(false)
const content = ref('')
const originalContent = ref('')
const searchDialogVisible = ref(false)
const aiPanelRef = ref()

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
      const versionsResp = await sectionApi.getVersions(sectionId.value)
      const versions = versionsResp.data || []
      const currentVer = versions.find(v => v.id === section.value.current_version_id)
      if (currentVer) {
        content.value = currentVer.content || ''
        originalContent.value = content.value
      }
    } else {
      content.value = ''
      originalContent.value = ''
    }
  } finally {
    loading.value = false
  }
}

async function saveContent() {
  saving.value = true
  try {
    // Create a new version
    const response = await sectionApi.createVersion(sectionId.value, {
      content: content.value,
      source_type: 'Human'
    })

    // Set as current version
    await sectionApi.setCurrentVersion(sectionId.value, response.data.id)
    await projectStore.fetchSection(sectionId.value)

    originalContent.value = content.value
    ElMessage.success('儲存成功')
  } catch {
    ElMessage.error('儲存失敗')
  } finally {
    saving.value = false
  }
}

function applyAiContent(aiContent) {
  if (content.value) {
    ElMessageBox.confirm('要取代現有內容還是附加到後面？', '應用方式', {
      distinguishCancelAndClose: true,
      confirmButtonText: '取代',
      cancelButtonText: '附加'
    }).then(() => {
      content.value = aiContent
    }).catch((action) => {
      if (action === 'cancel') {
        content.value = content.value + '\n\n' + aiContent
      }
    })
  } else {
    content.value = aiContent
  }
}

function searchDocuments() {
  searchDialogVisible.value = true
}

function onRagSelect(results) {
  searchDialogVisible.value = false
  aiPanelRef.value?.setRagContext(results)
  ElMessage.success(`已加入 ${results.length} 段參考內容`)
}

function goBack() {
  if (hasUnsavedChanges.value) {
    ElMessageBox.confirm('有未儲存的變更，確定要離開嗎？', '提示', {
      type: 'warning'
    }).then(() => {
      router.push(`/projects/${projectId.value}`)
    }).catch(() => {})
  } else {
    router.push(`/projects/${projectId.value}`)
  }
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
