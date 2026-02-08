import api from './index'

export const documentApi = {
  upload(projectId, file, onProgress) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', projectId)

    return api.post('/api/v1/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress) {
          onProgress(Math.round((e.loaded * 100) / e.total))
        }
      }
    })
  },

  getDocuments(projectId) {
    return api.get(`/api/v1/documents/project/${projectId}`)
  },

  getDocument(id) {
    return api.get(`/api/v1/documents/${id}`)
  },

  deleteDocument(id) {
    return api.delete(`/api/v1/documents/${id}`)
  },

  processDocument(id) {
    return api.post(`/api/v1/documents/${id}/process`)
  },

  downloadDocument(id) {
    return api.get(`/api/v1/documents/${id}/download`, {
      responseType: 'blob'
    })
  },

  search(query, projectId, topK = 5) {
    return api.post('/api/v1/documents/search', {
      query,
      project_id: projectId,
      top_k: topK
    })
  }
}
