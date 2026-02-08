<template>
  <div class="ai-assist-panel space-y-4">
    <!-- Level selector -->
    <el-card>
      <LevelSelector v-model="form.sectionLevel" @change="onLevelChange" />
    </el-card>

    <!-- Generation mode -->
    <el-card>
      <div class="text-sm text-gray-500 mb-2">生成模式</div>
      <el-radio-group v-model="form.mode" size="small">
        <el-radio-button value="generate">生成</el-radio-button>
        <el-radio-button value="rewrite">重寫</el-radio-button>
        <el-radio-button value="audit" :disabled="form.sectionLevel !== 'L2'">稽核</el-radio-button>
        <el-radio-button value="expand">擴展</el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- Prompt input -->
    <el-card>
      <div class="text-sm text-gray-500 mb-2">額外提示</div>
      <el-input
        v-model="form.prompt"
        type="textarea"
        :rows="3"
        placeholder="輸入額外的指示或要求..."
      />
    </el-card>

    <!-- RAG context -->
    <el-card v-if="ragContext.length > 0">
      <div class="text-sm text-gray-500 mb-2">
        參考文件 ({{ ragContext.length }} 段)
        <el-button text size="small" @click="ragContext = []">清除</el-button>
      </div>
      <div class="max-h-32 overflow-auto text-xs text-gray-600">
        <div v-for="(ctx, idx) in ragContext" :key="idx" class="mb-2 p-2 bg-gray-50 rounded">
          {{ (ctx.chunk_text || ctx.content || '').substring(0, 100) }}...
        </div>
      </div>
    </el-card>

    <!-- Cost estimator -->
    <CostEstimator
      ref="costEstimatorRef"
      :section-level="form.sectionLevel"
      :input-tokens="estimatedInputTokens"
      :output-tokens="estimatedOutputTokens"
      :use-cache="form.useCache"
    />

    <!-- Action buttons -->
    <div class="flex gap-2">
      <el-button
        type="primary"
        class="flex-1"
        :loading="streaming.isStreaming.value"
        :disabled="!canGenerate"
        @click="handleGenerate"
      >
        <el-icon class="mr-1"><MagicStick /></el-icon>
        {{ streaming.isStreaming.value ? '生成中...' : '開始生成' }}
      </el-button>

      <el-button
        v-if="streaming.isStreaming.value"
        type="danger"
        @click="handleStop"
      >
        停止
      </el-button>
    </div>

    <!-- Streaming output -->
    <StreamingOutput
      :content="streaming.content.value"
      :is-streaming="streaming.isStreaming.value"
      :error="streaming.error.value"
      :token-count="streaming.tokenCount.value"
      @clear-error="streaming.clearContent()"
    />

    <!-- Apply/Discard buttons -->
    <div v-if="streaming.content.value && !streaming.isStreaming.value" class="flex gap-2">
      <el-button type="success" class="flex-1" @click="handleApply">
        <el-icon class="mr-1"><Check /></el-icon>
        採用此內容
      </el-button>
      <el-button class="flex-1" @click="handleDiscard">
        <el-icon class="mr-1"><Close /></el-icon>
        放棄
      </el-button>
      <el-button @click="handleRegenerate">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useStreaming } from '@/composables/useStreaming'
import { aiApi } from '@/api/ai'
import LevelSelector from './LevelSelector.vue'
import CostEstimator from './CostEstimator.vue'
import StreamingOutput from './StreamingOutput.vue'
import { MagicStick, Check, Close, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  projectId: { type: String, required: true },
  sectionId: { type: String, required: true },
  sectionTitle: { type: String, default: '' },
  currentContent: { type: String, default: '' },
  sectionLevel: { type: String, default: 'L1' }
})

const emit = defineEmits(['apply', 'update:sectionLevel'])

const streaming = useStreaming()
const costEstimatorRef = ref()
const ragContext = ref([])

const form = reactive({
  sectionLevel: props.sectionLevel || 'L1',
  mode: 'generate',
  prompt: '',
  useCache: true
})

const estimatedInputTokens = computed(() => {
  const baseTokens = 500
  const contentTokens = Math.ceil((props.currentContent?.length || 0) / 2)
  const ragTokens = ragContext.value.reduce((sum, ctx) =>
    sum + ((ctx.chunk_text || ctx.content || '').length / 2), 0)
  return baseTokens + contentTokens + ragTokens
})

const estimatedOutputTokens = computed(() => {
  const map = { L1: 500, L2: 300, L3: 1000, L4: 2000 }
  return map[form.sectionLevel] || 500
})

const canGenerate = computed(() => {
  if (form.mode === 'rewrite' || form.mode === 'expand' || form.mode === 'audit') {
    return props.currentContent?.length > 0
  }
  return true
})

function onLevelChange(level) {
  emit('update:sectionLevel', level)
  if (level === 'L2' && props.currentContent) {
    form.mode = 'audit'
  }
}

async function handleGenerate() {
  const apiUrl = aiApi.getStreamUrl()

  const body = {
    project_id: props.projectId,
    section_id: props.sectionId,
    section_level: form.sectionLevel,
    generation_mode: form.mode,
    prompt: buildPrompt(),
    context: ragContext.value.map(c => c.chunk_text || c.content || '').join('\n\n'),
    template: props.currentContent || '',
    use_cache: form.useCache
  }

  await streaming.startStream(apiUrl, body)
  costEstimatorRef.value?.estimate()
}

function buildPrompt() {
  let prompt = ''

  if (props.sectionTitle) {
    prompt += `章節標題：${props.sectionTitle}\n\n`
  }

  if (form.prompt) {
    prompt += `要求：${form.prompt}\n\n`
  }

  if (form.mode === 'rewrite') {
    prompt += `請重寫以下內容，提升品質和專業度：\n\n${props.currentContent}`
  } else if (form.mode === 'expand') {
    prompt += `請擴展以下內容，增加更多細節：\n\n${props.currentContent}`
  } else if (form.mode === 'audit') {
    prompt += `請稽核以下內容，僅標註需要修改的地方：\n\n${props.currentContent}`
  }

  return prompt
}

function handleStop() {
  streaming.stopStream()
}

function handleApply() {
  emit('apply', streaming.content.value)
  ElMessage.success('內容已採用')
  streaming.clearContent()
}

function handleDiscard() {
  streaming.clearContent()
  ElMessage.info('已放棄生成的內容')
}

function handleRegenerate() {
  streaming.clearContent()
  handleGenerate()
}

defineExpose({
  setRagContext(context) {
    ragContext.value = context
  }
})

onMounted(() => {
  form.sectionLevel = props.sectionLevel || 'L1'
})
</script>
