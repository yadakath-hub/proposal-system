import api from './index'

export const templateApi = {
  create(data) {
    return api.post('/api/v1/section-templates', data)
  },

  list(params = {}) {
    return api.get('/api/v1/section-templates', { params })
  },

  getCategories() {
    return api.get('/api/v1/section-templates/categories')
  },

  get(id) {
    return api.get(`/api/v1/section-templates/${id}`)
  },

  update(id, data, changeNote = null) {
    return api.put(`/api/v1/section-templates/${id}`, data, {
      params: changeNote ? { change_note: changeNote } : {}
    })
  },

  delete(id) {
    return api.delete(`/api/v1/section-templates/${id}`)
  },

  getVersions(id) {
    return api.get(`/api/v1/section-templates/${id}/versions`)
  },

  recommend(data) {
    return api.post('/api/v1/section-templates/recommend', data, { timeout: 60000 })
  },

  apply(templateId, sectionId, mode = 'replace') {
    return api.post('/api/v1/section-templates/apply', {
      template_id: templateId,
      section_id: sectionId,
      mode: mode
    })
  }
}
