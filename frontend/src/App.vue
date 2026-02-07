<template>
  <n-config-provider :theme="darkTheme" :locale="zhTW" :date-locale="dateZhTW">
    <n-message-provider>
      <n-dialog-provider>
        <div class="app-container">
          <n-card>
            <n-space vertical size="large">
              <n-h1>🚀 AI Proposal Generator</n-h1>
              <n-h2>智慧投標建議書生成系統</n-h2>
              
              <n-divider />
              
              <n-alert type="success" title="系統狀態">
                <n-space vertical>
                  <n-text>✅ Frontend: Running on Vue 3 + Naive UI</n-text>
                  <n-text>
                    🔗 Backend API: 
                    <n-tag type="info">{{ backendStatus }}</n-tag>
                  </n-text>
                </n-space>
              </n-alert>
              
              <n-space>
                <n-button type="primary" @click="checkBackend">
                  檢查後端連線
                </n-button>
                <n-button @click="openDocs">
                  開啟 API 文件
                </n-button>
              </n-space>
              
              <n-divider />
              
              <n-h3>📋 Phase 1 完成項目</n-h3>
              <n-list bordered>
                <n-list-item>✅ Docker Compose 環境配置</n-list-item>
                <n-list-item>✅ PostgreSQL 16 + pgvector</n-list-item>
                <n-list-item>✅ Redis 快取服務</n-list-item>
                <n-list-item>✅ MinIO 物件儲存</n-list-item>
                <n-list-item>✅ FastAPI 後端框架</n-list-item>
                <n-list-item>✅ Vue 3 + Naive UI 前端</n-list-item>
              </n-list>
            </n-space>
          </n-card>
        </div>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { darkTheme, zhTW, dateZhTW } from 'naive-ui'
import axios from 'axios'

const backendStatus = ref('未檢查')

const checkBackend = async () => {
  try {
    backendStatus.value = '連線中...'
    const response = await axios.get('http://localhost:8000/health')
    backendStatus.value = `${response.data.status} (${response.data.version})`
  } catch (error) {
    backendStatus.value = '連線失敗'
  }
}

const openDocs = () => {
  window.open('http://localhost:8000/docs', '_blank')
}

// Auto-check on mount
checkBackend()
</script>

<style>
body {
  margin: 0;
  padding: 0;
  background-color: #18181c;
}

.app-container {
  min-height: 100vh;
  padding: 40px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.n-card {
  max-width: 800px;
  width: 100%;
}
</style>
