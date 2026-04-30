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
import { dietApi } from '../../services/diet';
import { COLORS, MEAL_TYPE_LABELS } from '../../constants';
import type { DietStats, DietMeal } from '../../types';

const MEAL_ICONS: Record<string, string> = {
  breakfast: '🌅',
  lunch: '☀️',
  dinner: '🌙',
  snack: '🍪',
};

export default function DietScreen() {
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

  return (
    <View style={styles.container}>
      <View style={styles.topBar}>
        <Text style={styles.topTitle}>饮食管理</Text>
        <TouchableOpacity style={styles.addBtn} onPress={() => setShowAddModal(true)}>
          <Text style={styles.addBtnText}>+</Text>
        </TouchableOpacity>
      </View>

      <ScrollView refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
        {/* Date */}
        <View style={styles.card}>
          <Text style={styles.dateText}>
            {new Date().getFullYear()}年{new Date().getMonth() + 1}月{new Date().getDate()}日
            {['日', '一', '二', '三', '四', '五', '六'][new Date().getDay()]}
          </Text>
        </View>

        {/* Calorie Card */}
        {stats && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>今日热量摄入</Text>
            <View style={styles.calRow}>
              <Text style={styles.calValue}>{stats.calories} kcal</Text>
              <Text style={styles.calGoal}>目标 {stats.caloriesGoal} kcal</Text>
            </View>
            <View style={styles.progressBg}>
              <View style={[styles.progressFill, { width: `${calPercent}%` }]} />
            </View>
            <View style={styles.progressLabels}>
              <Text style={styles.progressText}>已摄入 {calPercent.toFixed(0)}%</Text>
              <Text style={styles.progressText}>剩余 {stats.remainingCalories} kcal</Text>
            </View>
          </View>
        )}

        {/* Meals Card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>今日餐食记录</Text>
          {meals.length === 0 ? (
            <Text style={styles.emptyText}>暂无饮食记录</Text>
          ) : (
            meals.map((meal, idx) => (
              <View key={meal.mealId || idx} style={styles.mealItem}>
                <View style={styles.mealLeft}>
                  <Text style={styles.mealIcon}>{MEAL_ICONS[meal.mealType] || '🍽️'}</Text>
                  <View style={styles.mealInfo}>
                    <Text style={styles.mealName}>{meal.mealName}</Text>
                    <Text style={styles.mealType}>{MEAL_TYPE_LABELS[meal.mealType] || meal.mealType} · {meal.time}</Text>
                  </View>
                </View>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <Text style={styles.mealCal}>{meal.calories} kcal</Text>
                  <TouchableOpacity onPress={() => handleDelete(meal.mealId)}>
                    <Text style={{ color: COLORS.danger, fontSize: 13 }}>删除</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))
          )}
        </View>
        <View style={{ height: 24 }} />
      </ScrollView>

      {/* Add Meal Modal */}
      <Modal visible={showAddModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setShowAddModal(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>添加饮食记录</Text>
              <TouchableOpacity onPress={handleAddMeal} disabled={submitting}>
                <Text style={[styles.modalSave, submitting && { opacity: 0.5 }]}>保存</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.formCard}>
              <Text style={styles.formLabel}>餐食类型</Text>
              <View style={styles.chipRow}>
                {Object.entries(MEAL_TYPE_LABELS).map(([key, label]) => (
                  <TouchableOpacity
                    key={key}
                    style={[styles.chip, mealType === key && styles.chipActive]}
                    onPress={() => setMealType(key)}
                  >
                    <Text style={styles.chipIcon}>{MEAL_ICONS[key]}</Text>
                    <Text style={[styles.chipText, mealType === key && styles.chipActiveText]}>{label}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.formLabel}>食物内容</Text>
              <TextInput style={styles.formInput} placeholder="输入食物内容..." value={mealName} onChangeText={setMealName} />

              <Text style={styles.formLabel}>热量（kcal）</Text>
              <TextInput style={styles.formInput} placeholder="0" value={calories} onChangeText={setCalories} keyboardType="numeric" />

              <Text style={styles.formLabel}>备注</Text>
              <TextInput style={[styles.formInput, { height: 80 }]} placeholder="添加备注..." value={note} onChangeText={setNote} multiline textAlignVertical="top" />
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 56,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    paddingHorizontal: 16,
  },
  topTitle: { fontSize: 18, fontWeight: '600', color: COLORS.text, flex: 1, textAlign: 'center' },
  addBtn: {
    position: 'absolute',
    right: 16,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addBtnText: { color: COLORS.white, fontSize: 20, fontWeight: 'bold' },
  card: {
    backgroundColor: COLORS.white,
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 16,
  },
  dateText: { fontSize: 15, color: COLORS.text, textAlign: 'center' },
  cardTitle: { fontSize: 16, fontWeight: '600', color: COLORS.text, marginBottom: 12 },
  emptyText: { color: COLORS.textSecondary, textAlign: 'center', paddingVertical: 16 },
  calRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 },
  calValue: { fontSize: 24, fontWeight: 'bold', color: COLORS.text },
  calGoal: { fontSize: 14, color: COLORS.textSecondary },
  progressBg: { height: 8, backgroundColor: COLORS.border, borderRadius: 4, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: COLORS.success, borderRadius: 4 },
  progressLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 },
  progressText: { fontSize: 12, color: COLORS.textSecondary },
  mealItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  mealLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  mealIcon: { fontSize: 22, marginRight: 10 },
  mealInfo: { flex: 1 },
  mealName: { fontSize: 15, fontWeight: '500', color: COLORS.text },
  mealType: { fontSize: 13, color: COLORS.textSecondary, marginTop: 2 },
  mealCal: { fontSize: 15, fontWeight: '500', color: COLORS.text },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: COLORS.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: COLORS.white,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  modalClose: { fontSize: 20, color: COLORS.textSecondary, width: 32 },
  modalTitle: { fontSize: 17, fontWeight: '600', color: COLORS.text },
  modalSave: { color: COLORS.primary, fontSize: 16, fontWeight: '600', width: 48, textAlign: 'right' },
  formCard: { padding: 16, gap: 12 },
  formLabel: { fontSize: 14, fontWeight: '500', color: COLORS.text, marginTop: 4 },
  chipRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: 4,
  },
  chipActive: { backgroundColor: '#FFF7E6', borderColor: '#FAAD14' },
  chipIcon: { fontSize: 14 },
  chipText: { fontSize: 14, color: COLORS.textSecondary },
  chipActiveText: { color: '#D48806', fontWeight: '500' },
  formInput: {
    height: 44,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 15,
    color: COLORS.text,
    backgroundColor: COLORS.white,
  },
});
