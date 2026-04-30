export type CircumferenceKey =
  | 'neck'
  | 'shoulderWidth'
  | 'chest'
  | 'waist'
  | 'hip'
  | 'leftUpperArm'
  | 'rightUpperArm'
  | 'leftForearm'
  | 'rightForearm'
  | 'leftThigh'
  | 'rightThigh'
  | 'leftCalf'
  | 'rightCalf';

export type BodyCompKey =
  | 'bodyFat'
  | 'muscleMass'
  | 'waterPercentage'
  | 'visceralFatLevel'
  | 'bmr'
  | 'boneMass';

export interface BodyMeasurements {
  id: string;
  userId: string;
  measureDate: string;

  height: number;
  weight: number;

  neck: number;
  shoulderWidth: number;
  chest: number;
  waist: number;
  hip: number;
  leftUpperArm: number;
  rightUpperArm: number;
  leftForearm: number;
  rightForearm: number;
  leftThigh: number;
  rightThigh: number;
  leftCalf: number;
  rightCalf: number;

  bodyFat: number;
  muscleMass: number;
  waterPercentage: number;
  visceralFatLevel: number;
  bmr: number;
  boneMass: number;

  createdAt: string;
  updatedAt: string;
}
