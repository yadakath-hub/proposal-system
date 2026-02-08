<template>
  <div class="proposal-editor h-screen flex flex-col bg-gray-100">
    <!-- 頂部工具列 -->
    <ProposalHeader
      :project="project"
      :progress="proposalStore.progress"
      @import-structure="showImportDialog = true"
      @toggle-mode="proposalStore.toggleEditMode"
      @export="showExportDialog = true"
    />

    <!-- 主體三欄區域 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 左側：章節樹 -->
      <div
        class="section-tree-panel bg-white border-r overflow-hidden flex flex-col"
        :style="{ width: `${proposalStore.panelWidths.sectionTree}px` }"
      >
        <SectionTree
          :sections="proposalStore.sectionTree"
          :current-section="proposalStore.currentSection"
          @select="handleSelectSection"
          @reorder="handleReorder"
          @add="handleAddSection"
          @delete="handleDeleteSection"
        />
      </div>

      <!-- 中間：編輯區 -->
      <div class="editor-panel flex-1 flex flex-col overflow-hidden">
        <SectionEditorPanel
          v-if="proposalStore.currentSection"
          :section="proposalStore.currentSection"
          :project-id="projectId"
          @save="handleSaveSection"
          @generate="handleGenerate"
        />
        <div v-else class="flex-1 flex items-center justify-center text-gray-400">
          <div class="text-center">
            <el-icon :size="64"><DocumentAdd /></el-icon>
            <p class="mt-4">請從左側選擇章節開始編輯</p>
          </div>
        </div>
      </div>

      <!-- 右側：預覽區 -->
      <div
        class="preview-panel bg-white border-l overflow-hidden"
        :style="{ width: `${proposalStore.panelWidths.preview}px` }"
      >
        <ContentPreview
          :section="proposalStore.currentSection"
          :mode="previewMode"
          @change-mode="previewMode = $event"
        />
      </div>
    </div>

    <!-- 底部統計列 -->
    <ProposalFooter :stats="proposalStore.stats" />

    <!-- 匯入章節架構 Dialog -->
    <ImportStructureDialog
      v-model:visible="showImportDialog"
      :project-id="projectId"
      @imported="handleStructureImported"
    />

    <!-- 匯出 Dialog -->
    <ExportDialog
      v-model:visible="showExportDialog"
      :project-id="projectId"
      :sections="proposalStore.flattenSections(proposalStore.sectionTree)"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProposalStore } from '@/stores/proposal'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'
import { DocumentAdd } from '@element-plus/icons-vue'

import ProposalHeader from '@/components/proposal/ProposalHeader.vue'
import ProposalFooter from '@/components/proposal/ProposalFooter.vue'
import SectionTree from '@/components/proposal/SectionTree.vue'
import SectionEditorPanel from '@/components/proposal/SectionEditorPanel.vue'
import ContentPreview from '@/components/proposal/ContentPreview.vue'
import ImportStructureDialog from '@/components/proposal/ImportStructureDialog.vue'
import ExportDialog from '@/components/export/ExportDialog.vue'

const route = useRoute()
const router = useRouter()
const proposalStore = useProposalStore()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.projectId)
const project = computed(() => projectStore.currentProject)

const showImportDialog = ref(false)
const showExportDialog = ref(false)
const previewMode = ref('render')

async function loadData() {
  try {
    await projectStore.fetchProject(projectId.value)
    await projectStore.fetchSections(projectId.value)
    proposalStore.currentProject = projectStore.currentProject
    proposalStore.buildSectionTree(projectStore.sections)

    // 自動選擇第一個章節
    if (proposalStore.sectionTree.length > 0 && !proposalStore.currentSection) {
      proposalStore.setCurrentSection(proposalStore.sectionTree[0])
    }
  } catch {
    ElMessage.error('載入專案失敗')
  }
}

function handleSelectSection(section) {
  proposalStore.setCurrentSection(section)
}

async function handleReorder(items) {
  try {
    await projectStore.reorderSections(items)
  } catch {
    ElMessage.error('排序失敗')
  }
}

function handleAddSection() {
  // Navigate back to project detail to use the section form
  router.push(`/projects/${projectId.value}`)
}

async function handleDeleteSection(section) {
  try {
    await projectStore.deleteSection(section.id)
    if (proposalStore.currentSection?.id === section.id) {
      proposalStore.setCurrentSection(null)
    }
    await loadData()
    ElMessage.success('章節已刪除')
  } catch {
    ElMessage.error('刪除失敗')
  }
}

async function handleSaveSection(data) {
  try {
    await projectStore.updateSection(data.id, {
      requirement_text: data.requirement_text
    })
    // If content changed, create a new version
    if (data.content) {
      const { sectionApi } = await import('@/api/sections')
      const versionResp = await sectionApi.createVersion(data.id, {
        content: data.content,
        source_type: 'Human'
      })
      await sectionApi.setCurrentVersion(data.id, versionResp.data.id)
    }
    await loadData()
    ElMessage.success('儲存成功')
  } catch {
    ElMessage.error('儲存失敗')
  }
}

function handleGenerate() {
  // Navigate to section editor with AI panel
  if (proposalStore.currentSection) {
    router.push(`/projects/${projectId.value}/sections/${proposalStore.currentSection.id}`)
  }
}

function handleStructureImported() {
  loadData()
  ElMessage.success('章節架構已匯入')
}

onMounted(() => {
  loadData()
})

watch(projectId, () => {
  if (projectId.value) {
    loadData()
  }
})
</script>

<style scoped>
.proposal-editor {
  --header-height: 56px;
  --footer-height: 48px;
}
</style>
