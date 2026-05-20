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

// ============================================================================
// Training Results Snapshots - 训练成果快照
// ============================================================================

export interface TrainingResultSnapshot {
  id: number
  userId: number
  sessionId?: string
  templateKey?: string
  title: string
  periodType?: 'week' | 'month' | 'custom'
  periodStart?: string
  periodEnd?: string
  thumbnail?: string
  statsJson?: string
  cardHtml?: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface TrainingResultTemplateSample {
  templateKey: string
  templateName: string
  templateGroup: string
  description: string
  highlights: string[]
  previewHtml: string
  promptHint: string
  sortOrder: number
}

export interface UpdateTrainingResultRequest {
  title?: string
  statsJson?: string
  thumbnail?: string
}

function mapTrainingResultSnapshot(raw: any): TrainingResultSnapshot {
  return {
    id: raw.id,
    userId: raw.userId ?? raw.user_id,
    sessionId: raw.sessionId ?? raw.session_id,
    templateKey: raw.templateKey ?? raw.template_key,
    title: raw.title,
    periodType: raw.periodType ?? raw.period_type,
    periodStart: raw.periodStart ?? raw.period_start,
    periodEnd: raw.periodEnd ?? raw.period_end,
    thumbnail: raw.thumbnail,
    statsJson: raw.statsJson ?? raw.stats_json,
    cardHtml: raw.cardHtml ?? raw.card_html,
    isActive: raw.isActive ?? raw.is_active,
    createdAt: raw.createdAt ?? raw.created_at,
    updatedAt: raw.updatedAt ?? raw.updated_at,
  }
}

function mapTrainingResultTemplateSample(raw: any): TrainingResultTemplateSample {
  return {
    templateKey: raw.templateKey ?? raw.template_key,
    templateName: raw.templateName ?? raw.template_name,
    templateGroup: raw.templateGroup ?? raw.template_group,
    description: raw.description ?? '',
    highlights: raw.highlights ?? [],
    previewHtml: raw.previewHtml ?? raw.preview_html ?? '',
    promptHint: raw.promptHint ?? raw.prompt_hint ?? '',
    sortOrder: raw.sortOrder ?? raw.sort_order ?? 0,
  }
}

export const trainingResultsApi = {
  listTemplates: async (templateGroup = 'training-results'): Promise<TrainingResultTemplateSample[]> => {
    const list = (await api.get('/training/result-templates', {
      params: { template_group: templateGroup },
    })) as any[]
    return (Array.isArray(list) ? list : []).map(mapTrainingResultTemplateSample)
  },

  getTemplate: async (templateKey: string): Promise<TrainingResultTemplateSample> =>
    mapTrainingResultTemplateSample(await api.get(`/training/result-templates/${templateKey}`)),

  listResults: async (params?: {
    periodType?: string
    sessionId?: string
    limit?: number
    offset?: number
  }): Promise<TrainingResultSnapshot[]> => {
    const list = (await api.get('/training/results/list', {
      params: params
        ? {
            period_type: params.periodType,
            session_id: params.sessionId,
            limit: params.limit,
            offset: params.offset,
          }
        : undefined,
    })) as any[]
    return (Array.isArray(list) ? list : []).map(mapTrainingResultSnapshot)
  },

  getResult: async (snapshotId: number): Promise<TrainingResultSnapshot> =>
    mapTrainingResultSnapshot(await api.get(`/training/results/${snapshotId}`)),

  updateResult: (snapshotId: number, data: UpdateTrainingResultRequest): Promise<void> =>
    api.put(`/training/results/${snapshotId}`, data),

  deleteResult: (snapshotId: number): Promise<void> =>
    api.delete(`/training/results/${snapshotId}`),
}
