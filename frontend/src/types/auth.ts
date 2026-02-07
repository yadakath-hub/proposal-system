export interface User {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  avatar_url: string | null
  last_login_at: string | null
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginResponse {
  user: User
  tokens: TokenResponse
}

export interface LoginRequest {
  email: string
  password: string
}
