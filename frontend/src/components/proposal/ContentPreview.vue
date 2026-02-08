<template>
  <div class="content-preview h-full flex flex-col">
    <!-- 頭部 -->
    <div class="p-3 border-b flex items-center justify-between">
      <div class="flex items-center gap-2">
        <el-icon><View /></el-icon>
        <span class="font-medium">內容預覽</span>
      </div>
      <el-radio-group v-model="currentMode" size="small">
        <el-radio-button value="render">渲染</el-radio-button>
        <el-radio-button value="markdown">Markdown</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 預覽內容 -->
    <div class="flex-1 overflow-auto p-4">
      <template v-if="section?.content">
        <div v-if="currentMode === 'render'" class="prose prose-sm max-w-none" v-html="renderedContent" />
        <pre v-else class="text-sm whitespace-pre-wrap text-gray-700">{{ section.content }}</pre>
      </template>
      <div v-else class="h-full flex items-center justify-center text-gray-400">
        <div class="text-center">
          <el-icon :size="48"><Folder /></el-icon>
          <p class="mt-2">尚無生成內容</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { View, Folder } from '@element-plus/icons-vue'
import { marked } from 'marked'

const props = defineProps({
  section: Object,
  mode: { type: String, default: 'render' }
})

const emit = defineEmits(['change-mode'])

const currentMode = ref(props.mode)

const renderedContent = computed(() => {
  if (!props.section?.content) return ''
  try {
    return marked(props.section.content, { breaks: true })
  } catch {
    return props.section.content.replace(/\n/g, '<br>')
  }
})

watch(currentMode, (val) => {
  emit('change-mode', val)
})
</script>
