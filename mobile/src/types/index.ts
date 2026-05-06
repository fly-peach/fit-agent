// Auth
export interface LoginParams {
  email: string;
  password: string;
}

export interface RegisterParams {
  name: string;
  email: string;
  password: string;
}

export interface LoginResult {
  token: string;
  user: {
    userId: number;
    name: string;
    email: string;
    role: string;
  };
}

// User
export interface UserProfile {
  userId: number;
  name: string;
  email: string;
  avatar: string | null;
  role: string;
  createdAt: string;
}

export interface UserSettings {
  calorieGoal: number;
  proteinGoal: number;
  carbsGoal: number;
  fatGoal: number;
  waterGoal: number;
  weightGoal: number | null;
  weeklyTrainingGoal: number;
  notificationEnabled: boolean;
  reminderTime: string;
}

// Health
export interface HealthMetrics {
  weight: number;
  height: number;
  bodyFat: number;
  bmi: number;
  weightGoal: number | null;
  bmiStatus: string;
}

export interface HealthMeasurement {
  recordId: number;
  weight: number;
  bodyFat: number;
  bmi: number;
  bmiStatus: string;
  measureDate: string;
  createdAt: string;
}

export interface HealthReport {
  weightTrend: { date: string; value: number }[];
  bmiTrend: { date: string; value: number }[];
  summary: {
    avgWeight: number;
    avgBmi: number;
    weightChange: number;
    statusSummary: { normal: number; low: number; high: number };
  };
}

// Training
export interface WeeklyStats {
  weeklyCount: number;
  weeklyHours: number;
  weeklyCalories: number;
  streakDays: number;
  completedCount: number;
  remainingCount: number;
}

export interface TrainingSchedule {
  planId?: number;
  dayOfWeek: number;
  date: string;
  planName: string;
  planType: string;
  duration: number;
  intensity: string;
  status: string;
  isRecurring?: boolean;
  isLastInGroup?: boolean;
  completedAt: string | null;
}

export interface WeeklyProgress {
  targetCount: number;
  completedCount: number;
  progressPercent: number;
  daysProgress: { day: string; completed: boolean }[];
}

export interface TrainingPlan {
  planId?: number;
  planName: string;
  planType: string;
  targetIntensity?: string;
  estimatedDuration?: number;
  scheduledDate: string;
  note?: string;
  isRecurring?: boolean;
  exercises?: PlanExerciseInput[];
}

export interface PlanExerciseInput {
  exerciseId?: number;
  customName?: string;
  sets?: number;
  reps?: number;
  weight?: number;
  duration?: number;
  notes?: string;
}

export interface PlanExerciseItemOutput {
  id: number;
  exerciseId: number | null;
  customName: string | null;
  nameCn: string | null;
  targetMuscle: string | null;
  helperMuscles: string | null;
  difficulty: string | null;
  forceType: string | null;
  mechanics: string | null;
  equipment: string | null;
  sets: number;
  reps: number;
  weight: number | null;
  duration: number | null;
  notes: string | null;
}

export interface PlanDetail {
  planId: number;
  planName: string;
  planType: string;
  targetIntensity: string | null;
  estimatedDuration: number | null;
  scheduledDate: string | null;
  status: string;
  note: string | null;
  exercises: PlanExerciseItemOutput[];
}

// Diet
export interface DietStats {
  calories: number;
  caloriesGoal: number;
  remainingCalories: number;
  protein: number;
  proteinGoal: number;
  carbs: number;
  carbsGoal: number;
  fat: number;
  fatGoal: number;
  water: number;
  waterGoal: number;
  streakDays: number;
}

export interface DietMeal {
  mealId: number;
  mealType: string;
  mealName: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  time: string;
  note: string | null;
}

export interface NutritionProgress {
  protein: { current: number; goal: number; percent: number };
  carbs: { current: number; goal: number; percent: number };
  fat: { current: number; goal: number; percent: number };
}

export interface RecommendedFood {
  recommendId: number;
  foodName: string;
  calories: number;
  protein: number | null;
  reason: string | null;
  suitableTime: string | null;
}

export interface WeeklyDietTrend {
  dailyStats: { day: string; date: string; calories: number; proteinGoalMet: boolean; waterGoalMet: boolean }[];
  summary: { avgCalories: number; proteinGoalDays: number; waterGoalDays: number };
}

export interface FoodItem {
  foodId: number;
  name: string;
  category: string;
  source: 'system' | 'custom';
  portionUnit: string | null;
  portionGrams: number | null;
  portionCalories: number;
  caloriesPer100g: number;
  calorieLevel: string | null;
  protein: number;
  carbs: number;
  fat: number;
  suitableMeals: string;
}

// Exercise
export interface ExerciseItem {
  exerciseId: number;
  nameCn: string;
  nameEn: string | null;
  difficulty: string | null;
  forceType: string | null;
  mechanics: string | null;
  exerciseType: string | null;
  targetMuscle: string;
  equipment: string | null;
  isPinned: boolean;
}

export interface ExerciseDetail {
  exerciseId: number;
  nameCn: string;
  nameEn: string | null;
  difficulty: string | null;
  forceType: string | null;
  mechanics: string | null;
  equipment: string | null;
  exerciseType: string | null;
  targetMuscle: string;
  helperMuscles: string;
  instructions: string[];
  isPinned: boolean;
}

export interface PinnedExercise {
  pinId: number;
  exerciseId: number;
  nameCn: string;
  nameEn: string | null;
  difficulty: string | null;
  forceType: string | null;
  mechanics: string | null;
  exerciseType: string | null;
  targetMuscle: string;
  equipment: string | null;
  sortOrder: number;
}

// Chat
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  reasoning?: string;
}

export interface ChatSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  createdAt: string;
}
