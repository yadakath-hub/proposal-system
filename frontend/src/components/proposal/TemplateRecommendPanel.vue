<template>
  <el-card shadow="never" class="template-recommend">
    <template #header>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <el-icon class="text-purple-500"><MagicStick /></el-icon>
          <span>AI 範本推薦</span>
        </div>
        <el-button text size="small" :loading="loading" @click="getRecommendations">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </template>

    <div v-if="loading" class="text-center py-8">
      <el-icon :size="32" class="is-loading text-blue-500"><Loading /></el-icon>
      <p class="text-sm text-gray-500 mt-2">AI 正在分析推薦...</p>
    </div>

    <template v-else-if="recommendations.length > 0">
      <div v-if="analysis" class="mb-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
        {{ analysis }}
      </div>

      <div class="space-y-3">
        <div
          v-for="rec in recommendations"
          :key="rec.template_id"
          class="p-3 border rounded-lg hover:border-blue-500 cursor-pointer transition-colors"
          @click="showPreview(rec)"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="font-medium text-sm">{{ rec.name }}</span>
            <div class="flex items-center gap-2">
              <el-progress
                :percentage="rec.score"
                :stroke-width="6"
                :show-text="false"
                class="w-16"
              />
              <span class="text-sm font-bold" :class="getScoreClass(rec.score)">
                {{ rec.score }}%
              </span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mb-2">{{ rec.reason }}</p>
          <div class="flex items-center justify-between">
            <div class="text-xs text-gray-400">
              {{ rec.word_count }} 字 · 使用 {{ rec.usage_count }} 次
            </div>
            <el-button type="primary" size="small" @click.stop="applyTemplate(rec)">
              套用
            </el-button>
          </div>
        </div>
      </div>
    </template>

    <el-empty v-else description="點擊重新整理取得推薦" :image-size="60">
      <el-button type="primary" @click="getRecommendations">
        取得推薦
      </el-button>
    </el-empty>

    <!-- 預覽 Dialog -->
    <el-dialog v-model="showPreviewDialog" title="範本預覽" width="600px" append-to-body>
      <template v-if="previewTemplate">
        <div class="mb-4">
          <h3 class="font-bold text-lg">{{ previewTemplate.name }}</h3>
          <el-tag size="small" class="mt-1">{{ previewTemplate.category }}</el-tag>
        </div>
        <div class="bg-gray-50 p-4 rounded-lg max-h-80 overflow-auto">
          <pre class="whitespace-pre-wrap text-sm">{{ previewContent }}</pre>
        </div>
      </template>
      <template #footer>
        <el-button @click="showPreviewDialog = false">取消</el-button>
        <el-radio-group v-model="applyMode" class="mx-4">
          <el-radio value="replace">取代</el-radio>
          <el-radio value="append">附加</el-radio>
        </el-radio-group>
        <el-button type="primary" @click="confirmApply">套用</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import { templateApi } from '@/api/templates'
import { ElMessage } from 'element-plus'
import { MagicStick, Refresh, Loading } from '@element-plus/icons-vue'

const props = defineProps({
  sectionId: [String, Object],
  sectionTitle: String,
  sectionType: String,
  requirementContent: String,
  projectContext: String
})

const emit = defineEmits(['apply'])

const loading = ref(false)
const recommendations = ref([])
const analysis = ref('')

const showPreviewDialog = ref(false)
const previewTemplate = ref(null)
const previewContent = ref('')
const applyMode = ref('replace')

async function getRecommendations() {
  if (!props.sectionId) return

  loading.value = true
  recommendations.value = []
  analysis.value = ''

  try {
    const resp = await templateApi.recommend({
      section_id: props.sectionId,
      section_title: props.sectionTitle || '',
      section_type: props.sectionType,
      requirement_content: props.requirementContent,
      project_context: props.projectContext,
      top_k: 3
    })
    recommendations.value = resp.data.recommendations || []
    analysis.value = resp.data.analysis || ''
  } catch {
    ElMessage.error('取得推薦失敗')
  } finally {
    loading.value = false
  }
}

async function showPreview(rec) {
  previewTemplate.value = rec
  try {
    const resp = await templateApi.get(rec.template_id)
    previewContent.value = resp.data.content
    showPreviewDialog.value = true
  } catch {
    ElMessage.error('載入範本內容失敗')
  }
}

function applyTemplate(rec) {
  showPreview(rec)
}

async function confirmApply() {
  try {
    const resp = await templateApi.apply(
      previewTemplate.value.template_id,
      props.sectionId,
      applyMode.value
    )
    ElMessage.success('範本已套用')
    showPreviewDialog.value = false
    emit('apply', resp.data.content)
  } catch {
    ElMessage.error('套用失敗')
  }
}

function getScoreClass(score) {
  if (score >= 90) return 'text-green-600'
  if (score >= 70) return 'text-blue-600'
  if (score >= 50) return 'text-yellow-600'
  return 'text-gray-600'
}

watch(() => props.sectionId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    recommendations.value = []
    analysis.value = ''
  }
})
</script>
