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

export interface AgentConfig {
  agents_md: string
  soul_md: string
  api_key: string
  api_key_masked: string
  model_name: string
  enable_thinking: boolean
  is_custom_api_key: boolean
}

export interface DefaultConfig {
  agents_md: string
  soul_md: string
  model_name: string
  enable_thinking: boolean
}

export const agentApi = {
  getConfig: (): Promise<AgentConfig> =>
    api.get('/agent/config'),

  updateConfig: (data: Partial<AgentConfig>): Promise<void> =>
    api.put('/agent/config', data),

  getDefaults: (): Promise<DefaultConfig> =>
    api.get('/agent/defaults'),
}