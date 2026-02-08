import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectApi } from '@/api/projects'
import { sectionApi } from '@/api/sections'

export const useProjectStore = defineStore('project', () => {
  // State
  const projects = ref([])
  const currentProject = ref(null)
  const sections = ref([])
  const currentSection = ref(null)
  const loading = ref(false)

  // Getters
  const projectCount = computed(() => projects.value.length)
  const sortedSections = computed(() =>
    [...sections.value].sort((a, b) => a.sort_order - b.sort_order)
  )

  // Flatten a tree into a flat list (for display)
  function flattenTree(tree, result = []) {
    for (const node of tree) {
      result.push(node)
      if (node.children?.length) {
        flattenTree(node.children, result)
      }
    }
    return result
  }

  // Project actions
  async function fetchProjects(params = {}) {
    loading.value = true
    try {
      const response = await projectApi.getProjects(params)
      projects.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id) {
    loading.value = true
    try {
      const response = await projectApi.getProject(id)
      currentProject.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function createProject(data) {
    const response = await projectApi.createProject(data)
    projects.value.unshift(response.data)
    return response.data
  }

  async function updateProject(id, data) {
    const response = await projectApi.updateProject(id, data)
    const index = projects.value.findIndex(p => p.id === id)
    if (index !== -1) {
      projects.value[index] = response.data
    }
    if (currentProject.value?.id === id) {
      currentProject.value = response.data
    }
    return response.data
  }

  async function deleteProject(id) {
    await projectApi.deleteProject(id)
    projects.value = projects.value.filter(p => p.id !== id)
    if (currentProject.value?.id === id) {
      currentProject.value = null
    }
  }

  // Section actions
  async function fetchSections(projectId) {
    loading.value = true
    try {
      const response = await sectionApi.getTree(projectId)
      // API returns a tree; flatten for list display but keep tree too
      const tree = response.data
      sections.value = flattenTree(tree)
      return tree
    } finally {
      loading.value = false
    }
  }

  async function fetchSection(sectionId) {
    const response = await sectionApi.getSection(sectionId)
    currentSection.value = response.data
    return response.data
  }

  async function createSection(projectId, data) {
    const response = await sectionApi.createSection({ project_id: projectId, ...data })
    sections.value.push(response.data)
    return response.data
  }

  async function updateSection(sectionId, data) {
    const response = await sectionApi.updateSection(sectionId, data)
    const index = sections.value.findIndex(s => s.id === sectionId)
    if (index !== -1) {
      sections.value[index] = response.data
    }
    if (currentSection.value?.id === sectionId) {
      currentSection.value = response.data
    }
    return response.data
  }

  async function deleteSection(sectionId) {
    await sectionApi.deleteSection(sectionId)
    sections.value = sections.value.filter(s => s.id !== sectionId)
    if (currentSection.value?.id === sectionId) {
      currentSection.value = null
    }
  }

  async function reorderSections(items) {
    // items = [{id, sort_order}, ...]
    await sectionApi.reorderSections(items)
    // Update local sort_order
    for (const item of items) {
      const section = sections.value.find(s => s.id === item.id)
      if (section) section.sort_order = item.sort_order
    }
  }

  function clearCurrentProject() {
    currentProject.value = null
    sections.value = []
    currentSection.value = null
  }

  return {
    projects,
    currentProject,
    sections,
    currentSection,
    loading,
    projectCount,
    sortedSections,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
    fetchSections,
    fetchSection,
    createSection,
    updateSection,
    deleteSection,
    reorderSections,
    clearCurrentProject
  }
})
