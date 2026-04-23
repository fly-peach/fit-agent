import api from '../utils/request'

export interface LoginParams {
  email: string
  password: string
}

export interface RegisterParams {
  name: string
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

  register: (params: RegisterParams): Promise<LoginResult> =>
    api.post('/auth/register', params),

  logout: () =>
    api.post('/auth/logout'),
}