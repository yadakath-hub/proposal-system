import api from './index'

export const structureApi = {
  // Parse structure via form upload (image or PDF)
  parse(projectId, sourceType, file, textContent = null) {
    const formData = new FormData()
    formData.append('project_id', projectId)
    formData.append('source_type', sourceType)

    if (file) {
      formData.append('file', file)
    }
    if (textContent) {
      formData.append('text_content', textContent)
    }

    return api.post('/api/v1/structure/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000
    })
  },

  // Parse structure via base64 JSON body
  parseBase64(projectId, sourceType, content) {
    return api.post('/api/v1/structure/parse-base64', {
      project_id: projectId,
      source_type: sourceType,
      content: content
    }, { timeout: 60000 })
  },

  // Import parsed sections into a project
  import(projectId, sections, clearExisting = false) {
    return api.post('/api/v1/structure/import', {
      project_id: projectId,
      sections: sections,
      clear_existing: clearExisting
    })
  },

  // Get predefined structure templates
  getTemplates() {
    return api.get('/api/v1/structure/templates')
  }
}
