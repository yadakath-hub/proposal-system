<template>
  <div class="cost-estimator p-3 bg-gray-50 rounded-lg">
    <div class="flex justify-between items-center mb-2">
      <span class="text-sm text-gray-500">預估成本</span>
      <el-button text size="small" :loading="loading" @click="estimate">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>

    <div v-if="cost" class="space-y-1 text-sm">
      <div class="flex justify-between">
        <span class="text-gray-500">輸入</span>
        <span>${{ cost.input_cost?.toFixed(4) || '0.0000' }}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-gray-500">輸出</span>
        <span>${{ cost.output_cost?.toFixed(4) || '0.0000' }}</span>
      </div>
      <div v-if="cost.cache_savings > 0" class="flex justify-between text-green-600">
        <span>快取節省</span>
        <span>-${{ cost.cache_savings?.toFixed(4) }}</span>
      </div>
      <el-divider class="my-2" />
      <div class="flex justify-between font-bold">
        <span>總計</span>
        <span :class="totalCostClass">${{ cost.total_cost?.toFixed(4) || '0.0000' }}</span>
      </div>
    </div>

    <div v-else class="text-center text-gray-400 text-sm py-2">
      點擊重新整理預估成本
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  sectionLevel: { type: String, default: 'L1' },
  inputTokens: { type: Number, default: 1000 },
  outputTokens: { type: Number, default: 500 },
  useCache: { type: Boolean, default: true }
})

const loading = ref(false)
const cost = ref(null)

const totalCostClass = computed(() => {
  const total = cost.value?.total_cost || 0
  if (total > 0.5) return 'text-red-600'
  if (total > 0.1) return 'text-yellow-600'
  return 'text-green-600'
})

async function estimate() {
  loading.value = true
  try {
    // Local estimation based on known pricing
    const rates = {
      L1: { input: 0.10, output: 0.40 },
      L2: { input: 3.00, output: 15.00 },
      L3: { input: 0.30, output: 2.50 },
      L4: { input: 3.00, output: 15.00 }
    }
    const rate = rates[props.sectionLevel] || rates.L1
    const inputCost = (props.inputTokens / 1000000) * rate.input
    const outputCost = (props.outputTokens / 1000000) * rate.output
    const cacheSavings = props.useCache ? inputCost * 0.9 * 0.6 : 0

    cost.value = {
      input_cost: inputCost,
      output_cost: outputCost,
      cache_savings: cacheSavings,
      total_cost: inputCost + outputCost - cacheSavings
    }
  } finally {
    loading.value = false
  }
}

defineExpose({ estimate })
</script>
