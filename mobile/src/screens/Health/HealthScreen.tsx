import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { healthApi } from '../../services/health';
import { userApi } from '../../services/user';
import { COLORS, SHADOWS, BMI_STATUS_MAP } from '../../constants';
import type { HealthMetrics, HealthReport, UserProfile } from '../../types';

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
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [p, m, r] = await Promise.all([
        userApi.getProfile().catch(() => null),
        healthApi.getMetrics().catch(() => null),
        healthApi.getReport('month').catch(() => null),
      ]);
      if (p) setProfile(p);
      if (m) setMetrics(m);
      if (r) setReport(r);
    } catch {}
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
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

      {/* Filter Tabs */}
      {report?.summary?.statusSummary && (
        <View style={styles.card}>
          <View style={styles.filterRow}>
            <View style={[styles.filterTab, styles.filterActive]}>
              <Text style={styles.filterActiveText}>全部</Text>
            </View>
            <View style={[styles.filterTab, { backgroundColor: COLORS.successLight }]}>
              <Ionicons name="checkmark-circle" size={14} color={COLORS.success} />
              <Text style={{ color: COLORS.success, fontWeight: '500', fontSize: 13 }}>{report.summary.statusSummary.normal}项达标</Text>
            </View>
            <View style={[styles.filterTab, { backgroundColor: COLORS.warningLight }]}>
              <Ionicons name="remove-circle" size={14} color={COLORS.warning} />
              <Text style={{ color: COLORS.warning, fontWeight: '500', fontSize: 13 }}>{report.summary.statusSummary.low}项偏低</Text>
            </View>
            <View style={[styles.filterTab, { backgroundColor: COLORS.dangerLight }]}>
              <Ionicons name="alert-circle" size={14} color={COLORS.danger} />
              <Text style={{ color: COLORS.danger, fontWeight: '500', fontSize: 13 }}>{report.summary.statusSummary.high}项偏高</Text>
            </View>
          </View>
        </View>
      )}

      {/* Report */}
      {report && (
        <View style={styles.card}>
          <View style={styles.reportHeader}>
            <Text style={styles.reportTitle}>健康数据报表</Text>
            <View style={styles.periodBadge}>
              <Text style={styles.periodText}>近30天</Text>
            </View>
          </View>

          {report.weightTrend.length > 0 && (
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
                data={report.weightTrend.map((d) => d.value)}
                color={COLORS.primary}
                maxVal={Math.max(...report.weightTrend.map((d) => d.value)) * 1.1}
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
  reportHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  reportTitle: { fontSize: 18, fontWeight: '700', color: COLORS.text },
  periodBadge: {
    backgroundColor: COLORS.purpleBg,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  periodText: { fontSize: 12, color: '#7C3AED', fontWeight: '500' },
  chartSection: { marginTop: 20 },
  chartHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  chartTitleWrap: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  chartDot: { width: 8, height: 8, borderRadius: 4 },
  chartTitle: { fontSize: 14, fontWeight: '600', color: COLORS.text },
  chartValue: { fontSize: 14, color: COLORS.textSecondary, fontWeight: '500' },
  barRow: { flexDirection: 'row', alignItems: 'flex-end', height: 100, gap: 6 },
  barCol: { flex: 1, alignItems: 'center', justifyContent: 'flex-end' },
  bar: { borderRadius: 6, minHeight: 4 },
});
