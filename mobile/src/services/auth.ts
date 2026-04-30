import api from './request';
import type { LoginParams, RegisterParams, LoginResult } from '../types';

export const authApi = {
  login: (params: LoginParams): Promise<LoginResult> =>
    api.post('/auth/login', params),

  register: (params: RegisterParams): Promise<LoginResult> =>
    api.post('/auth/register', params),

  logout: () => api.post('/auth/logout'),
};
