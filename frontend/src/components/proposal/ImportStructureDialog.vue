<template>
  <el-dialog
    :model-value="visible"
    title="匯入章節架構"
    width="600px"
    @close="$emit('update:visible', false)"
  >
    <el-empty description="此功能將在 Phase 8-2 實作">
      <p class="text-gray-500 text-sm">
        支援上傳截圖或 PDF，AI 自動解析章節結構並匯入
      </p>
    </el-empty>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">關閉</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
defineProps({
  visible: Boolean,
  projectId: [String, Number]
})

defineEmits(['update:visible', 'imported'])
</script>
