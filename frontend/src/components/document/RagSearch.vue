<template>
  <div class="rag-search">
    <el-input
      v-model="query"
      placeholder="輸入搜尋關鍵字..."
      :prefix-icon="Search"
      size="large"
      @keyup.enter="handleSearch"
    >
      <template #append>
        <el-button :loading="loading" @click="handleSearch">搜尋</el-button>
      </template>
    </el-input>

    <div class="mt-4" v-loading="loading">
      <div v-if="results.length > 0">
        <div
          v-for="(result, idx) in results"
          :key="idx"
          class="p-3 border rounded-lg mb-2 cursor-pointer hover:bg-blue-50 transition-colors"
          :class="selectedIds.has(idx) ? 'border-blue-500 bg-blue-50' : ''"
          @click="toggleSelect(idx)"
        >
          <div class="flex justify-between items-start mb-2">
            <el-checkbox :model-value="selectedIds.has(idx)" @click.stop />
            <el-tag size="small">相似度: {{ (result.score * 100).toFixed(1) }}%</el-tag>
          </div>
          <p class="text-sm text-gray-700">{{ result.chunk_text }}</p>
          <p class="text-xs text-gray-400 mt-1">
            來源: {{ result.source_type }} | 段落 #{{ result.chunk_index }}
          </p>
        </div>

        <div class="flex justify-end mt-4">
          <el-button type="primary" :disabled="selectedIds.size === 0" @click="confirmSelect">
            使用選中的 {{ selectedIds.size }} 段內容
          </el-button>
        </div>
      </div>

      <el-empty v-else-if="searched && !loading" description="未找到相關內容" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { documentApi } from '@/api/documents'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  projectId: { type: String, required: true }
})

const emit = defineEmits(['select'])

const query = ref('')
const loading = ref(false)
const searched = ref(false)
const results = ref([])
const selectedIds = ref(new Set())

async function handleSearch() {
  if (!query.value.trim()) {
    ElMessage.warning('請輸入搜尋關鍵字')
    return
  }

  loading.value = true
  searched.value = true

  try {
    const response = await documentApi.search(query.value, props.projectId, 10)
    results.value = response.data.results || []
    selectedIds.value = new Set()
  } catch (e) {
    ElMessage.error('搜尋失敗: ' + (e.response?.data?.detail || e.message))
    results.value = []
  } finally {
    loading.value = false
  }
}

function toggleSelect(idx) {
  const newSet = new Set(selectedIds.value)
  if (newSet.has(idx)) {
    newSet.delete(idx)
  } else {
    newSet.add(idx)
  }
  selectedIds.value = newSet
}

function confirmSelect() {
  const selected = results.value.filter((_, idx) => selectedIds.value.has(idx))
  emit('select', selected)
}
</script>
