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
import { trainingApi } from '../../services/training';
import { COLORS, SHADOWS, TRAINING_TYPE_LABELS } from '../../constants';
import type { WeeklyStats, TrainingSchedule, TrainingPlan } from '../../types';

const TYPE_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  strength: 'barbell',
  cardio: 'heart',
  stretch: 'leaf',
};

export default function TrainingScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [stats, setStats] = useState<WeeklyStats | null>(null);
  const [schedule, setSchedule] = useState<TrainingSchedule[]>([]);
  const [trendDays, setTrendDays] = useState(7);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [planName, setPlanName] = useState('');
  const [planType, setPlanType] = useState('strength');
  const [duration, setDuration] = useState('30');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const today = new Date().toISOString().slice(0, 10);

  const loadData = useCallback(async () => {
    try {
      const [s, sc] = await Promise.all([
        trainingApi.getWeeklyStats().catch(() => null),
        trainingApi.getWeeklySchedule().catch(() => []),
      ]);
      if (s) setStats(s);
      if (sc) setSchedule(sc);
    } catch {}
  }, []);

  const loadTrend = useCallback(async () => {
    try {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - (trendDays - 1));
      const format = (date: Date) => date.toISOString().slice(0, 10);
      const result = await trainingApi.getDateRangeTrend(format(start), format(end)).catch(() => ({ dailyStats: [] }));
      setTrendData(result.dailyStats || []);
    } catch {}
  }, [trendDays]);

  useEffect(() => { loadData(); }, [loadData]);
  useEffect(() => { loadTrend(); }, [loadTrend]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    await loadTrend();
    setRefreshing(false);
  };

  const handleAddPlan = async () => {
    if (!planName.trim()) {
      Alert.alert('提示', '请输入训练名称');
      return;
    }
    setSubmitting(true);
    try {
      const data: TrainingPlan = {
        planName: planName.trim(),
        planType,
        scheduledDate: today,
        estimatedDuration: parseInt(duration) || 30,
        note: note.trim() || undefined,
      };
      await trainingApi.createPlan(data);
      setShowAddModal(false);
      setPlanName('');
      setDuration('30');
      setNote('');
      Alert.alert('成功', '训练计划已添加');
      loadData();
    } catch (err: any) {
      Alert.alert('错误', err.message || '添加失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleComplete = async (planId: number) => {
    try {
      await trainingApi.completePlan(planId, { actualDuration: 30 });
      Alert.alert('完成', '训练已标记完成');
      loadData();
    } catch (err: any) {
      Alert.alert('错误', err.message || '操作失败');
    }
  };

  const handleDelete = async (planId: number) => {
    Alert.alert('确认', '确定删除该训练计划？', [
      { text: '取消', style: 'cancel' },
      {
        text: '删除',
        style: 'destructive',
        onPress: async () => {
          try {
            await trainingApi.deletePlan(planId);
            loadData();
          } catch (err: any) {
            Alert.alert('错误', err.message || '删除失败');
          }
        },
      },
    ]);
  };

  const statusConfig = (status: string) => {
    switch (status) {
      case 'completed': return { color: COLORS.success, bg: COLORS.successLight, label: '已完成', icon: 'checkmark-circle' as keyof typeof Ionicons.glyphMap };
      case 'in_progress': return { color: COLORS.primary, bg: COLORS.blueBg, label: '进行中', icon: 'time-outline' as keyof typeof Ionicons.glyphMap };
      default: return { color: COLORS.warning, bg: COLORS.warningLight, label: '待完成', icon: 'ellipse-outline' as keyof typeof Ionicons.glyphMap };
    }
  };

  const todayPlans = schedule.filter(s => s.date === today);
  const recentPlans = schedule.slice(0, 6);
  const maxTrend = Math.max(...trendData.map(item => item.duration || 0), 1);

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Compact Header */}
        <View style={[styles.header, { paddingTop: insets.top + 6 }]}>
          <Text style={styles.headerTitle}>训练计划</Text>
          <Text style={styles.headerSub}>
            {new Date().getMonth() + 1}月{new Date().getDate()}日 周{['日', '一', '二', '三', '四', '五', '六'][new Date().getDay()]}
          </Text>
        </View>

        {/* Today's Plan */}
        <View style={[styles.card, { marginTop: 12 }]}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>今日训练</Text>
            <View style={styles.headerActions}>
              <TouchableOpacity style={styles.smallAction} onPress={() => navigation.navigate('TrainingCalendar')}>
                <Ionicons name="calendar-outline" size={18} color={COLORS.primary} />
              </TouchableOpacity>
              <TouchableOpacity style={styles.addBtn} onPress={() => navigation.navigate('TrainingCreate')}>
                <Ionicons name="add" size={22} color={COLORS.white} />
              </TouchableOpacity>
            </View>
          </View>
          {todayPlans.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="barbell-outline" size={48} color={COLORS.textTertiary} />
              <Text style={styles.emptyTitle}>暂无训练计划</Text>
              <Text style={styles.emptySub}>点击右上角添加今日训练</Text>
            </View>
          ) : (
            todayPlans.map((item, idx) => {
              const sc = statusConfig(item.status);
              return (
                <View key={item.planId || idx} style={styles.planItem}>
                  <View style={[styles.planTypeIcon, { backgroundColor: sc.bg }]}>
                    <Ionicons name={TYPE_ICONS[item.planType] || 'fitness'} size={20} color={sc.color} />
                  </View>
                  <View style={styles.planInfo}>
                    <Text style={styles.planName}>{item.planName}</Text>
                    <Text style={styles.planDetail}>{item.duration}分钟 · {item.intensity}</Text>
                  </View>
                  <View style={styles.planActions}>
                    <View style={[styles.statusBadge, { backgroundColor: sc.bg }]}>
                      <Ionicons name={sc.icon} size={12} color={sc.color} />
                      <Text style={[styles.statusText, { color: sc.color }]}>{sc.label}</Text>
                    </View>
                    {item.status !== 'completed' && item.planId && (
                      <TouchableOpacity style={styles.completeBtn} onPress={() => handleComplete(item.planId!)}>
                        <Ionicons name="checkmark" size={16} color={COLORS.primary} />
                      </TouchableOpacity>
                    )}
                    {item.planId && (
                      <TouchableOpacity onPress={() => navigation.navigate('TrainingPlanDetail', { planId: item.planId })} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
                        <Ionicons name="eye-outline" size={16} color={COLORS.primary} />
                      </TouchableOpacity>
                    )}
                    {item.planId && (
                      <TouchableOpacity onPress={() => handleDelete(item.planId!)} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
                        <Ionicons name="trash-outline" size={16} color={COLORS.textTertiary} />
                      </TouchableOpacity>
                    )}
                  </View>
                </View>
              );
            })
          )}
        </View>

        {/* Weekly Stats */}
        {stats && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>本周统计</Text>
            <View style={styles.statsRow}>
              <LinearGradient
                colors={['#FF6B6B', '#FF8E8E']}
                style={styles.statCard}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name="flame" size={20} color={COLORS.white} />
                <Text style={styles.statValueWhite}>{stats.weeklyCalories}</Text>
                <Text style={styles.statLabelWhite}>消耗卡路里</Text>
              </LinearGradient>
              <LinearGradient
                colors={[COLORS.gradientStart, COLORS.gradientEnd]}
                style={styles.statCard}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name="time" size={20} color={COLORS.white} />
                <Text style={styles.statValueWhite}>{stats.weeklyHours}h</Text>
                <Text style={styles.statLabelWhite}>训练时长</Text>
              </LinearGradient>
              <LinearGradient
                colors={['#F59E0B', '#FBBF24']}
                style={styles.statCard}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name="trophy" size={20} color={COLORS.white} />
                <Text style={styles.statValueWhite}>{stats.completedCount}</Text>
                <Text style={styles.statLabelWhite}>完成次数</Text>
              </LinearGradient>
            </View>
          </View>
        )}

        <View style={styles.card}>
          <View style={styles.trendHeader}>
            <Text style={styles.cardTitle}>训练趋势</Text>
            <View style={styles.daySwitch}>
              {[7, 14, 30].map(day => (
                <TouchableOpacity key={day} style={[styles.dayChip, trendDays === day && styles.dayChipActive]} onPress={() => setTrendDays(day)}>
                  <Text style={[styles.dayChipText, trendDays === day && styles.dayChipTextActive]}>近{day}天</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
          {trendData.length ? trendData.map(item => {
            const percent = Math.min(((item.duration || 0) / maxTrend) * 100, 100);
            return (
              <View key={item.date} style={styles.trendRow}>
                <Text style={styles.trendDate}>{item.date.slice(5)}</Text>
                <View style={styles.trendTrack}>
                  <View style={[styles.trendFill, { width: `${percent}%` }]} />
                </View>
                <Text style={styles.trendValue}>{item.duration} 分钟</Text>
              </View>
            );
          }) : (
            <Text style={styles.emptySub}>暂无趋势数据</Text>
          )}
        </View>

        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>最近计划</Text>
            <TouchableOpacity onPress={() => navigation.navigate('TrainingCalendar')}>
              <Text style={styles.linkText}>查看月历</Text>
            </TouchableOpacity>
          </View>
          {recentPlans.length ? recentPlans.map(item => (
            <TouchableOpacity
              key={`${item.planId || item.planName}-${item.date}`}
              style={styles.recentRow}
              onPress={() => item.planId && navigation.navigate('TrainingPlanDetail', { planId: item.planId })}
            >
              <View style={{ flex: 1 }}>
                <Text style={styles.planName}>{item.planName}</Text>
                <Text style={styles.planDetail}>{item.date} · {item.duration}分钟 · {item.intensity}</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={COLORS.textTertiary} />
            </TouchableOpacity>
          )) : (
            <Text style={styles.emptySub}>暂无计划</Text>
          )}
        </View>
        <View style={{ height: 24 }} />
      </ScrollView>

      {/* Add Plan Modal */}
      <Modal visible={showAddModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setShowAddModal(false)} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
                <Ionicons name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
              <Text style={styles.modalTitle}>添加训练计划</Text>
              <TouchableOpacity onPress={handleAddPlan} disabled={submitting}>
                <Text style={[styles.modalSave, submitting && { opacity: 0.5 }]}>保存</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.formCard}>
              <Text style={styles.formLabel}>训练类型</Text>
              <View style={styles.chipRow}>
                {Object.entries(TRAINING_TYPE_LABELS).map(([key, label]) => (
                  <TouchableOpacity
                    key={key}
                    style={[styles.chip, planType === key && styles.chipActive]}
                    onPress={() => setPlanType(key)}
                  >
                    <Ionicons name={TYPE_ICONS[key]} size={16} color={planType === key ? COLORS.primary : COLORS.textTertiary} />
                    <Text style={[styles.chipText, planType === key && styles.chipActiveText]}>{label}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.formLabel}>训练名称</Text>
              <View style={styles.inputWrap}>
                <Ionicons name="fitness-outline" size={18} color={COLORS.textTertiary} />
                <TextInput style={styles.formInput} placeholder="输入训练名称..." value={planName} onChangeText={setPlanName} placeholderTextColor={COLORS.textTertiary} />
              </View>

              <Text style={styles.formLabel}>训练时长（分钟）</Text>
              <View style={styles.inputWrap}>
                <Ionicons name="time-outline" size={18} color={COLORS.textTertiary} />
                <TextInput style={styles.formInput} placeholder="30" value={duration} onChangeText={setDuration} keyboardType="numeric" placeholderTextColor={COLORS.textTertiary} />
              </View>

              <Text style={styles.formLabel}>备注</Text>
              <TextInput style={[styles.formInputFull, { height: 80 }]} placeholder="添加训练备注..." value={note} onChangeText={setNote} multiline textAlignVertical="top" placeholderTextColor={COLORS.textTertiary} />
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
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  smallAction: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: COLORS.blueBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addBtn: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  emptyTitle: { fontSize: 16, fontWeight: '600', color: COLORS.text, marginTop: 12 },
  emptySub: { fontSize: 13, color: COLORS.textSecondary, marginTop: 4 },
  planItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  planTypeIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  planInfo: { flex: 1 },
  planName: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  planDetail: { fontSize: 13, color: COLORS.textSecondary, marginTop: 2 },
  planActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    gap: 3,
  },
  statusText: { fontSize: 11, fontWeight: '600' },
  completeBtn: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: COLORS.blueBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statsRow: { flexDirection: 'row', gap: 10, marginTop: 16 },
  statCard: {
    flex: 1,
    borderRadius: 14,
    padding: 14,
    alignItems: 'center',
    gap: 4,
  },
  statValueWhite: { fontSize: 20, fontWeight: 'bold', color: COLORS.white },
  statLabelWhite: { fontSize: 11, color: 'rgba(255,255,255,0.85)' },
  trendHeader: { gap: 12 },
  daySwitch: { flexDirection: 'row', gap: 8, marginTop: 10, flexWrap: 'wrap' },
  dayChip: { backgroundColor: COLORS.background, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6 },
  dayChipActive: { backgroundColor: COLORS.blueBg },
  dayChipText: { color: COLORS.textSecondary, fontSize: 12 },
  dayChipTextActive: { color: COLORS.primary, fontWeight: '700' },
  trendRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 10 },
  trendDate: { width: 54, fontSize: 12, color: COLORS.textSecondary },
  trendTrack: { flex: 1, height: 10, backgroundColor: COLORS.divider, borderRadius: 999, overflow: 'hidden' },
  trendFill: { height: '100%', backgroundColor: COLORS.primary, borderRadius: 999 },
  trendValue: { width: 72, fontSize: 12, color: COLORS.text, textAlign: 'right' },
  linkText: { color: COLORS.primary, fontWeight: '600' },
  recentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
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
  chipRow: { flexDirection: 'row', gap: 8 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: COLORS.white,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    gap: 6,
  },
  chipActive: { backgroundColor: COLORS.blueBg, borderColor: COLORS.primary },
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
