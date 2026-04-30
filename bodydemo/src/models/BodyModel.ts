import type { BodyMeasurements } from './BodyMeasurements';
import { getConfigByKey } from './BodyPartConfig';

export type BMIStatus = 'underweight' | 'normal' | 'overweight' | 'obese';
export type PartStatus = 'normal' | 'warning' | 'danger';
export type Gender = 'male' | 'female';

export interface BodyComparison {
  current: BodyMeasurements;
  previous: BodyMeasurements | null;
  changes: Partial<Record<keyof BodyMeasurements, number>>;
}

type MeasurementKey = keyof BodyMeasurements;
const NUMERIC_KEYS: MeasurementKey[] = [
  'height', 'weight',
  'neck', 'shoulderWidth', 'chest', 'waist', 'hip',
  'leftUpperArm', 'rightUpperArm', 'leftForearm', 'rightForearm',
  'leftThigh', 'rightThigh', 'leftCalf', 'rightCalf',
  'bodyFat', 'muscleMass', 'waterPercentage', 'visceralFatLevel', 'bmr', 'boneMass',
];

export class BodyModel {
  private data: BodyMeasurements;
  private gender: Gender;

  constructor(data: BodyMeasurements, gender: Gender = 'male') {
    this.data = data;
    this.gender = gender;
  }

  get raw(): BodyMeasurements {
    return this.data;
  }

  get currentGender(): Gender {
    return this.gender;
  }

  setGender(gender: Gender) {
    this.gender = gender;
  }

  getBMI(): number {
    const h = this.data.height / 100;
    if (h <= 0) return 0;
    return this.data.weight / (h * h);
  }

  getBMIStatus(): BMIStatus {
    const bmi = this.getBMI();
    if (bmi < 18.5) return 'underweight';
    if (bmi < 24) return 'normal';
    if (bmi < 28) return 'overweight';
    return 'obese';
  }

  getWaistToHipRatio(): number {
    if (this.data.hip <= 0) return 0;
    return this.data.waist / this.data.hip;
  }

  getFFMI(): number {
    const h = this.data.height / 100;
    if (h <= 0) return 0;
    const fatMass = this.data.weight * (this.data.bodyFat / 100);
    const leanMass = this.data.weight - fatMass;
    const ffmi = leanMass / (h * h);
    const normalized = ffmi + 6.1 * (1.8 - h);
    return Math.round(normalized * 100) / 100;
  }

  getBodyPartStatus(key: MeasurementKey): PartStatus {
    const config = getConfigByKey(key);
    if (!config) return 'normal';
    const value = this.data[key as keyof BodyMeasurements];
    if (typeof value !== 'number') return 'normal';
    const range = this.gender === 'female' ? config.normalRangeFemale : config.normalRange;
    const [lo, hi] = range;
    if (value >= lo && value <= hi) return 'normal';
    const margin = (hi - lo) * 0.3;
    if (value >= lo - margin && value <= hi + margin) return 'warning';
    return 'danger';
  }

  getIntensity(key: MeasurementKey): number {
    const config = getConfigByKey(key);
    if (!config) return 0;
    const value = this.data[key as keyof BodyMeasurements];
    if (typeof value !== 'number') return 0;
    const range = this.gender === 'female' ? config.normalRangeFemale : config.normalRange;
    const [lo, hi] = range;
    const rangeSize = hi - lo;
    if (rangeSize <= 0) return 0;
    const mid = (lo + hi) / 2;
    const deviation = Math.abs(value - mid) / (rangeSize / 2);
    return Math.min(10, Math.round(deviation * 10));
  }

  compare(other: BodyMeasurements): BodyComparison {
    const changes: Partial<Record<MeasurementKey, number>> = {};
    for (const key of NUMERIC_KEYS) {
      const curr = this.data[key];
      const prev = other[key];
      if (typeof curr === 'number' && typeof prev === 'number') {
        const diff = Math.round((curr - prev) * 100) / 100;
        if (diff !== 0) {
          changes[key] = diff;
        }
      }
    }
    return { current: this.data, previous: other, changes };
  }

  toJSON(): BodyMeasurements {
    return { ...this.data };
  }

  static fromJSON(json: Record<string, unknown>): BodyModel {
    return new BodyModel(json as unknown as BodyMeasurements);
  }

  static defaultMeasurements(): BodyMeasurements {
    const now = new Date().toISOString();
    return {
      id: crypto.randomUUID(),
      userId: 'demo',
      measureDate: now.slice(0, 10),
      height: 175,
      weight: 72,
      neck: 37,
      shoulderWidth: 42,
      chest: 96,
      waist: 82,
      hip: 96,
      leftUpperArm: 33,
      rightUpperArm: 33.5,
      leftForearm: 27,
      rightForearm: 27.5,
      leftThigh: 55,
      rightThigh: 55.5,
      leftCalf: 37,
      rightCalf: 37.5,
      bodyFat: 18,
      muscleMass: 38,
      waterPercentage: 57,
      visceralFatLevel: 5,
      bmr: 1650,
      boneMass: 3.0,
      createdAt: now,
      updatedAt: now,
    };
  }
}
