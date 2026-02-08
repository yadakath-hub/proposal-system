import api from './index'

export const requirementsApi = {
  // Analyze a tender document and extract requirements
  analyze(projectId, documentId, autoLink = true) {
    return api.post('/api/v1/requirements/analyze', {
      project_id: projectId,
      document_id: documentId,
      auto_link: autoLink
    }, { timeout: 120000 })
  },

  // List all requirements for a project
  getProjectRequirements(projectId) {
    return api.get(`/api/v1/requirements/project/${projectId}`)
  },

  // Get requirements linked to a section
  getSectionRequirements(sectionId) {
    return api.get(`/api/v1/requirements/section/${sectionId}`)
  },

  // Link requirements to a section
  linkRequirements(sectionId, requirementIds) {
    return api.post('/api/v1/requirements/link', {
      section_id: sectionId,
      requirement_ids: requirementIds
    })
  },

  // Remove a section-requirement link
  unlinkRequirement(linkId) {
    return api.delete(`/api/v1/requirements/link/${linkId}`)
  },

  // Toggle addressed status on a link
  markAddressed(linkId, isAddressed) {
    return api.patch(`/api/v1/requirements/link/${linkId}/addressed`, null, {
      params: { is_addressed: isAddressed }
    })
  },

  // Search requirements by keyword
  search(projectId, query, topK = 5) {
    return api.post('/api/v1/requirements/search', {
      project_id: projectId,
      query: query,
      top_k: topK
    })
  }
}
