import { fetchWithAuth } from "./client";
import type { UserPublic } from "./auth";
import type { Assessment } from "./assessment";
import type { BodyCompositionCompareResult, BodyCompositionRecord, BodyCompositionTrendPoint } from "./bodyComposition";
import type { MealData } from "./daily";

export interface DashboardMeData {
  me: UserPublic;
  latest_assessment: Assessment | null;
  body_composition_summary: {
    latest: BodyCompositionRecord | null;
    trend: Record<string, BodyCompositionTrendPoint[]>;
    compare: BodyCompositionCompareResult | null;
  };
  growth_analytics: {
    metrics_latest: {
      record_date: string;
      weight: number | null;
      body_fat_rate: number | null;
      bmi: number | null;
      visceral_fat_level: number | null;
      bmr: number | null;
    } | null;
    workout_latest: {
      record_date: string;
      duration_minutes: number;
      is_completed: boolean;
    } | null;
    nutrition_latest: {
      record_date: string;
      calories_kcal: number;
      protein_g: number;
      carb_g: number;
      fat_g: number;
      breakfast: MealData;
      lunch: MealData;
      dinner: MealData;
    } | null;
    trends: Record<string, Array<{ record_date: string; value: number }>>;
    health_profile: Record<
      string,
      {
        label: string;
        value: number | null;
        unit: string;
        reference_range: string;
        reference_note: string;
        delta: number | null;
        status: "normal" | "blue" | "yellow" | "red";
      }
    >;
    goal_progress: {
      target_type: string;
      outer_week_change: number;
      outer_ring_percent: number;
      inner_achieve_percent: number;
      trend_4w: Array<{ record_date: string; value: number }>;
    };
    alerts: Array<{
      level: "blue" | "yellow" | "red";
      metric: string;
      message: string;
      action: string;
    }>;
  };
}

export async function getDashboardMe(): Promise<DashboardMeData> {
  const response = await fetchWithAuth("/dashboard/me");
  const result = await response.json();
  return result.data as DashboardMeData;
}
