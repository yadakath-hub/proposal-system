<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '編輯章節' : '新增章節'"
    width="500px"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="章節編號" prop="chapter_number">
        <el-input v-model="form.chapter_number" placeholder="例: 1、1.1、2.3" />
      </el-form-item>

      <el-form-item label="標題" prop="title">
        <el-input v-model="form.title" placeholder="請輸入章節標題" />
      </el-form-item>

      <el-form-item label="需求描述" prop="requirement_text">
        <el-input
          v-model="form.requirement_text"
          type="textarea"
          :rows="3"
          placeholder="說明此章節的需求"
        />
      </el-form-item>

      <el-form-item label="層級深度" prop="depth_level">
        <el-radio-group v-model="form.depth_level">
          <el-radio-button :value="0">第一層</el-radio-button>
          <el-radio-button :value="1">第二層</el-radio-button>
          <el-radio-button :value="2">第三層</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="預估頁數" prop="estimated_pages">
        <el-input-number v-model="form.estimated_pages" :min="1" :max="100" />
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
  section: Object,
  projectId: String
})

const emit = defineEmits(['update:visible', 'saved'])

const projectStore = useProjectStore()
const formRef = ref()
const loading = ref(false)

const isEdit = computed(() => !!props.section?.id)

const form = reactive({
  chapter_number: '',
  title: '',
  requirement_text: '',
  depth_level: 0,
  estimated_pages: 1
})

const rules = {
  chapter_number: [{ required: true, message: '請輸入章節編號', trigger: 'blur' }],
  title: [{ required: true, message: '請輸入章節標題', trigger: 'blur' }]
}

watch(() => props.visible, (val) => {
  if (val && props.section) {
    Object.assign(form, {
      chapter_number: props.section.chapter_number || '',
      title: props.section.title || '',
      requirement_text: props.section.requirement_text || '',
      depth_level: props.section.depth_level ?? 0,
      estimated_pages: props.section.estimated_pages || 1
    })
  } else if (val) {
    Object.assign(form, {
      chapter_number: '',
      title: '',
      requirement_text: '',
      depth_level: 0,
      estimated_pages: 1
    })
  }
})

async function handleSubmit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      if (isEdit.value) {
        await projectStore.updateSection(props.section.id, form)
        ElMessage.success('章節已更新')
      } else {
        await projectStore.createSection(props.projectId, form)
        ElMessage.success('章節已建立')
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
