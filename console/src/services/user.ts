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

// --- 旧的配置接口类型（保留兼容性） ---
export interface AgentConfig {
  agents_md: string
  soul_md: string
  api_key_masked: string
  model_name: string
  is_custom_api_key: boolean
}

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

// --- 新的配置接口类型 ---

// API Key 相关
export interface SetApiKeyRequest {
  api_key: string
}

export interface ApiKeyStatusResponse {
  has_api_key: boolean
}

// 提示词相关
export interface PromptTemplatesResponse {
  agents_md: string
  soul_md: string
  updated_at: string | null
}

export interface UpdatePromptsRequest {
  agents_md?: string
  soul_md?: string
}

// 综合状态
export interface AgentConfigStatusV2 {
  has_api_key: boolean
  has_prompts: boolean
}

export const agentApi = {
  // --- 旧的 API（保留兼容性，建议使用新的 API） ---
  getConfig: (): Promise<AgentConfig> =>
    api.get('/agent/config'),

  updateConfig: (data: Partial<AgentConfigUpdate>): Promise<void> =>
    api.put('/agent/config', data),

  getDefaults: (): Promise<DefaultConfig> =>
    api.get('/agent/defaults'),

  // --- 新的 API ---
  // API Key 管理
  setApiKey: (data: SetApiKeyRequest): Promise<void> =>
    api.post('/agent/config/api-key', data),

  deleteApiKey: (): Promise<void> =>
    api.delete('/agent/config/api-key'),

  getApiKeyStatus: (): Promise<ApiKeyStatusResponse> =>
    api.get('/agent/config/api-key/status'),

  // 提示词管理
  getPrompts: (): Promise<PromptTemplatesResponse> =>
    api.get('/agent/config/prompts'),

  updatePrompts: (data: UpdatePromptsRequest): Promise<PromptTemplatesResponse> =>
    api.put('/agent/config/prompts', data),

  // 综合状态
  getConfigStatus: (): Promise<AgentConfigStatusV2> =>
    api.get('/agent/config/status'),
}

// --- 工作区 API（已废弃） ---
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