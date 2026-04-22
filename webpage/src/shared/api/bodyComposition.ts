import { fetchWithAuth } from "./client";

export interface BodyCompositionRecord {
  id: number;
  member_id: number;
  assessment_id: number | null;
  measured_at: string;

  weight: number | null;
  bmi: number | null;
  body_fat_rate: number | null;
  visceral_fat_level: number | null;
  fat_mass: number | null;
  muscle_mass: number | null;
  skeletal_muscle_mass: number | null;
  skeletal_muscle_rate: number | null;
  water_rate: number | null;
  water_mass: number | null;
  bmr: number | null;

  // 新增指标
  muscle_rate: number | null;
  bone_mass: number | null;
  protein_mass: number | null;
  ideal_weight: number | null;
  weight_control: number | null;
  fat_control: number | null;
  muscle_control: number | null;
  body_type: string | null;
  nutrition_status: string | null;
  body_age: number | null;
  subcutaneous_fat: number | null;
  fat_free_mass: number | null;
  fat_burn_hr_low: number | null;
  fat_burn_hr_high: number | null;

  raw_payload: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface BodyCompositionCreatePayload {
  assessment_id?: number;
  measured_at: string;
  weight?: number;
  bmi?: number;
  body_fat_rate?: number;
  visceral_fat_level?: number;
  fat_mass?: number;
  muscle_mass?: number;
  skeletal_muscle_mass?: number;
  skeletal_muscle_rate?: number;
  water_rate?: number;
  water_mass?: number;
  bmr?: number;
  muscle_rate?: number;
  bone_mass?: number;
  protein_mass?: number;
  ideal_weight?: number;
  weight_control?: number;
  fat_control?: number;
  muscle_control?: number;
  body_type?: string;
  nutrition_status?: string;
  body_age?: number;
  subcutaneous_fat?: number;
  fat_free_mass?: number;
  fat_burn_hr_low?: number;
  fat_burn_hr_high?: number;
  raw_payload?: Record<string, any>;
}

export interface BodyCompositionTrendPoint {
  measured_at: string;
  value: number;
}

export interface BodyCompositionCompareResult {
  a: BodyCompositionRecord;
  b: BodyCompositionRecord;
  diff: Record<string, number>;
  diff_ratio: Record<string, number>;
  tags: string[];
}

export interface BodyCompositionEvaluateResult {
  body_type: string | null;
  nutrition_status: string | null;
  body_age: number | null;
  health_score: number;
  subcutaneous_fat: number | null;
  ideal_weight: number | null;
  weight_control: number | null;
  fat_control: number | null;
  muscle_control: number | null;
  fat_free_mass: number | null;
  fat_burn_hr_low: number | null;
  fat_burn_hr_high: number | null;
  indicator_levels: Record<string, string>;
}

export interface IndicatorConfigResult {
  groups: Record<string, {
    label: string;
    icon: string;
    indicators: string[];
  }>;
  level_colors: Record<string, string>;
}

export async function createBodyComposition(payload: BodyCompositionCreatePayload): Promise<BodyCompositionRecord> {
  const response = await fetchWithAuth("/body-composition", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  return result.data as BodyCompositionRecord;
}

export async function listBodyComposition(params?: { from?: string; to?: string; limit?: number }): Promise<BodyCompositionRecord[]> {
  const query = new URLSearchParams();
  if (params?.from) query.set("from", params.from);
  if (params?.to) query.set("to", params.to);
  if (params?.limit) query.set("limit", String(params.limit));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const response = await fetchWithAuth(`/body-composition${suffix}`);
  const result = await response.json();
  return result.data as BodyCompositionRecord[];
}

export async function getBodyComposition(id: number): Promise<BodyCompositionRecord> {
  const response = await fetchWithAuth(`/body-composition/${id}`);
  const result = await response.json();
  return result.data as BodyCompositionRecord;
}

export async function getBodyCompositionTrend(metric: string, params?: { from?: string; to?: string; limit?: number }): Promise<BodyCompositionTrendPoint[]> {
  const query = new URLSearchParams({ metric });
  if (params?.from) query.set("from", params.from);
  if (params?.to) query.set("to", params.to);
  if (params?.limit) query.set("limit", String(params.limit));
  const response = await fetchWithAuth(`/body-composition/trend?${query.toString()}`);
  const result = await response.json();
  return result.data as BodyCompositionTrendPoint[];
}

export async function compareBodyComposition(a: number, b: number): Promise<BodyCompositionCompareResult> {
  const response = await fetchWithAuth(`/body-composition/compare?a=${a}&b=${b}`);
  const result = await response.json();
  return result.data as BodyCompositionCompareResult;
}

export async function evaluateBodyComposition(id: number, params?: { height_cm?: number; actual_age?: number }): Promise<BodyCompositionEvaluateResult> {
  const query = new URLSearchParams();
  if (params?.height_cm) query.set("height_cm", String(params.height_cm));
  if (params?.actual_age) query.set("actual_age", String(params.actual_age));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const response = await fetchWithAuth(`/body-composition/evaluate/${id}${suffix}`);
  const result = await response.json();
  return result.data as BodyCompositionEvaluateResult;
}

export async function getIndicatorConfig(): Promise<IndicatorConfigResult> {
  const response = await fetchWithAuth("/body-composition/indicator-config");
  const result = await response.json();
  return result.data as IndicatorConfigResult;
}
