// Memory service - placeholder for future implementation
export interface MemoryContent {
  id: number
  user_id: number
  category: string
  key: string
  value: string
  confidence: number
  source: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DailyLog {
  id: number
  user_id: number
  date: string
  summary: string
  created_at: string
}

export const memoryApi = {
  // Placeholder methods
}
