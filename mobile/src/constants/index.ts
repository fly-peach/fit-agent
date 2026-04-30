export const API_BASE_URL = 'http://localhost:8000/api';

// Primary palette - deep blue to vibrant blue gradient
export const COLORS = {
  // Primary
  primary: '#4F6BF6',
  primaryDark: '#3B4FCC',
  primaryLight: '#6B82FC',

  // Gradients
  gradientStart: '#4F6BF6',
  gradientEnd: '#8B5CF6',

  // Status
  success: '#22C55E',
  successLight: '#DCFCE7',
  warning: '#F59E0B',
  warningLight: '#FEF3C7',
  danger: '#EF4444',
  dangerLight: '#FEE2E2',
  info: '#3B82F6',
  infoLight: '#DBEAFE',

  // Neutrals
  background: '#F0F2F5',
  card: '#FFFFFF',
  white: '#FFFFFF',
  text: '#1A1D2E',
  textSecondary: '#8C8FA3',
  textTertiary: '#B4B6C8',
  border: '#E8EAF0',
  divider: '#F0F1F5',

  // Accent backgrounds
  purpleBg: '#F0EDFF',
  blueBg: '#EBF0FF',
  greenBg: '#ECFDF5',
  orangeBg: '#FFF7ED',
  pinkBg: '#FDF2F8',
};

export const SHADOWS = {
  card: {
    shadowColor: '#4F6BF6',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
  },
  cardHover: {
    shadowColor: '#4F6BF6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 6,
  },
  small: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
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

export const BMI_STATUS_MAP: Record<string, { label: string; color: string; bg: string }> = {
  underweight: { label: '偏瘦', color: COLORS.warning, bg: COLORS.warningLight },
  normal: { label: '标准', color: COLORS.success, bg: COLORS.successLight },
  overweight: { label: '偏胖', color: COLORS.warning, bg: COLORS.warningLight },
  obese: { label: '肥胖', color: COLORS.danger, bg: COLORS.dangerLight },
};
