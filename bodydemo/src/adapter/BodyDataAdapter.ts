import type { BodyMeasurements } from '../models/BodyMeasurements';
import { BodyModel } from '../models/BodyModel';

interface HealthMetrics {
  weight: number;
  height: number;
  bodyFat: number;
  bmi: number;
  weightGoal: number | null;
  bmiStatus: string;
}

export class BodyDataAdapter {
  static fromHealthMetrics(metrics: HealthMetrics): Partial<BodyMeasurements> {
    return {
      height: metrics.height,
      weight: metrics.weight,
      bodyFat: metrics.bodyFat,
    };
  }

  static fromAPIResponse(response: Record<string, unknown>): BodyModel {
    const data = response as unknown as BodyMeasurements;
    return new BodyModel(data);
  }

  static toAPIPayload(measurements: BodyMeasurements): Record<string, unknown> {
    const { ...payload } = measurements;
    return payload;
  }
}
