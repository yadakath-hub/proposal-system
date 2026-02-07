import client from './client'
import type { LoginRequest, LoginResponse, TokenResponse, User } from '../types/auth'

export function login(data: LoginRequest) {
  return client.post<LoginResponse>('/auth/login', data)
}

export function getMe() {
  return client.get<User>('/auth/me')
}

export function refresh(refreshToken: string) {
  return client.post<TokenResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  })
}
