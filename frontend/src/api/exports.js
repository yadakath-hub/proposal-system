import api from './index'

export const exportApi = {
  startExport(data) {
    return api.post('/api/v1/exports/', data)
  },

  getExportStatus(id) {
    return api.get(`/api/v1/exports/${id}/status`)
  },

  downloadExport(id) {
    return api.get(`/api/v1/exports/${id}/download`, {
      responseType: 'blob'
    })
  },

  getExportHistory(projectId) {
    return api.get(`/api/v1/exports/project/${projectId}`)
  },

  deleteExport(id) {
    return api.delete(`/api/v1/exports/${id}`)
  },

  getTemplates() {
    return api.get('/api/v1/exports/templates/')
  }
}
