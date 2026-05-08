import api from '../utils/request'

export interface MemoryContent {
  content: string
  last_updated: string
}

export interface DailyLog {
  date: string
  content: string
}

export interface ActiveHours {
  start: string
  end: string
}

export interface HeartbeatConfig {
  enabled: boolean
  every: string
  target: string
  active_hours: ActiveHours | null
}

export interface MemoryConfig {
  heartbeat: HeartbeatConfig
}

export const memoryApi = {
  get: (): Promise<MemoryContent> => api.get('/agent/memory'),
  update: (content: string): Promise<{ status: string }> =>
    api.put('/agent/memory', { content }),
  listLogs: (): Promise<string[]> => api.get('/agent/memory/logs'),
  getLog: (date: string): Promise<DailyLog> =>
    api.get(`/agent/memory/logs/${date}`),
  deleteLog: (date: string): Promise<{ status: string; date: string }> =>
    api.delete(`/agent/memory/logs/${date}`),
  // 记忆 + 心跳配置
  getConfig: (): Promise<MemoryConfig> => api.get('/agent/memory/config'),
  updateConfig: (config: Partial<MemoryConfig>): Promise<{ status: string }> =>
    api.put('/agent/memory/config', config),

  // HEARTBEAT.md 读写
  getHeartbeatDoc: (): Promise<{ content: string }> =>
    api.get('/agent/memory/heartbeat-doc'),
  updateHeartbeatDoc: (content: string): Promise<{ status: string }> =>
    api.put('/agent/memory/heartbeat-doc', { content }),
}
