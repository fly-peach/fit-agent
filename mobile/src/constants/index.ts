export const API_BASE_URL = 'http://localhost:8000/api';

export const COLORS = {
  primary: '#0F5FFE',
  success: '#52c41a',
  warning: '#faad14',
  danger: '#ff4d4f',
  background: '#F5F5F5',
  white: '#FFFFFF',
  text: '#333333',
  textSecondary: '#999999',
  border: '#E8E8E8',
};

export const MEAL_TYPE_LABELS: Record<string, string> = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐',
};

export const MEAL_TYPE_ICONS: Record<string, string> = {
  breakfast: 'weather-sunset-up',
  lunch: 'white-balance-sunny',
  dinner: 'moon-waning-crescent',
  snack: 'cookie',
};

export const TRAINING_TYPE_LABELS: Record<string, string> = {
  strength: '力量训练',
  cardio: '有氧运动',
  stretch: '拉伸放松',
};

export const BMI_STATUS_MAP: Record<string, { label: string; color: string }> = {
  underweight: { label: '偏瘦', color: COLORS.success },
  normal: { label: '标准', color: COLORS.success },
  overweight: { label: '偏胖', color: COLORS.warning },
  obese: { label: '肥胖', color: COLORS.danger },
};
