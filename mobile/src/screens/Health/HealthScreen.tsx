import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Alert,
  Dimensions,
  Modal,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { healthApi } from '../../services/health';
import { trainingApi } from '../../services/training';
import { dietApi } from '../../services/diet';
import { userApi } from '../../services/user';
import { COLORS, SHADOWS, BMI_STATUS_MAP } from '../../constants';
import type {
  DietStats,
  HealthMeasurement,
  HealthMetrics,
  HealthReport,
  UserProfile,
  WeeklyStats,
} from '../../types';

const { width } = Dimensions.get('window');

function StatusBadge({ status, value }: { status: string; value: string }) {
  const info = BMI_STATUS_MAP[status] || { label: value, color: COLORS.textSecondary, bg: '#F5F5F5' };
  return (
    <View style={[styles.badge, { backgroundColor: info.bg }]}>
      <Text style={[styles.badgeText, { color: info.color }]}>{info.label || value}</Text>
    </View>
  );
}

function MetricCard({ label, value, status, icon }: { label: string; value: string; status: string; icon: keyof typeof Ionicons.glyphMap }) {
  const info = BMI_STATUS_MAP[status] || { color: COLORS.textSecondary, bg: '#F5F5F5' };
  return (
    <View style={styles.metricCard}>
      <View style={[styles.metricIcon, { backgroundColor: info.bg }]}>
        <Ionicons name={icon} size={18} color={info.color} />
      </View>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
      <StatusBadge status={status} value={status} />
    </View>
  );
}

function BarChart({ data, color, maxVal }: { data: number[]; color: string; maxVal: number }) {
  const barWidth = (width - 96) / data.length - 6;
  return (
    <View style={styles.barRow}>
      {data.map((v, i) => {
        const isLast = i === data.length - 1;
        const height = Math.max((v / maxVal) * 90, 4);
        return (
          <View key={i} style={styles.barCol}>
            <LinearGradient
              colors={isLast ? [color, color] : [color + '99', color + '55']}
              style={[styles.bar, { width: barWidth, height }]}
              start={{ x: 0, y: 0 }}
              end={{ x: 0, y: 1 }}
            />
          </View>
        );
      })}
    </View>
  );
}

export default function HealthScreen() {
  const insets = useSafeAreaInsets();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
  const [report, setReport] = useState<HealthReport | null>(null);
  const [weeklyStats, setWeeklyStats] = useState<WeeklyStats | null>(null);
  const [dietStats, setDietStats] = useState<DietStats | null>(null);
  const [measurements, setMeasurements] = useState<HealthMeasurement[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [period, setPeriod] = useState<'week' | 'month'>('month');
  const [showAddModal, setShowAddModal] = useState(false);
  const [form, setForm] = useState({ weight: '', height: '', bodyFat: '' });

  const loadData = useCallback(async () => {
    try {
      const [p, m, r, ws, ds, ms] = await Promise.all([
        userApi.getProfile().catch(() => null),
        healthApi.getMetrics().catch(() => null),
        healthApi.getReport(period).catch(() => null),
        trainingApi.getWeeklyStats().catch(() => null),
        dietApi.getTodayStats().catch(() => null),
        healthApi.getMeasurements(12).catch(() => []),
      ]);
      if (p) setProfile(p);
      if (m) setMetrics(m);
      if (r) setReport(r);
      if (ws) setWeeklyStats(ws);
      if (ds) setDietStats(ds);
      setMeasurements(ms || []);
    } catch {}
  }, [period]);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const trendData = useMemo(() => {
    if (!report) return [];
    return period === 'week' ? report.weightTrend.slice(-7) : report.weightTrend;
  }, [period, report]);

  const handleSaveMetric = async () => {
    if (!form.weight || !form.height || !form.bodyFat) {
      Alert.alert('提示', '请填写完整的健康数据');
      return;
    }
    try {
      await healthApi.createMetric({
        weight: parseFloat(form.weight),
        height: parseFloat(form.height),
        bodyFat: parseFloat(form.bodyFat),
        measureDate: new Date().toISOString().slice(0, 10),
      });
      setForm({ weight: '', height: '', bodyFat: '' });
      setShowAddModal(false);
      loadData();
    } catch (e: any) {
      Alert.alert('错误', e.message || '保存失败');
    }
  };

  const handleExport = () => {
    Alert.alert('说明', '移动端暂不直接导出文件，请在 Web 端导出健康数据。');
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      showsVerticalScrollIndicator={false}
    >
      {/* Compact Header */}
      <View style={[styles.header, { paddingTop: insets.top + 6 }]}>
        <Text style={styles.headerTitle}>健康数据</Text>
        <Text style={styles.headerSub}>
          {new Date().getMonth() + 1}月{new Date().getDate()}日
        </Text>
      </View>

      <View style={styles.summaryGrid}>
        <View style={[styles.summaryCard, { backgroundColor: COLORS.blueBg }]}>
          <Text style={styles.summaryLabel}>本周训练</Text>
          <Text style={styles.summaryValue}>{weeklyStats?.weeklyCount || 0} 次</Text>
        </View>
        <View style={[styles.summaryCard, { backgroundColor: COLORS.greenBg }]}>
          <Text style={styles.summaryLabel}>剩余热量</Text>
          <Text style={styles.summaryValue}>{dietStats?.remainingCalories || 0} kcal</Text>
        </View>
        <View style={[styles.summaryCard, { backgroundColor: COLORS.purpleBg }]}>
          <Text style={styles.summaryLabel}>连续训练</Text>
          <Text style={styles.summaryValue}>{weeklyStats?.streakDays || 0} 天</Text>
        </View>
        <View style={[styles.summaryCard, { backgroundColor: COLORS.orangeBg }]}>
          <Text style={styles.summaryLabel}>当前体重</Text>
          <Text style={styles.summaryValue}>{metrics?.weight || 0} kg</Text>
        </View>
      </View>

      {dietStats && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>今日营养概览</Text>
          {[
            ['蛋白质', dietStats.protein, dietStats.proteinGoal, '#3B82F6'],
            ['碳水', dietStats.carbs, dietStats.carbsGoal, '#F59E0B'],
            ['脂肪', dietStats.fat, dietStats.fatGoal, '#EF4444'],
            ['饮水', dietStats.water, dietStats.waterGoal, COLORS.primary],
          ].map(([label, current, goal, color]) => {
            const percent = Math.min((Number(current) / Math.max(Number(goal), 1)) * 100, 100);
            return (
              <View key={String(label)} style={{ marginTop: 10 }}>
                <View style={styles.progressHeader}>
                  <Text style={styles.progressLabel}>{label}</Text>
                  <Text style={styles.progressValue}>{current}/{goal}</Text>
                </View>
                <View style={styles.progressTrack}>
                  <View style={[styles.progressFill, { width: `${percent}%`, backgroundColor: String(color) }]} />
                </View>
              </View>
            );
          })}
        </View>
      )}

      {/* Profile Card */}
      <View style={[styles.card, styles.profileCard]}>
        <View style={styles.profileHeader}>
          <LinearGradient
            colors={[COLORS.gradientStart, COLORS.gradientEnd]}
            style={styles.avatarCircle}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Text style={styles.avatarText}>{profile?.name?.[0] || 'U'}</Text>
          </LinearGradient>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>{profile?.name || '加载中...'}</Text>
            <Text style={styles.profileDetail}>
              {metrics ? `${metrics.height}cm` : '--'} | BMI: {metrics?.bmi?.toFixed(1) || '--'}
            </Text>
          </View>
          <View style={styles.profileArrow}>
            <Ionicons name="chevron-forward" size={20} color={COLORS.textTertiary} />
          </View>
        </View>
        {metrics && (
          <View style={styles.metricsGrid}>
            <MetricCard label="体重" value={`${metrics.weight}kg`} status={metrics.bmiStatus} icon="scale-outline" />
            <MetricCard label="身高" value={`${metrics.height}cm`} status="normal" icon="resize-outline" />
            <MetricCard label="体脂率" value={`${metrics.bodyFat}%`} status={metrics.bmiStatus} icon="water-outline" />
            <MetricCard label="BMI" value={metrics.bmi.toFixed(1)} status={metrics.bmiStatus} icon="heart-outline" />
          </View>
        )}
      </View>

      <View style={styles.card}>
        <View style={styles.actionHeader}>
          <Text style={styles.sectionTitle}>健康管理</Text>
          <View style={styles.actionButtons}>
            <TouchableOpacity style={styles.secondaryBtn} onPress={handleExport}>
              <Text style={styles.secondaryBtnText}>导出</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.primaryBtn} onPress={() => setShowAddModal(true)}>
              <Text style={styles.primaryBtnText}>新增记录</Text>
            </TouchableOpacity>
          </View>
        </View>
        {measurements.length ? measurements.map(item => (
          <View key={item.recordId} style={styles.measureRow}>
            <View style={styles.measureBadge}>
              <Text style={styles.measureBadgeText}>{item.measureDate.slice(5)}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.measureTitle}>{item.weight}kg · 体脂 {item.bodyFat}%</Text>
              <Text style={styles.measureMeta}>BMI {item.bmi.toFixed(1)} · {BMI_STATUS_MAP[item.bmiStatus]?.label || item.bmiStatus}</Text>
            </View>
          </View>
        )) : (
          <Text style={styles.emptyText}>暂无历史记录</Text>
        )}
      </View>

      {/* Report */}
      {report && (
        <View style={styles.card}>
          <View style={styles.reportHeader}>
            <Text style={styles.reportTitle}>健康数据报表</Text>
            <View style={styles.periodSwitch}>
              <TouchableOpacity style={[styles.periodChip, period === 'week' && styles.periodChipActive]} onPress={() => setPeriod('week')}>
                <Text style={[styles.periodChipText, period === 'week' && styles.periodChipTextActive]}>近7天</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.periodChip, period === 'month' && styles.periodChipActive]} onPress={() => setPeriod('month')}>
                <Text style={[styles.periodChipText, period === 'month' && styles.periodChipTextActive]}>近30天</Text>
              </TouchableOpacity>
            </View>
          </View>

          {report.summary?.statusSummary && (
            <View style={styles.filterRow}>
              <View style={[styles.filterTab, styles.filterActive]}>
                <Text style={styles.filterActiveText}>全部</Text>
              </View>
              <View style={[styles.filterTab, { backgroundColor: COLORS.successLight }]}>
                <Ionicons name="checkmark-circle" size={14} color={COLORS.success} />
                <Text style={styles.statusText}>{report.summary.statusSummary.normal}项达标</Text>
              </View>
              <View style={[styles.filterTab, { backgroundColor: COLORS.warningLight }]}>
                <Ionicons name="remove-circle" size={14} color={COLORS.warning} />
                <Text style={styles.statusText}>{report.summary.statusSummary.low}项偏低</Text>
              </View>
              <View style={[styles.filterTab, { backgroundColor: COLORS.dangerLight }]}>
                <Ionicons name="alert-circle" size={14} color={COLORS.danger} />
                <Text style={[styles.statusText, { color: COLORS.danger }]}>{report.summary.statusSummary.high}项偏高</Text>
              </View>
            </View>
          )}

          {trendData.length > 0 && (
            <View style={styles.chartSection}>
              <View style={styles.chartHeader}>
                <View style={styles.chartTitleWrap}>
                  <View style={[styles.chartDot, { backgroundColor: COLORS.primary }]} />
                  <Text style={styles.chartTitle}>体重趋势</Text>
                </View>
                <Text style={styles.chartValue}>
                  {report.summary.weightChange > 0 ? '+' : ''}{report.summary.weightChange.toFixed(2)}kg
                </Text>
              </View>
              <BarChart
                data={trendData.map((d) => d.value)}
                color={COLORS.primary}
                maxVal={Math.max(...trendData.map((d) => d.value), 1) * 1.1}
              />
            </View>
          )}

          {report.bmiTrend.length > 0 && (
            <View style={styles.chartSection}>
              <View style={styles.chartHeader}>
                <View style={styles.chartTitleWrap}>
                  <View style={[styles.chartDot, { backgroundColor: '#8B5CF6' }]} />
                  <Text style={styles.chartTitle}>BMI 趋势</Text>
                </View>
                <Text style={styles.chartValue}>{report.summary.avgBmi.toFixed(1)}</Text>
              </View>
              <BarChart
                data={report.bmiTrend.map((d) => d.value)}
                color="#8B5CF6"
                maxVal={Math.max(...report.bmiTrend.map((d) => d.value)) * 1.1}
              />
            </View>
          )}
        </View>
      )}

      <View style={{ height: 24 }} />

      <Modal visible={showAddModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setShowAddModal(false)}>
                <Ionicons name="close" size={22} color={COLORS.text} />
              </TouchableOpacity>
              <Text style={styles.modalTitle}>新增健康记录</Text>
              <TouchableOpacity onPress={handleSaveMetric}>
                <Text style={styles.modalSave}>保存</Text>
              </TouchableOpacity>
            </View>

            {[
              ['weight', '体重 (kg)'],
              ['height', '身高 (cm)'],
              ['bodyFat', '体脂率 (%)'],
            ].map(([key, label]) => (
              <View key={key} style={{ marginTop: 12 }}>
                <Text style={styles.inputLabel}>{label}</Text>
                <TextInput
                  style={styles.input}
                  value={(form as any)[key]}
                  onChangeText={value => setForm(prev => ({ ...prev, [key]: value }))}
                  keyboardType="numeric"
                />
              </View>
            ))}
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  headerSub: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginHorizontal: 16,
    marginTop: 12,
  },
  summaryCard: {
    width: (width - 42) / 2,
    borderRadius: 16,
    padding: 16,
  },
  summaryLabel: { fontSize: 12, color: COLORS.textSecondary },
  summaryValue: { fontSize: 20, fontWeight: '700', color: COLORS.text, marginTop: 6 },
  card: {
    backgroundColor: COLORS.card,
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 16,
    padding: 20,
    ...SHADOWS.card,
  },
  profileCard: {
    marginTop: 12,
  },
  profileHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
  avatarCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: { fontSize: 24, color: COLORS.white, fontWeight: 'bold' },
  profileInfo: { marginLeft: 14, flex: 1 },
  profileName: { fontSize: 20, fontWeight: '700', color: COLORS.text },
  profileDetail: { fontSize: 14, color: COLORS.textSecondary, marginTop: 2 },
  profileArrow: { padding: 4 },
  metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  metricCard: {
    width: (width - 72) / 2 - 5,
    backgroundColor: COLORS.background,
    borderRadius: 14,
    padding: 14,
    gap: 4,
  },
  metricIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  metricLabel: { fontSize: 12, color: COLORS.textSecondary },
  metricValue: { fontSize: 20, fontWeight: 'bold', color: COLORS.text },
  badge: { alignSelf: 'flex-start', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6, marginTop: 2 },
  badgeText: { fontSize: 11, fontWeight: '600' },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: COLORS.text },
  progressHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  progressLabel: { fontSize: 13, color: COLORS.text },
  progressValue: { fontSize: 12, color: COLORS.textSecondary },
  progressTrack: { height: 10, backgroundColor: COLORS.divider, borderRadius: 999, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 999 },
  actionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  actionButtons: { flexDirection: 'row', gap: 8 },
  primaryBtn: { backgroundColor: COLORS.primary, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8 },
  primaryBtnText: { color: COLORS.white, fontWeight: '700' },
  secondaryBtn: { backgroundColor: COLORS.background, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8 },
  secondaryBtnText: { color: COLORS.textSecondary, fontWeight: '600' },
  measureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 10,
    borderBottomColor: COLORS.divider,
    borderBottomWidth: 1,
  },
  measureBadge: {
    width: 54,
    height: 54,
    borderRadius: 14,
    backgroundColor: COLORS.blueBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  measureBadgeText: { color: COLORS.primary, fontWeight: '700', fontSize: 12 },
  measureTitle: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  measureMeta: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  emptyText: { color: COLORS.textSecondary, marginTop: 8 },
  filterRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  filterTab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: COLORS.background,
    gap: 4,
  },
  filterActive: { backgroundColor: COLORS.blueBg },
  filterActiveText: { color: COLORS.primary, fontWeight: '600', fontSize: 13 },
  statusText: { color: COLORS.success, fontWeight: '500', fontSize: 13 },
  reportHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  reportTitle: { fontSize: 18, fontWeight: '700', color: COLORS.text },
  periodSwitch: { flexDirection: 'row', gap: 8 },
  periodChip: { backgroundColor: COLORS.background, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 999 },
  periodChipActive: { backgroundColor: COLORS.blueBg },
  periodChipText: { fontSize: 12, color: COLORS.textSecondary },
  periodChipTextActive: { color: COLORS.primary, fontWeight: '700' },
  chartSection: { marginTop: 20 },
  chartHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  chartTitleWrap: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  chartDot: { width: 8, height: 8, borderRadius: 4 },
  chartTitle: { fontSize: 14, fontWeight: '600', color: COLORS.text },
  chartValue: { fontSize: 14, color: COLORS.textSecondary, fontWeight: '500' },
  barRow: { flexDirection: 'row', alignItems: 'flex-end', height: 100, gap: 6 },
  barCol: { flex: 1, alignItems: 'center', justifyContent: 'flex-end' },
  bar: { borderRadius: 6, minHeight: 4 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.28)', justifyContent: 'flex-end' },
  modalContent: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    minHeight: 300,
  },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  modalTitle: { fontSize: 18, fontWeight: '700', color: COLORS.text },
  modalSave: { fontSize: 16, color: COLORS.primary, fontWeight: '700' },
  inputLabel: { color: COLORS.textSecondary, marginBottom: 6 },
  input: {
    backgroundColor: COLORS.background,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
});
