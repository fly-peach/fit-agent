import api from './request';
import type { HealthMetrics, HealthMeasurement, HealthReport } from '../types';

export const healthApi = {
  getMetrics: (): Promise<HealthMetrics> => api.get('/health/metrics'),
  createMetric: (data: { weight?: number; height?: number; bodyFat?: number; measureDate: string }): Promise<{ recordId: number }> =>
    api.post('/health/metrics', data),
  getMeasurements: (limit: number = 10): Promise<HealthMeasurement[]> =>
    api.get('/health/measurements', { params: { limit } }),
  getReport: (period: string = 'week'): Promise<HealthReport> =>
    api.get('/health/report', { params: { period } }),
  exportData: (period: string = 'week', format: string = 'csv') =>
    api.get('/health/export', { params: { period, format }, responseType: 'blob' }),
};
