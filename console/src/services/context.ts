import api from '../utils/request'

export interface ContextStats {
  current_tokens: number
  max_tokens: number
  compaction_count_today: number
  compaction_count_total: number
  cache_file_count: number
  cache_total_size_bytes: number
  avg_response_tokens: number
}

export interface CacheEntry {
  id: string
  tool_name: string
  size_bytes: number
  created_at: string
}

export interface CompactResponse {
  success: boolean
  reason: string
}

export const contextApi = {
  getStats: (): Promise<ContextStats> => api.get('/agent/context/stats'),
  listCache: (): Promise<CacheEntry[]> => api.get('/agent/context/cache'),
  getCache: (id: string): Promise<{ content: string; id: string }> =>
    api.get(`/agent/context/cache/${id}`),
  clearCache: (): Promise<{ status: string; cleared: number }> =>
    api.delete('/agent/context/cache'),
  triggerCompact: (): Promise<CompactResponse> =>
    api.post('/agent/context/compact'),
}
