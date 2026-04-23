import api from '../utils/request'

export interface WeeklyStats {
  weeklyCount: number
  weeklyHours: number
  weeklyCalories: number
  streakDays: number
  completedCount: number
  remainingCount: number
}

export interface TrainingSchedule {
  dayOfWeek: number
  date: string
  planName: string
  planType: string
  duration: number
  intensity: string
  status: string
  completedAt: string | null
}

export interface WeeklyProgress {
  targetCount: number
  completedCount: number
  progressPercent: number
  daysProgress: { day: string; completed: boolean }[]
}

export interface RecommendedTraining {
  recommendId: number
  planName: string
  planType: string
  duration: number
  intensity: string
  caloriesBurn: number | null
  suitability: string | null
}

export interface TrainingPlan {
  planId?: number
  planName: string
  planType: string
  targetIntensity?: string
  estimatedDuration?: number
  scheduledDate: string
  note?: string
}

export const trainingApi = {
  getWeeklyStats: (): Promise<WeeklyStats> =>
    api.get('/training/stats/weekly'),

  getWeeklySchedule: (): Promise<TrainingSchedule[]> =>
    api.get('/training/schedule/weekly'),

  getWeeklyProgress: (): Promise<WeeklyProgress> =>
    api.get('/training/progress/weekly'),

  getRecommendations: (): Promise<RecommendedTraining[]> =>
    api.get('/training/recommendations'),

  createPlan: (data: TrainingPlan): Promise<{ planId: number }> =>
    api.post('/training/plans', data),

  updatePlan: (planId: number, data: Partial<TrainingPlan>): Promise<void> =>
    api.put(`/training/plans/${planId}`, data),

  completePlan: (planId: number, data: { actualDuration: number; actualIntensity?: string; caloriesBurned?: number; note?: string }): Promise<void> =>
    api.post(`/training/complete/${planId}`, data),

  deletePlan: (planId: number): Promise<void> =>
    api.delete(`/training/plans/${planId}`),
}