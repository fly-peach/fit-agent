import api from '../utils/request'

export interface UserProfile {
  userId: number
  name: string
  email: string
  avatar: string | null
  role: string
  createdAt: string
}

export interface UserSettings {
  calorieGoal: number
  proteinGoal: number
  carbsGoal: number
  fatGoal: number
  waterGoal: number
  weightGoal: number | null
  weeklyTrainingGoal: number
  notificationEnabled: boolean
  reminderTime: string
}

export const userApi = {
  getProfile: (): Promise<UserProfile> =>
    api.get('/user/profile'),

  updateProfile: (data: { name?: string; avatar?: string }): Promise<void> =>
    api.put('/user/profile', data),

  getSettings: (): Promise<UserSettings> =>
    api.get('/user/settings'),

  updateSettings: (data: Partial<UserSettings>): Promise<void> =>
    api.put('/user/settings', data),
}