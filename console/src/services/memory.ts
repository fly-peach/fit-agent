import api from '../utils/request'

export interface MemoryContent {
  content: string
  last_updated: string
}

export interface DailyLog {
  date: string
  content: string
}

export interface OptimizationResult {
  success: boolean
  reason: string
  date: string
  backup_path: string | null
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
  optimize: (): Promise<OptimizationResult> =>
    api.post('/agent/memory/optimize'),
}
