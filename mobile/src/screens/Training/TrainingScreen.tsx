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
import { trainingApi } from '../../services/training';
import { COLORS, TRAINING_TYPE_LABELS } from '../../constants';
import type { WeeklyStats, TrainingSchedule, TrainingPlan } from '../../types';

export default function TrainingScreen() {
  const [stats, setStats] = useState<WeeklyStats | null>(null);
  const [schedule, setSchedule] = useState<TrainingSchedule[]>([]);
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

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
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

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed': return COLORS.success;
      case 'in_progress': return COLORS.primary;
      default: return COLORS.primary;
    }
  };
  const statusLabel = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'in_progress': return '进行中';
      default: return '待完成';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.topBar}>
        <Text style={styles.topTitle}>训练计划</Text>
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

        {/* Today's Plan */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>今日训练计划</Text>
          </View>
          {schedule.filter(s => s.date === today).length === 0 ? (
            <Text style={styles.emptyText}>暂无训练计划</Text>
          ) : (
            schedule.filter(s => s.date === today).map((item, idx) => (
              <View key={item.planId || idx} style={styles.planItem}>
                <View style={styles.planInfo}>
                  <Text style={styles.planName}>{item.planName}</Text>
                  <Text style={styles.planDetail}>{item.duration}分钟 | {item.intensity}</Text>
                </View>
                <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
                  <View style={[styles.statusBadge, { backgroundColor: statusColor(item.status) + '18' }]}>
                    <Text style={[styles.statusText, { color: statusColor(item.status) }]}>
                      {statusLabel(item.status)}
                    </Text>
                  </View>
                  {item.status !== 'completed' && item.planId && (
                    <TouchableOpacity onPress={() => handleComplete(item.planId!)}>
                      <Text style={{ color: COLORS.primary, fontSize: 13 }}>完成</Text>
                    </TouchableOpacity>
                  )}
                  {item.planId && (
                    <TouchableOpacity onPress={() => handleDelete(item.planId!)}>
                      <Text style={{ color: COLORS.danger, fontSize: 13 }}>删除</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            ))
          )}
        </View>

        {/* Weekly Stats */}
        {stats && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>本周训练统计</Text>
            <View style={styles.statsRow}>
              <View style={[styles.statCard, { backgroundColor: '#FFF1F0' }]}>
                <Text style={[styles.statValue, { color: '#CF1322' }]}>{stats.weeklyCalories}</Text>
                <Text style={styles.statLabel}>消耗卡路里</Text>
              </View>
              <View style={[styles.statCard, { backgroundColor: '#E6F7FF' }]}>
                <Text style={[styles.statValue, { color: COLORS.primary }]}>{stats.weeklyHours}h</Text>
                <Text style={styles.statLabel}>训练时长</Text>
              </View>
              <View style={[styles.statCard, { backgroundColor: '#FFFBE6' }]}>
                <Text style={[styles.statValue, { color: '#D48806' }]}>{stats.completedCount}</Text>
                <Text style={styles.statLabel}>完成次数</Text>
              </View>
            </View>
          </View>
        )}
        <View style={{ height: 24 }} />
      </ScrollView>

      {/* Add Plan Modal */}
      <Modal visible={showAddModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setShowAddModal(false)}>
                <Text style={styles.modalClose}>✕</Text>
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
                    <Text style={[styles.chipText, planType === key && styles.chipActiveText]}>{label}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.formLabel}>训练名称</Text>
              <TextInput style={styles.formInput} placeholder="输入训练名称..." value={planName} onChangeText={setPlanName} />

              <Text style={styles.formLabel}>训练时长（分钟）</Text>
              <TextInput style={styles.formInput} placeholder="30" value={duration} onChangeText={setDuration} keyboardType="numeric" />

              <Text style={styles.formLabel}>备注</Text>
              <TextInput style={[styles.formInput, { height: 80 }]} placeholder="添加训练备注..." value={note} onChangeText={setNote} multiline textAlignVertical="top" />
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
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  cardTitle: { fontSize: 16, fontWeight: '600', color: COLORS.text },
  emptyText: { color: COLORS.textSecondary, textAlign: 'center', paddingVertical: 16 },
  planItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  planInfo: { flex: 1 },
  planName: { fontSize: 15, fontWeight: '500', color: COLORS.text },
  planDetail: { fontSize: 13, color: COLORS.textSecondary, marginTop: 2 },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  statusText: { fontSize: 12, fontWeight: '500' },
  statsRow: { flexDirection: 'row', gap: 8, marginTop: 12 },
  statCard: { flex: 1, borderRadius: 10, padding: 12, alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: 'bold' },
  statLabel: { fontSize: 12, color: COLORS.textSecondary, marginTop: 4 },
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
  chipRow: { flexDirection: 'row', gap: 8 },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chipActive: { backgroundColor: COLORS.primary + '18', borderColor: COLORS.primary },
  chipText: { fontSize: 14, color: COLORS.textSecondary },
  chipActiveText: { color: COLORS.primary, fontWeight: '500' },
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
