import api from '../utils/request'

export interface HealthMetrics {
  weight: number
  height: number
  bodyFat: number
  bmi: number
  weightGoal: number | null
  bmiStatus: string
}

export interface HealthMeasurement {
  recordId: number
  weight: number
  bodyFat: number
  bmi: number
  measureDate: string
  createdAt: string
}

export interface HealthReport {
  weightTrend: { date: string; value: number }[]
  bmiTrend: { date: string; value: number }[]
  summary: {
    avgWeight: number
    avgBmi: number
    weightChange: number
    statusSummary: { pass: number; low: number; high: number }
  }
}

export const healthApi = {
  getMetrics: (): Promise<HealthMetrics> =>
    api.get('/health/metrics'),

  createMetric: (data: { weight?: number; bodyFat?: number; measureDate: string }): Promise<{ recordId: number }> =>
    api.post('/health/metrics', data),

  getMeasurements: (limit: number = 10): Promise<HealthMeasurement[]> =>
    api.get('/health/measurements', { params: { limit } }),

  getReport: (period: string = 'week'): Promise<HealthReport> =>
    api.get('/health/report', { params: { period } }),

  exportData: (period: string = 'week', format: string = 'csv') =>
    api.get('/health/export', { params: { period, format }, responseType: 'blob' }),
}