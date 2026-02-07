<template>
  <div class="login-container">
    <n-card title="登入系統" style="max-width: 420px; width: 100%">
      <n-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <n-form-item label="電子信箱" path="email">
          <n-input v-model:value="form.email" placeholder="請輸入電子信箱" />
        </n-form-item>
        <n-form-item label="密碼" path="password">
          <n-input
            v-model:value="form.password"
            type="password"
            show-password-on="click"
            placeholder="請輸入密碼"
            @keyup.enter="handleLogin"
          />
        </n-form-item>
        <n-alert v-if="errorMsg" type="error" :title="errorMsg" style="margin-bottom: 16px" />
        <n-button type="primary" block :loading="authStore.loading" @click="handleLogin">
          登入
        </n-button>
      </n-form>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInst, FormRules } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInst | null>(null)
const errorMsg = ref('')

const form = reactive({
  email: '',
  password: '',
})

const rules: FormRules = {
  email: [{ required: true, message: '請輸入電子信箱', trigger: 'blur' }],
  password: [{ required: true, message: '請輸入密碼', trigger: 'blur' }],
}

async function handleLogin() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  errorMsg.value = ''
  try {
    await authStore.login(form.email, form.password)
    router.push('/')
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || '登入失敗，請稍後再試'
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
}
</style>
