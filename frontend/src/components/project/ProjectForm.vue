<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '編輯專案' : '新增專案'"
    width="500px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="專案名稱" prop="name">
        <el-input v-model="form.name" placeholder="請輸入專案名稱" />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="請輸入專案描述"
        />
      </el-form-item>

      <el-form-item label="標案編號" prop="tender_number">
        <el-input v-model="form.tender_number" placeholder="請輸入標案編號" />
      </el-form-item>

      <el-form-item label="狀態" prop="status" v-if="isEdit">
        <el-select v-model="form.status" class="w-full">
          <el-option label="草稿" value="Draft" />
          <el-option label="進行中" value="InProgress" />
          <el-option label="已完成" value="Completed" />
          <el-option label="已封存" value="Archived" />
        </el-select>
      </el-form-item>

      <el-form-item label="截止日期" prop="deadline">
        <el-date-picker
          v-model="form.deadline"
          type="date"
          placeholder="選擇截止日期"
          class="w-full"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="Token 預算" prop="max_token_budget">
        <el-input-number
          v-model="form.max_token_budget"
          :min="10000"
          :step="100000"
          class="w-full"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        {{ isEdit ? '更新' : '建立' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: Boolean,
  project: Object
})

const emit = defineEmits(['update:visible', 'saved'])

const projectStore = useProjectStore()
const formRef = ref()
const loading = ref(false)

const isEdit = computed(() => !!props.project?.id)

const form = reactive({
  name: '',
  description: '',
  tender_number: '',
  status: 'Draft',
  deadline: null,
  max_token_budget: 1000000
})

const rules = {
  name: [{ required: true, message: '請輸入專案名稱', trigger: 'blur' }]
}

watch(() => props.visible, (val) => {
  if (val && props.project) {
    Object.assign(form, {
      name: props.project.name || '',
      description: props.project.description || '',
      tender_number: props.project.tender_number || '',
      status: props.project.status || 'Draft',
      deadline: props.project.deadline || null,
      max_token_budget: props.project.max_token_budget || 1000000
    })
  } else if (val) {
    Object.assign(form, {
      name: '',
      description: '',
      tender_number: '',
      status: 'Draft',
      deadline: null,
      max_token_budget: 1000000
    })
  }
})

async function handleSubmit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const data = { ...form }
      // Remove empty optional fields
      if (!data.description) delete data.description
      if (!data.tender_number) delete data.tender_number
      if (!data.deadline) delete data.deadline

      if (isEdit.value) {
        await projectStore.updateProject(props.project.id, data)
        ElMessage.success('專案已更新')
      } else {
        delete data.status // new projects don't need status
        await projectStore.createProject(data)
        ElMessage.success('專案已建立')
      }
      emit('saved')
      handleClose()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '操作失敗')
    } finally {
      loading.value = false
    }
  })
}

function handleClose() {
  emit('update:visible', false)
  formRef.value?.resetFields()
}
</script>
