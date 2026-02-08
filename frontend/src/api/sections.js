import api from './index'

export const sectionApi = {
  // Get section tree for a project
  getTree(projectId) {
    return api.get(`/api/v1/sections/tree/${projectId}`)
  },

  // Get single section
  getSection(sectionId) {
    return api.get(`/api/v1/sections/${sectionId}`)
  },

  // Create section (project_id in body)
  createSection(data) {
    return api.post('/api/v1/sections/', data)
  },

  // Update section
  updateSection(sectionId, data) {
    return api.put(`/api/v1/sections/${sectionId}`, data)
  },

  // Delete section
  deleteSection(sectionId) {
    return api.delete(`/api/v1/sections/${sectionId}`)
  },

  // Reorder sections: items = [{id, sort_order}, ...]
  reorderSections(items) {
    return api.put('/api/v1/sections/reorder', { items })
  },

  // Lock / unlock
  lockSection(sectionId) {
    return api.post(`/api/v1/sections/${sectionId}/lock`)
  },

  unlockSection(sectionId) {
    return api.delete(`/api/v1/sections/${sectionId}/lock`)
  },

  // Versions
  getVersions(sectionId) {
    return api.get(`/api/v1/sections/${sectionId}/versions`)
  },

  createVersion(sectionId, data) {
    return api.post(`/api/v1/sections/${sectionId}/versions`, data)
  },

  setCurrentVersion(sectionId, versionId) {
    return api.put(`/api/v1/sections/${sectionId}/current-version`, { version_id: versionId })
  }
}
