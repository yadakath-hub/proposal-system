import api from './index'

export const authApi = {
  login(email, password) {
    return api.post('/api/v1/auth/login', { email, password })
  },

  register(data) {
    return api.post('/api/v1/auth/register', data)
  },

  refreshToken(refreshToken) {
    return api.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
  },

  getMe() {
    return api.get('/api/v1/auth/me')
  },

  changePassword(data) {
    return api.post('/api/v1/auth/change-password', data)
  }
}
