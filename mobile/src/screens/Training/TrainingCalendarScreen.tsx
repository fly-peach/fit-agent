import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
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
import { trainingApi } from '../../services/training';
import type { TrainingSchedule } from '../../types';

const weekdayNames = ['日', '一', '二', '三', '四', '五', '六'];

export default function TrainingCalendarScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [current, setCurrent] = useState(new Date());
  const [schedule, setSchedule] = useState<TrainingSchedule[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const year = current.getFullYear();
  const month = current.getMonth() + 1;

  const loadData = useCallback(async () => {
    const data = await trainingApi.getMonthlySchedule(year, month);
    setSchedule(data);
  }, [year, month]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const itemsByDate = useMemo(() => {
    const map = new Map<string, TrainingSchedule[]>();
    schedule.forEach(item => {
      const arr = map.get(item.date) || [];
      arr.push(item);
      map.set(item.date, arr);
    });
    return map;
  }, [schedule]);

  const dayCells = useMemo(() => {
    const start = new Date(year, month - 1, 1);
    const end = new Date(year, month, 0);
    const firstDay = start.getDay();
    const totalDays = end.getDate();
    const cells: Array<number | null> = [];
    for (let i = 0; i < firstDay; i += 1) cells.push(null);
    for (let day = 1; day <= totalDays; day += 1) cells.push(day);
    while (cells.length % 7 !== 0) cells.push(null);
    return cells;
  }, [year, month]);

  const changeMonth = (delta: number) => {
    setCurrent(prev => new Date(prev.getFullYear(), prev.getMonth() + delta, 1));
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      contentContainerStyle={{ paddingTop: insets.top + 8, paddingBottom: 24 }}
    >
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="chevron-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>训练月历</Text>
        <View style={{ width: 24 }} />
      </View>

      <View style={styles.card}>
        <View style={styles.monthRow}>
          <TouchableOpacity onPress={() => changeMonth(-1)}>
            <Ionicons name="chevron-back-circle-outline" size={24} color={COLORS.primary} />
          </TouchableOpacity>
          <Text style={styles.monthText}>{year} 年 {month} 月</Text>
          <TouchableOpacity onPress={() => changeMonth(1)}>
            <Ionicons name="chevron-forward-circle-outline" size={24} color={COLORS.primary} />
          </TouchableOpacity>
        </View>

        <View style={styles.grid}>
          {weekdayNames.map(name => (
            <Text key={name} style={styles.weekday}>{name}</Text>
          ))}
          {dayCells.map((day, index) => {
            if (!day) {
              return <View key={`blank-${index}`} style={styles.dayCell} />;
            }
            const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const items = itemsByDate.get(dateStr) || [];
            return (
              <TouchableOpacity key={dateStr} style={styles.dayCell}>
                <Text style={styles.dayNumber}>{day}</Text>
                {items.slice(0, 2).map(item => (
                  <TouchableOpacity
                    key={`${item.planId}-${item.planName}`}
                    style={[styles.dayTag, item.status === 'completed' && styles.dayTagDone]}
                    onPress={() => item.planId && navigation.navigate('TrainingPlanDetail', { planId: item.planId })}
                  >
                    <Text numberOfLines={1} style={styles.dayTagText}>{item.planName}</Text>
                  </TouchableOpacity>
                ))}
              </TouchableOpacity>
            );
          })}
        </View>
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
  monthRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  monthText: { fontSize: 18, fontWeight: '700', color: COLORS.text },
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  weekday: {
    width: '14.2857%',
    textAlign: 'center',
    color: COLORS.textSecondary,
    marginBottom: 8,
    fontWeight: '600',
  },
  dayCell: {
    width: '14.2857%',
    minHeight: 84,
    padding: 4,
    borderWidth: 1,
    borderColor: COLORS.divider,
  },
  dayNumber: { fontSize: 12, color: COLORS.text, marginBottom: 4 },
  dayTag: {
    backgroundColor: COLORS.blueBg,
    borderRadius: 8,
    paddingHorizontal: 4,
    paddingVertical: 2,
    marginTop: 2,
  },
  dayTagDone: { backgroundColor: COLORS.successLight },
  dayTagText: { fontSize: 10, color: COLORS.primary },
});

