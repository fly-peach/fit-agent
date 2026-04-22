import { fetchWithAuth } from "./client";

export interface DailyMetrics {
  id: number;
  user_id: number;
  record_date: string;
  weight: number | null;
  body_fat_rate: number | null;
  bmi: number | null;
  created_at: string;
  updated_at: string;
}

export interface WorkoutItem {
  name: string;
  sets: number;
  reps: number;
  duration_minutes: number;
}

export interface DailyWorkoutPlan {
  id: number;
  user_id: number;
  record_date: string;
  plan_title: string;
  items: WorkoutItem[];
  duration_minutes: number;
  is_completed: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface MealData {
  calories_kcal: number;
  protein_g: number;
  carb_g: number;
  fat_g: number;
}

export interface DailyNutrition {
  id: number;
  user_id: number;
  record_date: string;
  calories_kcal: number;
  protein_g: number;
  carb_g: number;
  fat_g: number;
  notes: string | null;
  breakfast: MealData;
  lunch: MealData;
  dinner: MealData;
  created_at: string;
  updated_at: string;
}

type ApiWrap<T> = { code: number; message: string; data: T };

export async function upsertDailyMetrics(recordDate: string, payload: Partial<DailyMetrics>): Promise<DailyMetrics> {
  const resp = await fetchWithAuth(`/daily-metrics/${recordDate}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = (await resp.json()) as ApiWrap<DailyMetrics>;
  return result.data;
}

export async function listDailyMetrics(from?: string, to?: string): Promise<DailyMetrics[]> {
  const query = new URLSearchParams();
  if (from) query.set("from", from);
  if (to) query.set("to", to);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const resp = await fetchWithAuth(`/daily-metrics${suffix}`);
  const result = (await resp.json()) as ApiWrap<DailyMetrics[]>;
  return result.data;
}

export async function upsertDailyWorkout(
  recordDate: string,
  payload: Omit<DailyWorkoutPlan, "id" | "user_id" | "record_date" | "created_at" | "updated_at">
): Promise<DailyWorkoutPlan> {
  const resp = await fetchWithAuth(`/daily-workout/${recordDate}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = (await resp.json()) as ApiWrap<DailyWorkoutPlan>;
  return result.data;
}

export async function listDailyWorkout(from?: string, to?: string): Promise<DailyWorkoutPlan[]> {
  const query = new URLSearchParams();
  if (from) query.set("from", from);
  if (to) query.set("to", to);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const resp = await fetchWithAuth(`/daily-workout${suffix}`);
  const result = (await resp.json()) as ApiWrap<DailyWorkoutPlan[]>;
  return result.data;
}

export async function upsertDailyNutrition(
  recordDate: string,
  payload: {
    breakfast?: MealData;
    lunch?: MealData;
    dinner?: MealData;
    calories_kcal?: number;
    protein_g?: number;
    carb_g?: number;
    fat_g?: number;
    notes?: string | null;
  }
): Promise<DailyNutrition> {
  const resp = await fetchWithAuth(`/daily-nutrition/${recordDate}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = (await resp.json()) as ApiWrap<DailyNutrition>;
  return result.data;
}

export async function listDailyNutrition(from?: string, to?: string): Promise<DailyNutrition[]> {
  const query = new URLSearchParams();
  if (from) query.set("from", from);
  if (to) query.set("to", to);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const resp = await fetchWithAuth(`/daily-nutrition${suffix}`);
  const result = (await resp.json()) as ApiWrap<DailyNutrition[]>;
  return result.data;
}
