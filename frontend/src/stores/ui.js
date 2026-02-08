import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const isLoading = ref(false)
  const sidebarCollapsed = ref(false)

  function setLoading(value) {
    isLoading.value = value
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return {
    isLoading,
    sidebarCollapsed,
    setLoading,
    toggleSidebar
  }
})
