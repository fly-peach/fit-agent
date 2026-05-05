import api from '../utils/request'

export interface Skill {
  name: string
  version: string
  description: string
  enabled: boolean
  path: string
  tags: string[]
  channels: string[]
  source: string
}

export interface SkillDetail extends Skill {
  content: string
  body: string
  references: string[]
  scripts: string[]
  config: Record<string, any>
}

export interface SkillPackageConfig {
  name: string
  enabled: boolean
  auto_update: boolean
  priority: number
  config: Record<string, any>
}

export interface SkillSystemConfig {
  version: string
  initialized: boolean
  initialized_at: string | null
  last_synced_at: string | null
  default_skills_enabled: string[]
  skill_packages: Record<string, SkillPackageConfig>
  global_settings: Record<string, any>
}

export interface SkillSyncStatus {
  initialized: boolean
  initialized_at: string | null
  last_synced_at: string | null
  total_skill_packages: number
  total_scanned_skills: number
  enabled_skills: string[]
}

export interface InitializeConfigRequest {
  default_skill_names: string[]
}

export interface UpdateSkillPackageRequest {
  enabled?: boolean
  auto_update?: boolean
  priority?: number
  config?: Record<string, any>
}

export interface SyncConfigRequest {
  direction: 'two-way' | 'to-config' | 'from-config'
}

export const skillApi = {
  // 技能基本管理
  list: (): Promise<Skill[]> => api.get('/agent/skills'),
  get: (name: string): Promise<SkillDetail> => api.get(`/agent/skills/${name}`),
  getFile: (name: string, filePath: string): Promise<{ content: string }> =>
    api.get(
      `/agent/skills/${name}/files/${filePath
        .split('/')
        .map((segment) => encodeURIComponent(segment))
        .join('/')}`
    ),
  enable: (name: string): Promise<{ status: string; name: string; enabled: boolean }> =>
    api.put(`/agent/skills/${name}/enable`),
  disable: (name: string): Promise<{ status: string; name: string; enabled: boolean }> =>
    api.put(`/agent/skills/${name}/disable`),
  upload: (file: File): Promise<{ status: string; name: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/agent/skills/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  delete: (name: string): Promise<{ status: string; name: string }> =>
    api.delete(`/agent/skills/${name}`),

  // 技能配置管理
  getConfig: (): Promise<SkillSystemConfig> =>
    api.get('/agent/skills/config'),

  getSyncStatus: (): Promise<SkillSyncStatus> =>
    api.get('/agent/skills/config/sync-status'),

  initializeConfig: (data: InitializeConfigRequest): Promise<SkillSystemConfig> =>
    api.post('/agent/skills/config/initialize', data),

  syncConfig: (data: SyncConfigRequest): Promise<SkillSystemConfig> =>
    api.post('/agent/skills/config/sync', data),

  updateSkillPackage: (name: string, data: UpdateSkillPackageRequest): Promise<SkillSystemConfig> =>
    api.put(`/agent/skills/config/packages/${name}`, data),

  resetConfig: (): Promise<SkillSystemConfig> =>
    api.delete('/agent/skills/config/reset'),

  // 重新补充模板技能
  restockTemplates: (): Promise<{ status: string; restocked: string[] }> =>
    api.post('/agent/skills/restock-templates'),
}
