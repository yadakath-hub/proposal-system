<template>
  <div class="proposal-editor">
    <!-- Top toolbar -->
    <ProposalHeader
      :project="project"
      :progress="proposalStore.progress"
      @import-structure="showImportDialog = true"
      @analyze-requirements="showRequirementDialog = true"
      @toggle-mode="proposalStore.toggleEditMode"
      @export="showExportDialog = true"
    />

    <!-- Three-panel body -->
    <div class="editor-body">
      <!-- Left: Section tree -->
      <aside class="section-panel" :style="{ width: leftPanelWidth + 'px' }">
        <SectionTree
          :sections="proposalStore.sectionTree"
          :current-section="proposalStore.currentSection"
          @select="handleSelectSection"
          @reorder="handleReorder"
          @add="handleAddSection"
          @delete="handleDeleteSection"
        />
        <div
          class="resize-handle resize-handle-right"
          @mousedown="startResize('left', $event)"
        />
      </aside>

      <!-- Center: Editor -->
      <main class="content-panel">
        <SectionEditorPanel
          v-if="proposalStore.currentSection"
          :section="proposalStore.currentSection"
          :project-id="projectId"
          @save="handleSaveSection"
          @generate="handleGenerate"
        />
        <div v-else class="empty-state">
          <el-icon :size="64" class="empty-icon"><DocumentAdd /></el-icon>
          <h3>請選擇或建立章節</h3>
          <p>從左側選擇章節開始編輯，或點擊「匯入章節架構」快速建立</p>
          <el-button type="primary" @click="showImportDialog = true">
            匯入章節架構
          </el-button>
        </div>
      </main>

      <!-- Right: Preview -->
      <aside class="preview-panel" :style="{ width: rightPanelWidth + 'px' }">
        <div
          class="resize-handle resize-handle-left"
          @mousedown="startResize('right', $event)"
        />
        <ContentPreview
          :section="proposalStore.currentSection"
          :mode="previewMode"
          @change-mode="previewMode = $event"
        />
      </aside>
    </div>

    <!-- Bottom stats -->
    <ProposalFooter :stats="proposalStore.stats" />

    <!-- Dialogs -->
    <ImportStructureDialog
      v-model:visible="showImportDialog"
      :project-id="projectId"
      @imported="handleStructureImported"
    />

    <RequirementAnalyzeDialog
      v-model:visible="showRequirementDialog"
      :project-id="projectId"
      @analyzed="handleRequirementAnalyzed"
    />

    <ExportDialog
      v-model:visible="showExportDialog"
      :project-id="projectId"
      :sections="proposalStore.flattenSections(proposalStore.sectionTree)"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
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
import RequirementAnalyzeDialog from '@/components/proposal/RequirementAnalyzeDialog.vue'
import ExportDialog from '@/components/export/ExportDialog.vue'

const route = useRoute()
const router = useRouter()
const proposalStore = useProposalStore()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.projectId)
const project = computed(() => projectStore.currentProject)

// Panel widths (resizable)
const leftPanelWidth = ref(280)
const rightPanelWidth = ref(360)
const previewMode = ref('render')

// Dialogs
const showImportDialog = ref(false)
const showRequirementDialog = ref(false)
const showExportDialog = ref(false)

// Drag resize
let isResizing = false
let resizeTarget = ''
let startX = 0
let startWidth = 0

function startResize(target, e) {
  isResizing = true
  resizeTarget = target
  startX = e.clientX
  startWidth = target === 'left' ? leftPanelWidth.value : rightPanelWidth.value

  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function handleResize(e) {
  if (!isResizing) return

  const diff = e.clientX - startX
  const newWidth = resizeTarget === 'left'
    ? startWidth + diff
    : startWidth - diff

  const minWidth = 200
  const maxWidth = 500

  if (resizeTarget === 'left') {
    leftPanelWidth.value = Math.max(minWidth, Math.min(maxWidth, newWidth))
  } else {
    rightPanelWidth.value = Math.max(minWidth, Math.min(maxWidth, newWidth))
  }
}

function stopResize() {
  isResizing = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// Data loading
async function loadData() {
  try {
    await projectStore.fetchProject(projectId.value)
    await projectStore.fetchSections(projectId.value)
    proposalStore.currentProject = projectStore.currentProject
    proposalStore.buildSectionTree(projectStore.sections)

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
  if (proposalStore.currentSection) {
    router.push(`/projects/${projectId.value}/sections/${proposalStore.currentSection.id}`)
  }
}

function handleStructureImported() {
  loadData()
  ElMessage.success('章節架構已匯入')
}

function handleRequirementAnalyzed() {
  ElMessage.success('需求分析完成，已自動關聯至對應章節')
}

onMounted(() => {
  loadData()
})

onBeforeUnmount(() => {
  // Cleanup any lingering resize listeners
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})

watch(projectId, () => {
  if (projectId.value) {
    loadData()
  }
})
</script>

<style scoped>
.proposal-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* Three-panel body */
.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.section-panel,
.preview-panel {
  position: relative;
  background: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.section-panel {
  border-right: 1px solid var(--border-color);
}

.preview-panel {
  border-left: 1px solid var(--border-color);
}

.content-panel {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Resize handles */
.resize-handle {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  z-index: 10;
  transition: background 0.15s;
}

.resize-handle:hover {
  background: #1890ff;
}

.resize-handle-right {
  right: -2px;
}

.resize-handle-left {
  left: -2px;
}

/* Empty state */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  padding: 40px;
  text-align: center;
}

.empty-icon {
  color: #d9d9d9;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.empty-state p {
  margin: 0 0 24px;
  max-width: 300px;
}

/* Responsive */
@media (max-width: 1280px) {
  .section-panel {
    width: 240px !important;
  }

  .preview-panel {
    width: 300px !important;
  }
}

@media (max-width: 1024px) {
  .preview-panel {
    display: none;
  }
}
</style>
