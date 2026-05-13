import api from '../utils/request'
import { PlanExerciseInput, PlanExerciseItemOutput } from './exercise'

export type { PlanExerciseInput, PlanExerciseItemOutput }

export interface WeeklyStats {
  weeklyCount: number
  weeklyHours: number
  weeklyCalories: number
  streakDays: number
  completedCount: number
  remainingCount: number
}

export interface TrainingSchedule {
  planId?: number
  dayOfWeek: number
  date: string
  planName: string
  planType: string
  duration: number
  intensity: string
  status: string
  isRecurring?: boolean
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
  isRecurring?: boolean
  exercises?: PlanExerciseInput[]
}

export interface PlanDetail {
  planId: number
  planName: string
  planType: string
  targetIntensity: string | null
  estimatedDuration: number | null
  scheduledDate: string | null
  status: string
  note: string | null
  exercises: PlanExerciseItemOutput[]
}

export const trainingApi = {
  getWeeklyStats: (): Promise<WeeklyStats> =>
    api.get('/training/stats/weekly'),

  getWeeklySchedule: (): Promise<TrainingSchedule[]> =>
    api.get('/training/schedule/weekly'),

  getMonthlySchedule: (year: number, month: number): Promise<{
    planId?: number
    date: string
    planName: string
    planType: string
    duration: number
    intensity: string
    status: string
    isRecurring?: boolean
  }[]> =>
    api.get('/training/schedule/monthly', { params: { year, month } }),

  getWeeklyProgress: (): Promise<WeeklyProgress> =>
    api.get('/training/progress/weekly'),

  getRecommendations: (): Promise<RecommendedTraining[]> =>
    api.get('/training/recommendations'),

  createPlan: (data: TrainingPlan): Promise<{ planId: number }> =>
    api.post('/training/plans', data),

  updatePlan: (planId: number, data: Partial<TrainingPlan>): Promise<void> =>
    api.put(`/api/training/plans/${planId}`, data),

  completePlan: (planId: number, data: { actualDuration: number; actualIntensity?: string; caloriesBurned?: number; note?: string; completedDate?: string }): Promise<void> =>
    api.post(`/api/training/complete/${planId}`, data),

  deletePlan: (planId: number): Promise<void> =>
    api.delete(`/api/training/plans/${planId}`),

  getDateRangeTrend: (startDate: string, endDate: string): Promise<{
    dailyStats: {
      date: string
      duration: number
      caloriesBurned: number
      planCount: number
    }[]
  }> =>
    api.get('/training/trend/range', { params: { start_date: startDate, end_date: endDate } }),

  getPlanDetail: (planId: number): Promise<PlanDetail> =>
    api.get(`/api/training/plans/${planId}/detail`),

  updatePlanExercise: (exerciseId: number, data: { sets?: number; reps?: number; weight?: number; duration?: number }): Promise<void> =>
    api.put(`/api/training/plans/exercise/${exerciseId}`, data),

  addPlanExercise: (planId: number, data: PlanExerciseInput): Promise<void> =>
    api.post(`/api/training/plans/${planId}/exercises`, data),

  deletePlanExercise: (exerciseId: number): Promise<void> =>
    api.delete(`/api/training/plans/exercise/${exerciseId}`),
}