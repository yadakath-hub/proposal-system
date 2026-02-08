<template>
  <div class="section-editor-panel h-full flex flex-col">
    <!-- 章節標題 -->
    <div class="p-4 border-b bg-white">
      <div class="text-xs text-gray-400 mb-1">{{ section.chapter_number }}</div>
      <h2 class="text-xl font-bold">{{ section.title }}</h2>
      <el-tag :type="getStatusType(section.status)" size="small" class="mt-2">
        {{ getStatusText(section.status) }}
      </el-tag>
    </div>

    <!-- 編輯區域 -->
    <div class="flex-1 overflow-auto p-4 space-y-4">
      <!-- 需求解讀範本 -->
      <el-card shadow="never">
        <template #header>
          <div class="flex items-center gap-2">
            <el-icon class="text-blue-500"><InfoFilled /></el-icon>
            <span>需求解讀範本</span>
          </div>
        </template>
        <p class="text-gray-600 text-sm">
          {{ section.requirement_text || '說明本案之源起、目的、預期效益。' }}
        </p>
        <el-button text type="primary" size="small" class="mt-2">
          編輯範本提示
        </el-button>
      </el-card>

      <!-- 關聯需求 -->
      <SectionRequirements
        :section-id="section.id"
        :project-id="projectId"
      />

      <!-- 該案特定需求說明 -->
      <el-card shadow="never">
        <template #header>
          <div class="flex items-center gap-2">
            <el-icon class="text-green-500"><Edit /></el-icon>
            <span>該案特定需求說明</span>
          </div>
        </template>
        <el-input
          v-model="form.requirement"
          type="textarea"
          :rows="4"
          placeholder="請輸入本案的特定需求說明，例如：專案規模、預算、時程、特殊技術要求等..."
        />
      </el-card>

      <!-- AI 範本推薦 -->
      <TemplateRecommendPanel
        :section-id="section.id"
        :section-title="section.title"
        :requirement-content="form.requirement"
        @apply="handleTemplateApply"
      />

      <!-- 內容編輯 -->
      <el-card shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <el-icon class="text-purple-500"><Document /></el-icon>
              <span>章節內容</span>
            </div>
            <span class="text-sm text-gray-400">{{ form.content?.length || 0 }} 字</span>
          </div>
        </template>
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="10"
          placeholder="在此輸入章節內容，或點擊下方按鈕使用 AI 生成..."
        />
      </el-card>
    </div>

    <!-- 底部操作按鈕 -->
    <div class="p-4 border-t bg-white flex items-center gap-3">
      <el-button type="primary" size="large" :icon="MagicStick" @click="$emit('generate')">
        AI 生成內容
      </el-button>
      <el-button size="large" @click="clearContent">
        清除內容
      </el-button>
      <el-button size="large" :icon="PictureFilled">
        插入圖表
      </el-button>
      <div class="flex-1"></div>
      <el-button type="success" size="large" :icon="Check" @click="handleSave">
        儲存
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { InfoFilled, Edit, Document, MagicStick, PictureFilled, Check } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import SectionRequirements from '@/components/proposal/SectionRequirements.vue'
import TemplateRecommendPanel from '@/components/proposal/TemplateRecommendPanel.vue'

const props = defineProps({
  section: { type: Object, required: true },
  projectId: [String, Number]
})

const emit = defineEmits(['save', 'generate'])

const form = reactive({
  requirement: '',
  content: ''
})

watch(() => props.section, (newSection) => {
  if (newSection) {
    form.requirement = newSection.requirement_text || ''
    form.content = newSection.content || ''
  }
}, { immediate: true })

function handleSave() {
  emit('save', {
    id: props.section.id,
    requirement_text: form.requirement,
    content: form.content
  })
}

function handleTemplateApply(content) {
  form.content = content
}

function clearContent() {
  ElMessageBox.confirm('確定要清除內容嗎？', '提示', { type: 'warning' })
    .then(() => {
      form.content = ''
    })
    .catch(() => {})
}

function getStatusType(status) {
  const map = {
    Approved: 'success',
    Writing: 'warning',
    Review: '',
    NotStarted: 'info',
    Locked: 'danger'
  }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = {
    Approved: '已完成',
    Writing: '撰寫中',
    Review: '審核中',
    NotStarted: '未開始',
    Locked: '已鎖定'
  }
  return map[status] || '未開始'
}
</script>
