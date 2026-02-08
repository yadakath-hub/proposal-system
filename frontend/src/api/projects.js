import api from './index'

export const projectApi = {
  getProjects(params = {}) {
    return api.get('/api/v1/projects/', { params })
  },

  getProject(id) {
    return api.get(`/api/v1/projects/${id}`)
  },

  createProject(data) {
    return api.post('/api/v1/projects/', data)
  },

  updateProject(id, data) {
    return api.put(`/api/v1/projects/${id}`, data)
  },

  deleteProject(id) {
    return api.delete(`/api/v1/projects/${id}`)
  },

  getBudget(id) {
    return api.get(`/api/v1/projects/${id}/budget`)
  }
}
