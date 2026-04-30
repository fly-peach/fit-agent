import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { dietApi } from '../../services/diet';
import { COLORS, SHADOWS, MEAL_TYPE_LABELS } from '../../constants';
import type { DietStats, DietMeal } from '../../types';

const MEAL_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  breakfast: 'sunny',
  lunch: 'partly-sunny',
  dinner: 'moon',
  snack: 'cafe',
};

const MEAL_COLORS: Record<string, [string, string]> = {
  breakfast: ['#F59E0B', '#FBBF24'],
  lunch: ['#3B82F6', '#60A5FA'],
  dinner: ['#8B5CF6', '#A78BFA'],
  snack: ['#EC4899', '#F472B6'],
};

export default function DietScreen() {
  const insets = useSafeAreaInsets();
  const [stats, setStats] = useState<DietStats | null>(null);
  const [meals, setMeals] = useState<DietMeal[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [mealType, setMealType] = useState('breakfast');
  const [mealName, setMealName] = useState('');
  const [calories, setCalories] = useState('');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [s, m] = await Promise.all([
        dietApi.getTodayStats().catch(() => null),
        dietApi.getTodayMeals().catch(() => []),
      ]);
      if (s) setStats(s);
      if (m) setMeals(m);
    } catch {}
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleAddMeal = async () => {
    if (!mealName.trim()) {
      Alert.alert('提示', '请输入食物内容');
      return;
    }
    setSubmitting(true);
    try {
      await dietApi.createMeal({
        mealType,
        mealName: mealName.trim(),
        calories: parseInt(calories) || 0,
        time: new Date().toTimeString().slice(0, 5),
        note: note.trim() || undefined,
      });
      setShowAddModal(false);
      setMealName('');
      setCalories('');
      setNote('');
      Alert.alert('成功', '饮食记录已添加');
      loadData();
    } catch (err: any) {
      Alert.alert('错误', err.message || '添加失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = (mealId: number) => {
    Alert.alert('确认', '确定删除该饮食记录？', [
      { text: '取消', style: 'cancel' },
      {
        text: '删除',
        style: 'destructive',
        onPress: async () => {
          try {
            await dietApi.deleteMeal(mealId);
            loadData();
          } catch (err: any) {
            Alert.alert('错误', err.message || '删除失败');
          }
        },
      },
    ]);
  };

  const calPercent = stats ? Math.min((stats.calories / stats.caloriesGoal) * 100, 100) : 0;
  const proteinPercent = stats ? Math.min((stats.protein / stats.proteinGoal) * 100, 100) : 0;
  const carbsPercent = stats ? Math.min((stats.carbs / stats.carbsGoal) * 100, 100) : 0;
  const fatPercent = stats ? Math.min((stats.fat / stats.fatGoal) * 100, 100) : 0;

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Compact Header */}
        <View style={[styles.header, { paddingTop: insets.top + 6 }]}>
          <Text style={styles.headerTitle}>饮食管理</Text>
          <Text style={styles.headerSub}>
            {new Date().getMonth() + 1}月{new Date().getDate()}日
          </Text>
        </View>

        {/* Calorie Card */}
        {stats && (
          <View style={[styles.card, { marginTop: 12 }]}>
            <Text style={styles.cardTitle}>今日热量摄入</Text>
            <View style={styles.calRow}>
              <Text style={styles.calValue}>{stats.calories}</Text>
              <Text style={styles.calUnit}>/ {stats.caloriesGoal} kcal</Text>
            </View>
            <View style={styles.progressTrack}>
              <LinearGradient
                colors={calPercent >= 100 ? [COLORS.danger, '#F87171'] : [COLORS.success, '#4ADE80']}
                style={[styles.progressFill, { width: `${calPercent}%` }]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
              />
            </View>
            <View style={styles.progressLabels}>
              <Text style={styles.progressText}>已摄入 {calPercent.toFixed(0)}%</Text>
              <Text style={styles.progressText}>剩余 {stats.remainingCalories} kcal</Text>
            </View>

            {/* Nutrition breakdown */}
            <View style={styles.divider} />
            <Text style={styles.nutritionTitle}>营养素摄入</Text>
            <View style={styles.nutritionGrid}>
              <View style={styles.nutritionItem}>
                <View style={styles.nutritionHeader}>
                  <View style={[styles.nutritionDot, { backgroundColor: '#3B82F6' }]} />
                  <Text style={styles.nutritionLabel}>蛋白质</Text>
                </View>
                <Text style={styles.nutritionValue}>{stats.protein}g <Text style={styles.nutritionGoal}>/ {stats.proteinGoal}g</Text></Text>
                <View style={styles.miniTrack}>
                  <View style={[styles.miniFill, { width: `${proteinPercent}%`, backgroundColor: '#3B82F6' }]} />
                </View>
              </View>
              <View style={styles.nutritionItem}>
                <View style={styles.nutritionHeader}>
                  <View style={[styles.nutritionDot, { backgroundColor: '#F59E0B' }]} />
                  <Text style={styles.nutritionLabel}>碳水</Text>
                </View>
                <Text style={styles.nutritionValue}>{stats.carbs}g <Text style={styles.nutritionGoal}>/ {stats.carbsGoal}g</Text></Text>
                <View style={styles.miniTrack}>
                  <View style={[styles.miniFill, { width: `${carbsPercent}%`, backgroundColor: '#F59E0B' }]} />
                </View>
              </View>
              <View style={styles.nutritionItem}>
                <View style={styles.nutritionHeader}>
                  <View style={[styles.nutritionDot, { backgroundColor: '#EF4444' }]} />
                  <Text style={styles.nutritionLabel}>脂肪</Text>
                </View>
                <Text style={styles.nutritionValue}>{stats.fat}g <Text style={styles.nutritionGoal}>/ {stats.fatGoal}g</Text></Text>
                <View style={styles.miniTrack}>
                  <View style={[styles.miniFill, { width: `${fatPercent}%`, backgroundColor: '#EF4444' }]} />
                </View>
              </View>
            </View>
          </View>
        )}

        {/* Meals Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>今日餐食</Text>
            <TouchableOpacity style={styles.addBtn} onPress={() => setShowAddModal(true)}>
              <Ionicons name="add" size={22} color={COLORS.white} />
            </TouchableOpacity>
          </View>
          {meals.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="restaurant-outline" size={48} color={COLORS.textTertiary} />
              <Text style={styles.emptyTitle}>暂无饮食记录</Text>
              <Text style={styles.emptySub}>点击右上角添加饮食记录</Text>
            </View>
          ) : (
            meals.map((meal, idx) => {
              const colors = MEAL_COLORS[meal.mealType] || ['#6B7280', '#9CA3AF'];
              return (
                <View key={meal.mealId || idx} style={styles.mealItem}>
                  <LinearGradient
                    colors={colors}
                    style={styles.mealIconWrap}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                  >
                    <Ionicons name={MEAL_ICONS[meal.mealType] || 'restaurant'} size={18} color={COLORS.white} />
                  </LinearGradient>
                  <View style={styles.mealInfo}>
                    <Text style={styles.mealName}>{meal.mealName}</Text>
                    <Text style={styles.mealType}>{MEAL_TYPE_LABELS[meal.mealType] || meal.mealType} · {meal.time}</Text>
                  </View>
                  <View style={styles.mealRight}>
                    <Text style={styles.mealCal}>{meal.calories} kcal</Text>
                    <TouchableOpacity onPress={() => handleDelete(meal.mealId)} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
                      <Ionicons name="trash-outline" size={16} color={COLORS.textTertiary} />
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })
          )}
        </View>
        <View style={{ height: 24 }} />
      </ScrollView>

      {/* Add Meal Modal */}
      <Modal visible={showAddModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setShowAddModal(false)} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
                <Ionicons name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
              <Text style={styles.modalTitle}>添加饮食记录</Text>
              <TouchableOpacity onPress={handleAddMeal} disabled={submitting}>
                <Text style={[styles.modalSave, submitting && { opacity: 0.5 }]}>保存</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.formCard}>
              <Text style={styles.formLabel}>餐食类型</Text>
              <View style={styles.chipRow}>
                {Object.entries(MEAL_TYPE_LABELS).map(([key, label]) => {
                  const colors = MEAL_COLORS[key] || ['#6B7280', '#9CA3AF'];
                  const isActive = mealType === key;
                  return (
                    <TouchableOpacity
                      key={key}
                      style={[styles.chip, isActive && styles.chipActive]}
                      onPress={() => setMealType(key)}
                    >
                      {isActive ? (
                        <LinearGradient
                          colors={colors}
                          style={styles.chipGradient}
                          start={{ x: 0, y: 0 }}
                          end={{ x: 1, y: 1 }}
                        >
                          <Ionicons name={MEAL_ICONS[key]} size={14} color={COLORS.white} />
                        </LinearGradient>
                      ) : (
                        <View style={styles.chipIconPlaceholder}>
                          <Ionicons name={MEAL_ICONS[key]} size={14} color={COLORS.textTertiary} />
                        </View>
                      )}
                      <Text style={[styles.chipText, isActive && styles.chipActiveText]}>{label}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              <Text style={styles.formLabel}>食物内容</Text>
              <View style={styles.inputWrap}>
                <Ionicons name="restaurant-outline" size={18} color={COLORS.textTertiary} />
                <TextInput style={styles.formInput} placeholder="输入食物内容..." value={mealName} onChangeText={setMealName} placeholderTextColor={COLORS.textTertiary} />
              </View>

              <Text style={styles.formLabel}>热量（kcal）</Text>
              <View style={styles.inputWrap}>
                <Ionicons name="flame-outline" size={18} color={COLORS.textTertiary} />
                <TextInput style={styles.formInput} placeholder="0" value={calories} onChangeText={setCalories} keyboardType="numeric" placeholderTextColor={COLORS.textTertiary} />
              </View>

              <Text style={styles.formLabel}>备注</Text>
              <TextInput style={[styles.formInputFull, { height: 80 }]} placeholder="添加备注..." value={note} onChangeText={setNote} multiline textAlignVertical="top" placeholderTextColor={COLORS.textTertiary} />
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 8,
  },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: COLORS.text },
  headerSub: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  card: {
    backgroundColor: COLORS.card,
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 16,
    padding: 20,
    ...SHADOWS.card,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  cardTitle: { fontSize: 18, fontWeight: '700', color: COLORS.text },
  addBtn: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  calRow: { flexDirection: 'row', alignItems: 'baseline', marginBottom: 12 },
  calValue: { fontSize: 32, fontWeight: 'bold', color: COLORS.text },
  calUnit: { fontSize: 14, color: COLORS.textSecondary, marginLeft: 4 },
  progressTrack: { height: 10, backgroundColor: COLORS.divider, borderRadius: 5, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 5 },
  progressLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 },
  progressText: { fontSize: 12, color: COLORS.textSecondary },
  divider: { height: 1, backgroundColor: COLORS.divider, marginVertical: 16 },
  nutritionTitle: { fontSize: 14, fontWeight: '600', color: COLORS.text, marginBottom: 12 },
  nutritionGrid: { gap: 12 },
  nutritionItem: { gap: 4 },
  nutritionHeader: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  nutritionDot: { width: 8, height: 8, borderRadius: 4 },
  nutritionLabel: { fontSize: 12, color: COLORS.textSecondary },
  nutritionValue: { fontSize: 14, fontWeight: '600', color: COLORS.text },
  nutritionGoal: { fontSize: 12, color: COLORS.textTertiary, fontWeight: '400' },
  miniTrack: { height: 4, backgroundColor: COLORS.divider, borderRadius: 2, overflow: 'hidden' },
  miniFill: { height: '100%', borderRadius: 2 },
  emptyState: { alignItems: 'center', paddingVertical: 32 },
  emptyTitle: { fontSize: 16, fontWeight: '600', color: COLORS.text, marginTop: 12 },
  emptySub: { fontSize: 13, color: COLORS.textSecondary, marginTop: 4 },
  mealItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  mealIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  mealInfo: { flex: 1 },
  mealName: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  mealType: { fontSize: 13, color: COLORS.textSecondary, marginTop: 2 },
  mealRight: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  mealCal: { fontSize: 14, fontWeight: '600', color: COLORS.text },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: COLORS.background,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: COLORS.white,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
  },
  modalTitle: { fontSize: 17, fontWeight: '700', color: COLORS.text },
  modalSave: { color: COLORS.primary, fontSize: 16, fontWeight: '600' },
  formCard: { padding: 20, gap: 14 },
  formLabel: { fontSize: 14, fontWeight: '600', color: COLORS.text, marginBottom: 2 },
  chipRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: COLORS.white,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    gap: 6,
  },
  chipActive: { borderColor: COLORS.primary, backgroundColor: COLORS.blueBg },
  chipGradient: {
    width: 22,
    height: 22,
    borderRadius: 6,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chipIconPlaceholder: {
    width: 22,
    height: 22,
    borderRadius: 6,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chipText: { fontSize: 14, color: COLORS.textSecondary },
  chipActiveText: { color: COLORS.primary, fontWeight: '600' },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 48,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    gap: 8,
    backgroundColor: COLORS.white,
  },
  formInput: {
    flex: 1,
    fontSize: 15,
    color: COLORS.text,
  },
  formInputFull: {
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: COLORS.text,
    backgroundColor: COLORS.white,
  },
});
