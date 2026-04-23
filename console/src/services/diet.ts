import api from '../utils/request'

export interface DietStats {
  calories: number
  caloriesGoal: number
  remainingCalories: number
  protein: number
  proteinGoal: number
  carbs: number
  carbsGoal: number
  fat: number
  fatGoal: number
  water: number
  waterGoal: number
  streakDays: number
}

export interface DietMeal {
  mealId: number
  mealType: string
  mealName: string
  calories: number
  protein: number
  carbs: number
  fat: number
  time: string
  note: string | null
}

export interface NutritionProgress {
  protein: { current: number; goal: number; percent: number }
  carbs: { current: number; goal: number; percent: number }
  fat: { current: number; goal: number; percent: number }
}

export interface RecommendedFood {
  recommendId: number
  foodName: string
  calories: number
  protein: number | null
  reason: string | null
  suitableTime: string | null
}

export interface WeeklyDietTrend {
  dailyStats: { day: string; date: string; calories: number; proteinGoalMet: boolean; waterGoalMet: boolean }[]
  summary: { avgCalories: number; proteinGoalDays: number; waterGoalDays: number }
}

export const dietApi = {
  getTodayStats: (): Promise<DietStats> =>
    api.get('/diet/stats/today'),

  getTodayMeals: (): Promise<DietMeal[]> =>
    api.get('/diet/meals/today'),

  createMeal: (data: { mealType: string; mealName: string; calories: number; protein?: number; carbs?: number; fat?: number; water?: number; time: string; note?: string }): Promise<{ mealId: number }> =>
    api.post('/diet/meals', data),

  updateMeal: (mealId: number, data: Partial<DietMeal>): Promise<void> =>
    api.put(`/diet/meals/${mealId}`, data),

  deleteMeal: (mealId: number): Promise<void> =>
    api.delete(`/diet/meals/${mealId}`),

  getNutritionProgress: (): Promise<NutritionProgress> =>
    api.get('/diet/nutrition/progress'),

  getRecommendations: (): Promise<RecommendedFood[]> =>
    api.get('/diet/recommendations'),

  getWeeklyTrend: (): Promise<WeeklyDietTrend> =>
    api.get('/diet/trend/weekly'),
}