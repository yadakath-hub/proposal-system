<template>
  <div class="streaming-output">
    <div
      ref="outputRef"
      class="output-content bg-white border rounded-lg p-4 min-h-[200px] max-h-[400px] overflow-auto"
    >
      <div v-if="!content && !isStreaming" class="text-gray-400 text-center py-8">
        AI 生成的內容將顯示在這裡
      </div>

      <div v-else class="prose prose-sm max-w-none">
        <div v-html="renderedContent" />
        <span v-if="isStreaming" class="typing-cursor">|</span>
      </div>
    </div>

    <div class="flex justify-between items-center mt-2 text-xs text-gray-500">
      <div v-if="isStreaming" class="flex items-center gap-2">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>生成中...</span>
      </div>
      <div v-else-if="content">
        <span>生成完成 ({{ content.length }} 字)</span>
      </div>
      <div v-else></div>

      <div v-if="tokenCount.output > 0">
        輸出: {{ tokenCount.output }} tokens
      </div>
    </div>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      closable
      class="mt-2"
      @close="$emit('clear-error')"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Loading } from '@element-plus/icons-vue'

const props = defineProps({
  content: { type: String, default: '' },
  isStreaming: { type: Boolean, default: false },
  error: { type: String, default: null },
  tokenCount: { type: Object, default: () => ({ input: 0, output: 0 }) }
})

defineEmits(['clear-error'])

const outputRef = ref(null)

const renderedContent = computed(() => {
  if (!props.content) return ''
  // Simple markdown: convert newlines to <br> and **bold**
  return props.content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
})

watch(() => props.content, () => {
  nextTick(() => {
    if (outputRef.value) {
      outputRef.value.scrollTop = outputRef.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.typing-cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
