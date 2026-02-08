<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-800">註冊帳號</h1>
        <p class="text-gray-500 mt-2">建立您的帳號</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
      >
        <el-form-item label="Email" prop="email">
          <el-input
            v-model="form.email"
            type="email"
            placeholder="請輸入 Email"
            size="large"
          />
        </el-form-item>

        <el-form-item label="姓名" prop="full_name">
          <el-input
            v-model="form.full_name"
            placeholder="請輸入姓名"
            size="large"
          />
        </el-form-item>

        <el-form-item label="密碼" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="請輸入密碼"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item label="確認密碼" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="請再次輸入密碼"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="w-full"
            :loading="loading"
            @click="handleRegister"
          >
            註冊
          </el-button>
        </el-form-item>
      </el-form>

      <div class="text-center mt-4">
        <span class="text-gray-500">已有帳號？</span>
        <router-link to="/login" class="text-blue-500 hover:text-blue-600 ml-1">
          立即登入
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  email: '',
  full_name: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('兩次輸入的密碼不一致'))
  } else {
    callback()
  }
}

const rules = {
  email: [
    { required: true, message: '請輸入 Email', trigger: 'blur' },
    { type: 'email', message: '請輸入有效的 Email', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '請輸入姓名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '請輸入密碼', trigger: 'blur' },
    { min: 6, message: '密碼至少 6 個字元', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '請確認密碼', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

async function handleRegister() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await authStore.register({
        email: form.email,
        full_name: form.full_name,
        password: form.password
      })
      ElMessage.success('註冊成功，請登入')
      router.push('/login')
    } catch (error) {
      // Error already handled by axios interceptor
    } finally {
      loading.value = false
    }
  })
}
</script>
