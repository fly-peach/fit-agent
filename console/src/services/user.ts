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
  api_key_masked: string
  model_name: string
  is_custom_api_key: boolean
}

// Update request type can still include api_key
export interface AgentConfigUpdate {
  agents_md?: string
  soul_md?: string
  api_key?: string
  model_name?: string
}

export interface DefaultConfig {
  agents_md: string
  soul_md: string
  model_name: string
}

export const agentApi = {
  getConfig: (): Promise<AgentConfig> =>
    api.get('/agent/config'),

  updateConfig: (data: Partial<AgentConfigUpdate>): Promise<void> =>
    api.put('/agent/config', data),

  getDefaults: (): Promise<DefaultConfig> =>
    api.get('/agent/defaults'),
}

export interface AgentWorkspaceStatus {
  is_configured: boolean
  local_working_dir: string | null
}

export interface AgentWorkspaceConfig {
  id: number
  user_id: number
  local_working_dir: string
  last_used_at: string | null
  created_at: string
}

export const workspaceApi = {
  getStatus: (): Promise<AgentWorkspaceStatus> =>
    api.get('/agent/workspace/status'),

  createOrUpdate: (data: { local_working_dir?: string }): Promise<AgentWorkspaceConfig> =>
    api.post('/agent/workspace', data),

  update: (data: { local_working_dir: string }): Promise<AgentWorkspaceConfig> =>
    api.put('/agent/workspace', data),

  delete: (): Promise<void> =>
    api.delete('/agent/workspace'),
}