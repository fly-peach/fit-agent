import api from '../utils/request'

export interface LoginParams {
  email: string
  password: string
}

export interface LoginResult {
  token: string
  user: {
    userId: number
    name: string
    email: string
    role: string
  }
}

export const authApi = {
  login: (params: LoginParams): Promise<LoginResult> =>
    api.post('/auth/login', params),

  logout: () =>
    api.post('/auth/logout'),
}