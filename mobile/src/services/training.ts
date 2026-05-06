import api from './request';
import type {
  WeeklyStats,
  TrainingSchedule,
  WeeklyProgress,
  TrainingPlan,
  PlanDetail,
  PlanExerciseInput,
} from '../types';

export const trainingApi = {
  getWeeklyStats: (): Promise<WeeklyStats> => api.get('/training/stats/weekly'),
  getWeeklySchedule: (): Promise<TrainingSchedule[]> => api.get('/training/schedule/weekly'),
  getMonthlySchedule: (year: number, month: number): Promise<TrainingSchedule[]> =>
    api.get('/training/schedule/monthly', { params: { year, month } }),
  getWeeklyProgress: (): Promise<WeeklyProgress> => api.get('/training/progress/weekly'),
  getDateRangeTrend: (startDate: string, endDate: string): Promise<{
    dailyStats: {
      date: string;
      duration: number;
      caloriesBurned: number;
      planCount: number;
    }[];
  }> => api.get('/training/trend/range', { params: { start_date: startDate, end_date: endDate } }),
  createPlan: (data: TrainingPlan): Promise<{ planId: number }> =>
    api.post('/training/plans', data),
  updatePlan: (planId: number, data: Partial<TrainingPlan>): Promise<void> =>
    api.put(`/training/plans/${planId}`, data),
  completePlan: (planId: number, data: { actualDuration: number; actualIntensity?: string; caloriesBurned?: number; note?: string }): Promise<void> =>
    api.post(`/training/complete/${planId}`, data),
  deletePlan: (planId: number): Promise<void> => api.delete(`/training/plans/${planId}`),
  getPlanDetail: (planId: number): Promise<PlanDetail> =>
    api.get(`/training/plans/${planId}/detail`),
  addPlanExercise: (planId: number, data: PlanExerciseInput): Promise<void> =>
    api.post(`/training/plans/${planId}/exercises`, data),
  updatePlanExercise: (exerciseId: number, data: { sets?: number; reps?: number; weight?: number; duration?: number }): Promise<void> =>
    api.put(`/training/plans/exercise/${exerciseId}`, data),
  deletePlanExercise: (exerciseId: number): Promise<void> =>
    api.delete(`/training/plans/exercise/${exerciseId}`),
  renewPlan: (planId: number): Promise<void> =>
    api.post(`/training/plans/${planId}/renew`),
};
