import api from '../utils/request'

export interface ExerciseItem {
  exerciseId: number
  nameCn: string
  nameEn: string | null
  difficulty: string | null
  forceType: string | null
  mechanics: string | null
  exerciseType: string | null
  targetMuscle: string
  equipment: string | null
  isPinned: boolean
}

export interface ExerciseDetail {
  exerciseId: number
  nameCn: string
  nameEn: string | null
  difficulty: string | null
  forceType: string | null
  mechanics: string | null
  equipment: string | null
  exerciseType: string | null
  targetMuscle: string
  helperMuscles: string
  instructions: string[]
  isPinned: boolean
}

export interface PinnedExercise {
  pinId: number
  exerciseId: number
  nameCn: string
  nameEn: string | null
  difficulty: string | null
  forceType: string | null
  mechanics: string | null
  exerciseType: string | null
  targetMuscle: string
  equipment: string | null
  sortOrder: number
}

export interface PlanExerciseInput {
  exerciseId?: number
  customName?: string
  sets?: number
  reps?: number
  weight?: number
  duration?: number
  notes?: string
}

export interface PlanExerciseItemOutput {
  id: number
  exerciseId: number | null
  customName: string | null
  nameCn: string | null
  targetMuscle: string | null
  helperMuscles: string | null
  difficulty: string | null
  forceType: string | null
  mechanics: string | null
  equipment: string | null
  sets: number
  reps: number
  weight: number | null
  duration: number | null
  notes: string | null
}

export const exerciseApi = {
  listExercises: (params?: {
    keyword?: string
    targetMuscle?: string
    exerciseType?: string
    difficulty?: string
    equipment?: string
    forceType?: string
    mechanics?: string
    limit?: number
  }): Promise<ExerciseItem[]> =>
    api.get('/api/exercises', { params }),

  getExerciseDetail: (exerciseId: number): Promise<ExerciseDetail> =>
    api.get(`/api/exercises/${exerciseId}`),

  getMuscleCategories: (): Promise<string[]> =>
    api.get('/exercises/categories/muscles'),

  getTypeCategories: (): Promise<string[]> =>
    api.get('/exercises/categories/types'),

  getEquipmentCategories: (): Promise<string[]> =>
    api.get('/exercises/categories/equipment'),

  getForceTypeCategories: (): Promise<string[]> =>
    api.get('/exercises/categories/force-types'),

  getMechanicsCategories: (): Promise<string[]> =>
    api.get('/exercises/categories/mechanics'),

  // 收藏
  pinExercise: (exerciseId: number): Promise<void> =>
    api.post('/exercises/pin', { exerciseId }),

  unpinExercise: (exerciseId: number): Promise<void> =>
    api.delete(`/api/exercises/pin/${exerciseId}`),

  getPinnedExercises: (): Promise<PinnedExercise[]> =>
    api.get('/exercises/pinned'),

  reorderPinned: (exerciseIds: number[]): Promise<void> =>
    api.post('/exercises/pin/reorder', { exerciseIds }),
}
