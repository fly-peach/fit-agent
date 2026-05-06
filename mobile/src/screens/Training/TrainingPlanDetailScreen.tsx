import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { COLORS, SHADOWS } from '../../constants';
import { trainingApi } from '../../services/training';
import type { PlanDetail } from '../../types';

export default function TrainingPlanDetailScreen({ route, navigation }: any) {
  const insets = useSafeAreaInsets();
  const { planId } = route.params;
  const [detail, setDetail] = useState<PlanDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const loadDetail = useCallback(async () => {
    setLoading(true);
    try {
      const data = await trainingApi.getPlanDetail(planId);
      setDetail(data);
    } catch (e: any) {
      Alert.alert('错误', e.message || '获取详情失败');
    } finally {
      setLoading(false);
    }
  }, [planId]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  const updateExercise = async (exerciseId: number, field: 'sets' | 'reps', value: string) => {
    try {
      await trainingApi.updatePlanExercise(exerciseId, { [field]: parseInt(value, 10) || 0 });
      loadDetail();
    } catch (e: any) {
      Alert.alert('错误', e.message || '更新失败');
    }
  };

  const deleteExercise = async (exerciseId: number) => {
    try {
      await trainingApi.deletePlanExercise(exerciseId);
      loadDetail();
    } catch (e: any) {
      Alert.alert('错误', e.message || '删除失败');
    }
  };

  const completePlan = async () => {
    try {
      await trainingApi.completePlan(planId, { actualDuration: detail?.estimatedDuration || 30 });
      Alert.alert('成功', '计划已完成');
      loadDetail();
    } catch (e: any) {
      Alert.alert('错误', e.message || '完成失败');
    }
  };

  const renewPlan = async () => {
    try {
      await trainingApi.renewPlan(planId);
      Alert.alert('成功', '续期成功');
    } catch (e: any) {
      Alert.alert('错误', e.message || '续期失败');
    }
  };

  const deletePlan = async () => {
    try {
      await trainingApi.deletePlan(planId);
      Alert.alert('成功', '删除成功');
      navigation.goBack();
    } catch (e: any) {
      Alert.alert('错误', e.message || '删除失败');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingTop: insets.top + 8, paddingBottom: 24 }}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="chevron-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>计划详情</Text>
        <View style={{ width: 24 }} />
      </View>

      <View style={styles.card}>
        <Text style={styles.title}>{loading ? '加载中...' : detail?.planName || '训练计划'}</Text>
        <Text style={styles.meta}>类型：{detail?.planType || '-'}</Text>
        <Text style={styles.meta}>状态：{detail?.status || '-'}</Text>
        <Text style={styles.meta}>计划日期：{detail?.scheduledDate || '-'}</Text>
        <Text style={styles.meta}>备注：{detail?.note || '无'}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>动作项</Text>
        {detail?.exercises?.length ? detail.exercises.map(item => (
          <View key={item.id} style={styles.exerciseCard}>
            <View style={styles.exerciseHeader}>
              <View style={{ flex: 1 }}>
                <Text style={styles.exerciseTitle}>{item.customName || item.nameCn || `动作 #${item.exerciseId}`}</Text>
                <Text style={styles.exerciseMeta}>{item.targetMuscle || '自定义动作'} · {item.difficulty || '未分级'}</Text>
              </View>
              <TouchableOpacity onPress={() => deleteExercise(item.id)}>
                <Ionicons name="trash-outline" size={18} color={COLORS.danger} />
              </TouchableOpacity>
            </View>
            <View style={styles.inlineInputs}>
              <View style={styles.inlineField}>
                <Text style={styles.inlineLabel}>组数</Text>
                <TextInput
                  defaultValue={String(item.sets)}
                  style={styles.input}
                  keyboardType="numeric"
                  onEndEditing={e => updateExercise(item.id, 'sets', e.nativeEvent.text)}
                />
              </View>
              <View style={styles.inlineField}>
                <Text style={styles.inlineLabel}>次数</Text>
                <TextInput
                  defaultValue={String(item.reps)}
                  style={styles.input}
                  keyboardType="numeric"
                  onEndEditing={e => updateExercise(item.id, 'reps', e.nativeEvent.text)}
                />
              </View>
            </View>
          </View>
        )) : (
          <Text style={styles.emptyText}>暂无动作项</Text>
        )}
      </View>

      <View style={styles.actionRow}>
        <TouchableOpacity style={[styles.actionBtn, { backgroundColor: COLORS.primary }]} onPress={completePlan}>
          <Text style={styles.actionBtnText}>标记完成</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionBtn, { backgroundColor: COLORS.warning }]} onPress={renewPlan}>
          <Text style={styles.actionBtnText}>循环续期</Text>
        </TouchableOpacity>
      </View>
      <TouchableOpacity style={[styles.actionBtn, styles.deleteBtn]} onPress={deletePlan}>
        <Text style={styles.actionBtnText}>删除计划</Text>
      </TouchableOpacity>
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
  title: { fontSize: 20, fontWeight: '700', color: COLORS.text, marginBottom: 8 },
  meta: { fontSize: 14, color: COLORS.textSecondary, marginTop: 4 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: COLORS.text, marginBottom: 10 },
  exerciseCard: {
    paddingVertical: 12,
    borderBottomColor: COLORS.divider,
    borderBottomWidth: 1,
  },
  exerciseHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  exerciseTitle: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  exerciseMeta: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  inlineInputs: { flexDirection: 'row', gap: 12, marginTop: 10 },
  inlineField: { flex: 1 },
  inlineLabel: { fontSize: 12, color: COLORS.textSecondary, marginBottom: 6 },
  input: {
    backgroundColor: COLORS.background,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  emptyText: { color: COLORS.textSecondary },
  actionRow: { flexDirection: 'row', gap: 12, marginHorizontal: 16, marginTop: 16 },
  actionBtn: {
    flex: 1,
    borderRadius: 14,
    paddingVertical: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionBtnText: { color: COLORS.white, fontWeight: '700' },
  deleteBtn: { marginHorizontal: 16, marginTop: 12, backgroundColor: COLORS.danger },
});

