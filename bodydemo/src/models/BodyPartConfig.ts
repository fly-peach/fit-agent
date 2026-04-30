import type { CircumferenceKey, BodyCompKey, BodyMeasurements } from './BodyMeasurements';

export interface BodyPartConfig {
  key: CircumferenceKey | BodyCompKey | 'height' | 'weight';
  label: string;
  unit: string;
  icon: string;
  muscleIds: string[];
  normalRange: [number, number];
  normalRangeFemale: [number, number];
  side: 'left' | 'right' | 'center';
  category: 'circumference' | 'basic' | 'composition';
}

export const CIRCUMFERENCE_PARTS: BodyPartConfig[] = [
  { key: 'neck', label: '颈围', unit: 'cm', icon: '📏', muscleIds: ['neck-left', 'neck-right'], normalRange: [33, 40], normalRangeFemale: [30, 37], side: 'center', category: 'circumference' },
  { key: 'shoulderWidth', label: '肩宽', unit: 'cm', icon: '📐', muscleIds: ['shoulder-front-left', 'shoulder-side-left', 'shoulder-front-right', 'shoulder-side-right'], normalRange: [36, 46], normalRangeFemale: [34, 42], side: 'center', category: 'circumference' },
  { key: 'chest', label: '胸围', unit: 'cm', icon: '💪', muscleIds: ['chest-upper-left', 'chest-lower-left', 'chest-upper-right', 'chest-lower-right'], normalRange: [85, 110], normalRangeFemale: [80, 100], side: 'center', category: 'circumference' },
  { key: 'waist', label: '腰围', unit: 'cm', icon: '📏', muscleIds: ['obliques-left', 'obliques-right', 'abs-lower-left', 'abs-lower-right'], normalRange: [70, 90], normalRangeFemale: [65, 85], side: 'center', category: 'circumference' },
  { key: 'hip', label: '臀围', unit: 'cm', icon: '🍑', muscleIds: ['hip-flexor-left', 'hip-flexor-right'], normalRange: [85, 105], normalRangeFemale: [85, 105], side: 'center', category: 'circumference' },
  { key: 'leftUpperArm', label: '左上臂围', unit: 'cm', icon: '💪', muscleIds: ['biceps-left'], normalRange: [28, 38], normalRangeFemale: [24, 34], side: 'left', category: 'circumference' },
  { key: 'rightUpperArm', label: '右上臂围', unit: 'cm', icon: '💪', muscleIds: ['biceps-right'], normalRange: [28, 38], normalRangeFemale: [24, 34], side: 'right', category: 'circumference' },
  { key: 'leftForearm', label: '左前臂围', unit: 'cm', icon: '🤲', muscleIds: ['forearm-left'], normalRange: [24, 30], normalRangeFemale: [20, 26], side: 'left', category: 'circumference' },
  { key: 'rightForearm', label: '右前臂围', unit: 'cm', icon: '🤲', muscleIds: ['forearm-right'], normalRange: [24, 30], normalRangeFemale: [20, 26], side: 'right', category: 'circumference' },
  { key: 'leftThigh', label: '左大腿围', unit: 'cm', icon: '🦵', muscleIds: ['quads-left', 'adductors-left'], normalRange: [48, 62], normalRangeFemale: [44, 58], side: 'left', category: 'circumference' },
  { key: 'rightThigh', label: '右大腿围', unit: 'cm', icon: '🦵', muscleIds: ['quads-right', 'adductors-right'], normalRange: [48, 62], normalRangeFemale: [44, 58], side: 'right', category: 'circumference' },
  { key: 'leftCalf', label: '左小腿围', unit: 'cm', icon: '🦶', muscleIds: ['tibialis-anterior-left'], normalRange: [33, 42], normalRangeFemale: [30, 38], side: 'left', category: 'circumference' },
  { key: 'rightCalf', label: '右小腿围', unit: 'cm', icon: '🦶', muscleIds: ['tibialis-anterior-right'], normalRange: [33, 42], normalRangeFemale: [30, 38], side: 'right', category: 'circumference' },
];

export const BASIC_PARTS: BodyPartConfig[] = [
  { key: 'height', label: '身高', unit: 'cm', icon: '📏', muscleIds: [], normalRange: [160, 185], normalRangeFemale: [155, 175], side: 'center', category: 'basic' },
  { key: 'weight', label: '体重', unit: 'kg', icon: '⚖️', muscleIds: [], normalRange: [55, 85], normalRangeFemale: [48, 75], side: 'center', category: 'basic' },
];

export const COMPOSITION_PARTS: BodyPartConfig[] = [
  { key: 'bodyFat', label: '体脂率', unit: '%', icon: '📊', muscleIds: [], normalRange: [10, 25], normalRangeFemale: [18, 30], side: 'center', category: 'composition' },
  { key: 'muscleMass', label: '肌肉量', unit: 'kg', icon: '💪', muscleIds: [], normalRange: [30, 50], normalRangeFemale: [24, 40], side: 'center', category: 'composition' },
  { key: 'waterPercentage', label: '水分率', unit: '%', icon: '💧', muscleIds: [], normalRange: [50, 65], normalRangeFemale: [45, 60], side: 'center', category: 'composition' },
  { key: 'visceralFatLevel', label: '内脏脂肪', unit: '级', icon: '🔬', muscleIds: [], normalRange: [1, 9], normalRangeFemale: [1, 9], side: 'center', category: 'composition' },
  { key: 'bmr', label: '基础代谢', unit: 'kcal', icon: '🔥', muscleIds: [], normalRange: [1400, 2000], normalRangeFemale: [1100, 1700], side: 'center', category: 'composition' },
  { key: 'boneMass', label: '骨量', unit: 'kg', icon: '🦴', muscleIds: [], normalRange: [2.5, 3.5], normalRangeFemale: [2.2, 3.0], side: 'center', category: 'composition' },
];

export const ALL_PART_CONFIGS: BodyPartConfig[] = [...BASIC_PARTS, ...CIRCUMFERENCE_PARTS, ...COMPOSITION_PARTS];

export function getConfigByKey(key: string): BodyPartConfig | undefined {
  return ALL_PART_CONFIGS.find(c => c.key === key);
}

export function getMuscleIdToPartKeyMap(): Record<string, keyof BodyMeasurements> {
  const map: Record<string, keyof BodyMeasurements> = {};
  for (const config of ALL_PART_CONFIGS) {
    for (const mId of config.muscleIds) {
      map[mId] = config.key as keyof BodyMeasurements;
    }
  }
  return map;
}
