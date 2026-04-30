import api from './request';
import type { UserProfile, UserSettings } from '../types';

export const userApi = {
  getProfile: (): Promise<UserProfile> => api.get('/user/profile'),
  updateProfile: (data: { name?: string; avatar?: string }): Promise<void> =>
    api.put('/user/profile', data),
  getSettings: (): Promise<UserSettings> => api.get('/user/settings'),
  updateSettings: (data: Partial<UserSettings>): Promise<void> =>
    api.put('/user/settings', data),
};
