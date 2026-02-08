import api from './index'

export const aiApi = {
  generate(data) {
    return api.post('/api/v1/ai/generate', data)
  },

  // Returns URL for SSE streaming via fetch
  getStreamUrl() {
    return (api.defaults.baseURL || '') + '/api/v1/ai/generate/stream'
  },

  audit(data) {
    return api.post('/api/v1/ai/audit', data)
  },

  rewrite(data) {
    return api.post('/api/v1/ai/rewrite', data)
  },

  estimateCost(data) {
    return api.post('/api/v1/ai/estimate', data)
  },

  getModels() {
    return api.get('/api/v1/ai/models')
  },

  getStrategies() {
    return api.get('/api/v1/ai/strategies')
  }
}
