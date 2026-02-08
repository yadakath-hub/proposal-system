import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useProposalStore = defineStore('proposal', () => {
  // 當前專案
  const currentProject = ref(null)

  // 章節樹結構（支援多層級）
  const sectionTree = ref([])

  // 當前選中的章節
  const currentSection = ref(null)

  // 編輯模式
  const editMode = ref('edit') // 'edit' | 'preview'

  // 面板寬度
  const panelWidths = ref({
    sectionTree: 280,
    editor: 'flex-1',
    preview: 350
  })

  // 統計
  const stats = computed(() => {
    const all = flattenSections(sectionTree.value)
    return {
      total: all.length,
      completed: all.filter(s => s.status === 'Approved').length,
      generating: all.filter(s => s.status === 'Writing').length,
      pending: all.filter(s => s.status === 'NotStarted' || !s.status).length,
      totalWords: all.reduce((sum, s) => sum + (s.content?.length || 0), 0),
      estimatedPages: Math.ceil(all.reduce((sum, s) => sum + (s.content?.length || 0), 0) / 500)
    }
  })

  // 完成進度
  const progress = computed(() => {
    if (stats.value.total === 0) return 0
    return Math.round((stats.value.completed / stats.value.total) * 100)
  })

  // 扁平化章節樹
  function flattenSections(sections, result = []) {
    for (const section of sections) {
      result.push(section)
      if (section.children?.length) {
        flattenSections(section.children, result)
      }
    }
    return result
  }

  // 構建章節樹
  function buildSectionTree(sections) {
    const map = new Map()
    const roots = []

    sections.forEach(s => {
      map.set(s.id, { ...s, children: [] })
    })

    sections.forEach(s => {
      const node = map.get(s.id)
      if (s.parent_id && map.has(s.parent_id)) {
        map.get(s.parent_id).children.push(node)
      } else {
        roots.push(node)
      }
    })

    const sortNodes = (nodes) => {
      nodes.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
      nodes.forEach(n => {
        if (n.children?.length) sortNodes(n.children)
      })
    }
    sortNodes(roots)

    sectionTree.value = roots
  }

  function setCurrentSection(section) {
    currentSection.value = section
  }

  function toggleEditMode() {
    editMode.value = editMode.value === 'edit' ? 'preview' : 'edit'
  }

  return {
    currentProject,
    sectionTree,
    currentSection,
    editMode,
    panelWidths,
    stats,
    progress,
    buildSectionTree,
    setCurrentSection,
    toggleEditMode,
    flattenSections
  }
})
