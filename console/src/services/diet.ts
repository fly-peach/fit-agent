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

// ---------------------------------------------------------------------------
// 食物数据库
// ---------------------------------------------------------------------------

export interface FoodItem {
  foodId: number
  name: string
  category: string
  source: 'system' | 'custom'
  portionUnit: string | null
  portionGrams: number | null
  portionCalories: number
  caloriesPer100g: number
  calorieLevel: string | null
  protein: number
  carbs: number
  fat: number
  suitableMeals: string
}

export const dietApi = {
  getTodayStats: (): Promise<DietStats> =>
    api.get('/diet/stats/today'),

  getTodayMeals: (targetDate?: string): Promise<DietMeal[]> =>
    api.get('/diet/meals/today', { params: targetDate ? { date: targetDate } : undefined }),

  createMeal: (data: { mealType: string; mealName: string; calories: number; protein?: number; carbs?: number; fat?: number; water?: number; time: string; note?: string; mealDate?: string }): Promise<{ mealId: number }> =>
    api.post('/diet/meals', data),

  updateMeal: (mealId: number, data: Partial<DietMeal>): Promise<void> =>
    api.put(`/api/diet/meals/${mealId}`, data),

  deleteMeal: (mealId: number): Promise<void> =>
    api.delete(`/api/diet/meals/${mealId}`),

  getNutritionProgress: (): Promise<NutritionProgress> =>
    api.get('/diet/nutrition/progress'),

  getRecommendations: (): Promise<RecommendedFood[]> =>
    api.get('/diet/recommendations'),

  getWeeklyTrend: (): Promise<WeeklyDietTrend> =>
    api.get('/diet/trend/weekly'),

  // 食物数据库
  searchFoods: (keyword = '', category = '', mealType = ''): Promise<FoodItem[]> =>
    api.get('/diet/foods', { params: { keyword, category, meal_type: mealType } }),

  getFoodCategories: (): Promise<string[]> =>
    api.get('/diet/foods/categories'),

  addCustomFood: (data: {
    name: string; category: string;
    portionUnit?: string; portionGrams?: number;
    portionCalories: number; caloriesPer100g: number;
    calorieLevel?: string;
    protein?: number; carbs?: number; fat?: number;
  }): Promise<{ foodId: number }> =>
    api.post('/diet/foods', data),

  deleteCustomFood: (foodId: number): Promise<void> =>
    api.delete(`/api/diet/foods/${foodId}`),

  getDateRangeTrend: (startDate: string, endDate: string): Promise<{
    dailyStats: {
      date: string
      calories: number
      protein: number
      carbs: number
      fat: number
      water: number
      proteinGoalMet: boolean
      waterGoalMet: boolean
      mealCount: number
    }[]
    goals: {
      caloriesGoal: number
      proteinGoal: number
      carbsGoal: number
      fatGoal: number
      waterGoal: number
    }
  }> =>
    api.get('/diet/trend/range', { params: { start_date: startDate, end_date: endDate } }),
}