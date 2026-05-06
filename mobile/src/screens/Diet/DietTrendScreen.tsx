import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { COLORS, SHADOWS } from '../../constants';
import { dietApi } from '../../services/diet';
import type { DietMeal } from '../../types';

const DAY_OPTIONS = [7, 14, 30];

export default function DietTrendScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [days, setDays] = useState(7);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [goals, setGoals] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [meals, setMeals] = useState<DietMeal[]>([]);
  const [mealsLoading, setMealsLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - (days - 1));
      const format = (date: Date) => date.toISOString().slice(0, 10);
      const result = await dietApi.getDateRangeTrend(format(start), format(end));
      setTrendData(result.dailyStats);
      setGoals(result.goals);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = async () => {
    await loadData();
  };

  const fetchMeals = async (dateStr: string) => {
    setMealsLoading(true);
    try {
      const result = await dietApi.getTodayMeals(dateStr);
      setMeals(result);
      setSelectedDate(dateStr);
    } finally {
      setMealsLoading(false);
    }
  };

  const maxCalories = useMemo(() => Math.max(...trendData.map(d => d.calories || 0), goals?.caloriesGoal || 1), [trendData, goals]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingTop: insets.top + 8, paddingBottom: 24 }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="chevron-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>饮食趋势</Text>
        <View style={{ width: 24 }} />
      </View>

      <View style={styles.card}>
        <View style={styles.optionRow}>
          {DAY_OPTIONS.map(option => (
            <TouchableOpacity
              key={option}
              style={[styles.optionChip, days === option && styles.optionChipActive]}
              onPress={() => setDays(option)}
            >
              <Text style={[styles.optionText, days === option && styles.optionTextActive]}>近{option}天</Text>
            </TouchableOpacity>
          ))}
        </View>

        {loading ? (
          <ActivityIndicator color={COLORS.primary} />
        ) : (
          trendData.map(item => {
            const percent = Math.min(((item.calories || 0) / (maxCalories || 1)) * 100, 100);
            return (
              <TouchableOpacity key={item.date} style={styles.trendRow} onPress={() => fetchMeals(item.date)}>
                <View style={{ width: 72 }}>
                  <Text style={styles.dateText}>{item.date.slice(5)}</Text>
                </View>
                <View style={styles.barTrack}>
                  <View style={[styles.barFill, { width: `${percent}%` }]} />
                </View>
                <Text style={styles.valueText}>{item.calories} kcal</Text>
              </TouchableOpacity>
            );
          })
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>目标参考</Text>
        <Text style={styles.goalText}>热量 {goals?.caloriesGoal || '-'} kcal</Text>
        <Text style={styles.goalText}>蛋白 {goals?.proteinGoal || '-'} g</Text>
        <Text style={styles.goalText}>碳水 {goals?.carbsGoal || '-'} g</Text>
        <Text style={styles.goalText}>脂肪 {goals?.fatGoal || '-'} g</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>按天明细 {selectedDate ? `· ${selectedDate}` : ''}</Text>
        {mealsLoading ? (
          <ActivityIndicator color={COLORS.primary} />
        ) : meals.length ? (
          meals.map(meal => (
            <View key={meal.mealId} style={styles.mealRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.mealName}>{meal.mealName}</Text>
                <Text style={styles.mealMeta}>{meal.mealType} · {meal.time}</Text>
              </View>
              <Text style={styles.valueText}>{meal.calories} kcal</Text>
            </View>
          ))
        ) : (
          <Text style={styles.emptyText}>点击上方某一天查看餐食明细</Text>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  headerTitle: { fontSize: 20, fontWeight: '700', color: COLORS.text },
  card: {
    marginHorizontal: 16,
    marginTop: 12,
    padding: 16,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    ...SHADOWS.card,
  },
  optionRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  optionChip: { backgroundColor: COLORS.background, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 8 },
  optionChipActive: { backgroundColor: COLORS.blueBg },
  optionText: { color: COLORS.textSecondary },
  optionTextActive: { color: COLORS.primary, fontWeight: '700' },
  trendRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 10 },
  dateText: { color: COLORS.textSecondary, fontSize: 12 },
  barTrack: { flex: 1, height: 10, backgroundColor: COLORS.divider, borderRadius: 999, overflow: 'hidden' },
  barFill: { height: '100%', backgroundColor: COLORS.primary, borderRadius: 999 },
  valueText: { fontSize: 12, color: COLORS.text, fontWeight: '600' },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: COLORS.text, marginBottom: 8 },
  goalText: { fontSize: 14, color: COLORS.textSecondary, marginTop: 4 },
  mealRow: { flexDirection: 'row', alignItems: 'center', marginTop: 10, paddingBottom: 10, borderBottomWidth: 1, borderBottomColor: COLORS.divider },
  mealName: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  mealMeta: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  emptyText: { color: COLORS.textSecondary },
});

