import { fetchWithAuth } from "./client";

export interface Assessment {
  id: number;
  member_id: number;
  status: "draft" | "in_progress" | "completed";
  goal: string | null;
  risk_level: "low" | "medium" | "high" | null;
  questionnaire_summary: Record<string, any> | null;
  report_summary: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface AssessmentCreatePayload {
  goal?: string;
  questionnaire_summary?: Record<string, any>;
}

export interface AssessmentCompletePayload {
  risk_level: "low" | "medium" | "high";
  report_summary: Record<string, any>;
}

export interface AssessmentReport {
  id: number;
  status: string;
  risk_level: string | null;
  report_summary: Record<string, any> | null;
  completed_at: string | null;
}

export async function createAssessment(payload: AssessmentCreatePayload): Promise<Assessment> {
  const response = await fetchWithAuth("/assessments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  return result.data as Assessment;
}

export async function getAssessments(status?: string): Promise<Assessment[]> {
  const url = status ? `/assessments?status=${encodeURIComponent(status)}` : "/assessments";
  const response = await fetchWithAuth(url);
  const result = await response.json();
  return result.data as Assessment[];
}

export async function getAssessment(id: number): Promise<Assessment> {
  const response = await fetchWithAuth(`/assessments/${id}`);
  const result = await response.json();
  return result.data as Assessment;
}

export async function completeAssessment(id: number, payload: AssessmentCompletePayload): Promise<Assessment> {
  const response = await fetchWithAuth(`/assessments/${id}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  return result.data as Assessment;
}

export async function getAssessmentReport(id: number): Promise<AssessmentReport> {
  const response = await fetchWithAuth(`/assessments/${id}/report`);
  const result = await response.json();
  return result.data as AssessmentReport;
}
