<template>
  <el-config-provider :locale="zhTw">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import zhTw from 'element-plus/dist/locale/zh-tw.mjs'
</script>
