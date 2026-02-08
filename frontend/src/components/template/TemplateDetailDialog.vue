<template>
  <el-dialog
    :model-value="visible"
    title="範本詳情"
    width="800px"
    @close="$emit('update:visible', false)"
  >
    <div v-loading="loading">
      <template v-if="template">
        <div class="flex items-start justify-between mb-4">
          <div>
            <h2 class="text-xl font-bold">{{ template.name }}</h2>
            <div class="flex items-center gap-2 mt-2">
              <el-tag>{{ getCategoryLabel(template.category) }}</el-tag>
              <el-tag type="info">v{{ template.version }}</el-tag>
              <span class="text-sm text-gray-500">{{ template.word_count }} 字</span>
              <span class="text-sm text-gray-500">使用 {{ template.usage_count }} 次</span>
            </div>
          </div>
          <el-button type="primary" @click="$emit('edit', template)">編輯</el-button>
        </div>

        <el-divider />

        <div v-if="template.description" class="mb-4">
          <h3 class="text-sm text-gray-500 mb-1">描述</h3>
          <p>{{ template.description }}</p>
        </div>

        <div v-if="template.tags?.length" class="mb-4">
          <h3 class="text-sm text-gray-500 mb-1">標籤</h3>
          <el-tag v-for="tag in template.tags" :key="tag" class="mr-2" size="small">
            {{ tag }}
          </el-tag>
        </div>

        <div class="mb-4">
          <h3 class="text-sm text-gray-500 mb-1">內容預覽</h3>
          <div class="bg-gray-50 p-4 rounded-lg max-h-64 overflow-auto">
            <pre class="whitespace-pre-wrap text-sm">{{ template.content }}</pre>
          </div>
        </div>

        <div v-if="template.versions?.length">
          <h3 class="text-sm text-gray-500 mb-2">版本歷史</h3>
          <el-timeline>
            <el-timeline-item
              v-for="v in template.versions"
              :key="v.version"
              :timestamp="formatDate(v.created_at)"
              placement="top"
            >
              <p class="font-medium">版本 {{ v.version }}</p>
              <p class="text-sm text-gray-500">{{ v.change_note || '無說明' }}</p>
            </el-timeline-item>
          </el-timeline>
        </div>
      </template>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { templateApi } from '@/api/templates'

const props = defineProps({
  visible: Boolean,
  templateId: [String, Number]
})

defineEmits(['update:visible', 'edit'])

const loading = ref(false)
const template = ref(null)

const categoryLabels = {
  introduction: '公司簡介',
  technical: '技術規劃',
  solution: '解決方案',
  management: '專案管理',
  security: '資安規劃',
  compliance: '法規合規',
  qualification: '廠商資格',
  experience: '專案實績',
  team: '團隊組織',
  timeline: '時程規劃',
  pricing: '報價說明',
  maintenance: '維護服務',
  training: '教育訓練',
  other: '其他'
}

watch(() => props.visible, (val) => {
  if (val && props.templateId) {
    loadTemplate()
  }
})

async function loadTemplate() {
  loading.value = true
  try {
    const resp = await templateApi.get(props.templateId)
    template.value = resp.data
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

function getCategoryLabel(value) {
  return categoryLabels[value] || value
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-TW')
}
</script>
