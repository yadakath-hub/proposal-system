<template>
  <n-config-provider :theme="darkTheme" :locale="zhTW" :date-locale="dateZhTW">
    <n-message-provider>
      <n-dialog-provider>
        <router-view />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { darkTheme, zhTW, dateZhTW } from 'naive-ui'
</script>

<style>
body {
  margin: 0;
  padding: 0;
  background-color: #18181c;
}
</style>
