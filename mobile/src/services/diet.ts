import api from './request';
import type { DietStats, DietMeal, NutritionProgress } from '../types';

export const dietApi = {
  getTodayStats: (): Promise<DietStats> => api.get('/diet/stats/today'),
  getTodayMeals: (): Promise<DietMeal[]> => api.get('/diet/meals/today'),
  createMeal: (data: { mealType: string; mealName: string; calories: number; protein?: number; carbs?: number; fat?: number; time: string; note?: string }): Promise<{ mealId: number }> =>
    api.post('/diet/meals', data),
  deleteMeal: (mealId: number): Promise<void> => api.delete(`/diet/meals/${mealId}`),
  getNutritionProgress: (): Promise<NutritionProgress> => api.get('/diet/nutrition/progress'),
};
