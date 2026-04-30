import api from './request';
import type { WeeklyStats, TrainingSchedule, WeeklyProgress, TrainingPlan } from '../types';

export const trainingApi = {
  getWeeklyStats: (): Promise<WeeklyStats> => api.get('/training/stats/weekly'),
  getWeeklySchedule: (): Promise<TrainingSchedule[]> => api.get('/training/schedule/weekly'),
  getWeeklyProgress: (): Promise<WeeklyProgress> => api.get('/training/progress/weekly'),
  createPlan: (data: TrainingPlan): Promise<{ planId: number }> =>
    api.post('/training/plans', data),
  completePlan: (planId: number, data: { actualDuration: number; actualIntensity?: string; caloriesBurned?: number; note?: string }): Promise<void> =>
    api.post(`/training/complete/${planId}`, data),
  deletePlan: (planId: number): Promise<void> => api.delete(`/training/plans/${planId}`),
};
