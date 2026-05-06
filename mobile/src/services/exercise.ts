import api from './request';
import type {
  ExerciseItem,
  ExerciseDetail,
  PinnedExercise,
} from '../types';

export const exerciseApi = {
  listExercises: (params?: {
    keyword?: string;
    targetMuscle?: string;
    exerciseType?: string;
    difficulty?: string;
    equipment?: string;
    forceType?: string;
    mechanics?: string;
    limit?: number;
  }): Promise<ExerciseItem[]> =>
    api.get('/exercises', { params }),

  getExerciseDetail: (exerciseId: number): Promise<ExerciseDetail> =>
    api.get(`/exercises/${exerciseId}`),

  getMuscleCategories: (): Promise<string[]> =>
    api.get('/exercises/categories/muscles'),

  getTypeCategories: (): Promise<string[]> =>
    api.get('/exercises/categories/types'),

  getEquipmentCategories: (): Promise<string[]> =>
    api.get('/exercises/categories/equipment'),

  pinExercise: (exerciseId: number): Promise<void> =>
    api.post('/exercises/pin', { exerciseId }),

  unpinExercise: (exerciseId: number): Promise<void> =>
    api.delete(`/exercises/pin/${exerciseId}`),

  getPinnedExercises: (): Promise<PinnedExercise[]> =>
    api.get('/exercises/pinned'),

  reorderPinned: (exerciseIds: number[]): Promise<void> =>
    api.post('/exercises/pin/reorder', { exerciseIds }),
};

