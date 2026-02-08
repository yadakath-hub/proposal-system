<template>
  <div class="level-selector">
    <div class="text-sm text-gray-500 mb-2">章節等級</div>
    <el-radio-group v-model="selectedLevel" size="small" @change="onChange">
      <el-radio-button
        v-for="level in levels"
        :key="level.value"
        :value="level.value"
      >
        <el-tooltip :content="level.description" placement="top">
          <span>{{ level.label }}</span>
        </el-tooltip>
      </el-radio-button>
    </el-radio-group>

    <div class="mt-2 text-xs text-gray-400">
      <span>模型: {{ currentStrategy.model }}</span>
      <span class="ml-2">思考: {{ currentStrategy.thinking }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: 'L1' }
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectedLevel = ref(props.modelValue)

const levels = [
  {
    value: 'L1',
    label: 'L1 基礎',
    description: '目錄/簡介 - Gemini Flash Lite, 快速生成',
    model: 'gemini-flash-lite',
    thinking: '0'
  },
  {
    value: 'L2',
    label: 'L2 合規',
    description: '資安/法規 - Claude 3.5 + 稽核模式',
    model: 'claude-3.5-sonnet',
    thinking: '500'
  },
  {
    value: 'L3',
    label: 'L3 標準',
    description: '專案管理 - Gemini Flash, 標準品質',
    model: 'gemini-flash',
    thinking: '1000'
  },
  {
    value: 'L4',
    label: 'L4 決勝',
    description: '解決方案 - Claude 4.5 + 深度推理',
    model: 'claude-4.5-sonnet',
    thinking: '2000'
  }
]

const currentStrategy = computed(() => {
  return levels.find(l => l.value === selectedLevel.value) || levels[0]
})

watch(() => props.modelValue, (val) => {
  selectedLevel.value = val
})

function onChange(val) {
  emit('update:modelValue', val)
  emit('change', val)
}
</script>
