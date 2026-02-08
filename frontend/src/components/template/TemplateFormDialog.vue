<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '編輯範本' : '新增範本'"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="範本名稱" prop="name">
            <el-input v-model="form.name" placeholder="例如：公司簡介 - 科技業版" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="分類" prop="category">
            <el-select v-model="form.category" class="w-full">
              <el-option
                v-for="cat in categories"
                :key="cat.value"
                :label="cat.label"
                :value="cat.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="簡述此範本的適用場景"
        />
      </el-form-item>

      <el-form-item label="標籤">
        <el-select
          v-model="form.tags"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="新增標籤..."
          class="w-full"
        >
          <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
        </el-select>
      </el-form-item>

      <el-form-item label="範本內容" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="15"
          placeholder="請輸入範本內容..."
        />
        <div class="flex justify-between mt-2 text-sm text-gray-500">
          <span>字數：{{ form.content?.length || 0 }}</span>
          <span>可使用 {變數名} 作為佔位符</span>
        </div>
      </el-form-item>

      <el-form-item v-if="isEdit" label="變更說明">
        <el-input v-model="changeNote" placeholder="說明此次修改的內容（選填）" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSubmit">
        {{ isEdit ? '更新' : '建立' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { templateApi } from '@/api/templates'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: Boolean,
  template: Object,
  categories: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible', 'saved'])

const formRef = ref()
const saving = ref(false)
const changeNote = ref('')

const isEdit = computed(() => !!props.template?.id)

const form = reactive({
  name: '',
  category: '',
  description: '',
  content: '',
  tags: []
})

const rules = {
  name: [{ required: true, message: '請輸入範本名稱', trigger: 'blur' }],
  category: [{ required: true, message: '請選擇分類', trigger: 'change' }],
  content: [{ required: true, message: '請輸入範本內容', trigger: 'blur' }]
}

const commonTags = ['政府標案', '科技業', '金融業', '製造業', '服務業', '醫療業', '教育業', '通用']

watch(() => props.visible, async (val) => {
  if (val) {
    changeNote.value = ''
    if (props.template) {
      Object.assign(form, {
        name: props.template.name || '',
        category: props.template.category || '',
        description: props.template.description || '',
        content: props.template.content || '',
        tags: props.template.tags || []
      })
      // Load full content if missing (list view doesn't include content)
      if (!form.content && props.template.id) {
        try {
          const resp = await templateApi.get(props.template.id)
          form.content = resp.data.content
        } catch {
          // ignore
        }
      }
    } else {
      Object.assign(form, {
        name: '',
        category: '',
        description: '',
        content: '',
        tags: []
      })
    }
  }
})

async function handleSubmit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      if (isEdit.value) {
        await templateApi.update(props.template.id, form, changeNote.value)
        ElMessage.success('範本已更新')
      } else {
        await templateApi.create(form)
        ElMessage.success('範本已建立')
      }
      emit('saved')
      handleClose()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '操作失敗')
    } finally {
      saving.value = false
    }
  })
}

function handleClose() {
  emit('update:visible', false)
}
</script>
