<template>
  <div class="p-6">
    <!-- 頁面標題 -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold">範本庫管理</h1>
        <p class="text-gray-500 mt-1">管理章節範本，提升建議書撰寫效率</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">
        新增範本
      </el-button>
    </div>

    <!-- 分類統計卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-6">
      <el-card
        v-for="cat in categories"
        :key="cat.value"
        shadow="hover"
        class="cursor-pointer transition-all"
        :class="selectedCategory === cat.value ? 'border-blue-500 border-2' : ''"
        @click="filterByCategory(cat.value)"
      >
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ cat.count }}</p>
          <p class="text-xs text-gray-500 truncate">{{ cat.label }}</p>
        </div>
      </el-card>
    </div>

    <!-- 搜尋和篩選 -->
    <el-card class="mb-6">
      <div class="flex flex-wrap gap-4 items-center">
        <el-input
          v-model="searchQuery"
          placeholder="搜尋範本名稱或內容..."
          :prefix-icon="Search"
          clearable
          class="w-64"
          @input="debouncedSearch"
        />

        <el-select v-model="selectedCategory" placeholder="選擇分類" clearable class="w-40">
          <el-option
            v-for="cat in categories"
            :key="cat.value"
            :label="cat.label"
            :value="cat.value"
          />
        </el-select>

        <el-button :icon="Refresh" @click="loadTemplates">重新整理</el-button>

        <div class="flex-1 text-right text-sm text-gray-500">
          共 {{ total }} 個範本
        </div>
      </div>
    </el-card>

    <!-- 範本列表 -->
    <el-card v-loading="loading">
      <el-table :data="templates" @row-click="showTemplateDetail">
        <el-table-column label="名稱" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <span class="font-medium">{{ row.name }}</span>
              <el-tag size="small">v{{ row.version }}</el-tag>
            </div>
            <p class="text-xs text-gray-500 mt-1">{{ truncate(row.description, 50) }}</p>
          </template>
        </el-table-column>

        <el-table-column label="分類" width="120">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)" size="small">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="字數" width="80" prop="word_count" />
        <el-table-column label="使用次數" width="100" prop="usage_count" />

        <el-table-column label="更新時間" width="150">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click.stop="editTemplate(row)">編輯</el-button>
            <el-button text size="small" type="danger" @click.stop="deleteTemplate(row)">
              刪除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && templates.length === 0" description="尚無範本" />

      <div class="flex justify-center mt-4" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadTemplates"
        />
      </div>
    </el-card>

    <!-- 新增/編輯範本 Dialog -->
    <TemplateFormDialog
      v-model:visible="showFormDialog"
      :template="editingTemplate"
      :categories="categories"
      @saved="handleSaved"
    />

    <!-- 範本詳情 Dialog -->
    <TemplateDetailDialog
      v-model:visible="showDetailDialog"
      :template-id="selectedTemplateId"
      @edit="editTemplateFromDetail"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { templateApi } from '@/api/templates'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { useDebounceFn } from '@vueuse/core'
import TemplateFormDialog from '@/components/template/TemplateFormDialog.vue'
import TemplateDetailDialog from '@/components/template/TemplateDetailDialog.vue'

const loading = ref(false)
const templates = ref([])
const categories = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const selectedCategory = ref('')

const showFormDialog = ref(false)
const showDetailDialog = ref(false)
const editingTemplate = ref(null)
const selectedTemplateId = ref(null)

async function loadCategories() {
  try {
    const resp = await templateApi.getCategories()
    categories.value = resp.data.categories
  } catch {
    // ignore
  }
}

async function loadTemplates() {
  loading.value = true
  try {
    const resp = await templateApi.list({
      category: selectedCategory.value || undefined,
      search: searchQuery.value || undefined,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    })
    templates.value = resp.data.items
    total.value = resp.data.total
  } catch {
    ElMessage.error('載入範本失敗')
  } finally {
    loading.value = false
  }
}

const debouncedSearch = useDebounceFn(() => {
  currentPage.value = 1
  loadTemplates()
}, 300)

function filterByCategory(category) {
  selectedCategory.value = selectedCategory.value === category ? '' : category
  currentPage.value = 1
  loadTemplates()
}

function showCreateDialog() {
  editingTemplate.value = null
  showFormDialog.value = true
}

function editTemplate(row) {
  editingTemplate.value = row
  showFormDialog.value = true
}

function editTemplateFromDetail(template) {
  showDetailDialog.value = false
  editingTemplate.value = template
  showFormDialog.value = true
}

function showTemplateDetail(row) {
  selectedTemplateId.value = row.id
  showDetailDialog.value = true
}

async function deleteTemplate(template) {
  try {
    await ElMessageBox.confirm(`確定要刪除範本「${template.name}」嗎？`, '刪除確認', {
      type: 'warning'
    })
    await templateApi.delete(template.id)
    ElMessage.success('範本已刪除')
    loadTemplates()
    loadCategories()
  } catch {
    // cancelled or error
  }
}

function handleSaved() {
  loadTemplates()
  loadCategories()
}

function truncate(str, len) {
  if (!str) return ''
  return str.length > len ? str.substring(0, len) + '...' : str
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-TW')
}

function getCategoryLabel(value) {
  const cat = categories.value.find(c => c.value === value)
  return cat?.label || value
}

function getCategoryType(value) {
  const map = {
    introduction: 'primary',
    technical: 'success',
    solution: 'warning',
    security: 'danger',
    management: 'info'
  }
  return map[value] || ''
}

watch(selectedCategory, () => {
  currentPage.value = 1
  loadTemplates()
})

onMounted(() => {
  loadCategories()
  loadTemplates()
})
</script>
