import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { healthApi } from '../../services/health';
import { userApi } from '../../services/user';
import { COLORS, BMI_STATUS_MAP } from '../../constants';
import type { HealthMetrics, HealthReport, UserProfile } from '../../types';

const { width } = Dimensions.get('window');

function StatusBadge({ status, value }: { status: string; value: string }) {
  const info = BMI_STATUS_MAP[status] || { label: value, color: COLORS.textSecondary };
  return (
    <View style={[styles.badge, { backgroundColor: info.color + '18' }]}>
      <Text style={[styles.badgeText, { color: info.color }]}>{info.label || value}</Text>
    </View>
  );
}

function MetricCard({ label, value, status }: { label: string; value: string; status: string }) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
      <StatusBadge status={status} value={status} />
    </View>
  );
}

function BarChart({ data, color, maxVal }: { data: number[]; color: string; maxVal: number }) {
  const barWidth = (width - 80) / data.length - 8;
  return (
    <View style={styles.barRow}>
      {data.map((v, i) => (
        <View key={i} style={styles.barCol}>
          <View style={[styles.bar, { width: barWidth, height: (v / maxVal) * 100, backgroundColor: color + (i === data.length - 1 ? 'ff' : '66') }]} />
        </View>
      ))}
    </View>
  );
}

export default function HealthScreen() {
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
    >
      <View style={styles.topBar}>
        <Text style={styles.topTitle}>健康数据</Text>
      </View>

      {/* Profile Card */}
      <View style={styles.card}>
        <View style={styles.profileHeader}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarText}>{profile?.name?.[0] || 'U'}</Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>{profile?.name || '加载中...'}</Text>
            <Text style={styles.profileDetail}>
              {metrics ? `${metrics.height}cm` : '--'} | BMI: {metrics?.bmi?.toFixed(1) || '--'}
            </Text>
          </View>
        </View>
        {metrics && (
          <View style={styles.metricsGrid}>
            <MetricCard label="体重" value={`${metrics.weight}kg`} status={metrics.bmiStatus} />
            <MetricCard label="身高" value={`${metrics.height}cm`} status="normal" />
            <MetricCard label="体脂率" value={`${metrics.bodyFat}%`} status={metrics.bmiStatus} />
            <MetricCard label="BMI" value={metrics.bmi.toFixed(1)} status={metrics.bmiStatus} />
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
            <View style={styles.filterTab}>
              <Text style={{ color: COLORS.success }}>{report.summary.statusSummary.pass}项达标</Text>
            </View>
            <View style={styles.filterTab}>
              <Text style={{ color: COLORS.danger }}>{report.summary.statusSummary.low}项偏低</Text>
            </View>
            <View style={styles.filterTab}>
              <Text style={{ color: COLORS.warning }}>{report.summary.statusSummary.high}项偏高</Text>
            </View>
          </View>
        </View>
      )}

      {/* Report */}
      {report && (
        <View style={styles.card}>
          <View style={styles.reportHeader}>
            <Text style={styles.reportTitle}>健康数据报表</Text>
            <Text style={styles.reportPeriod}>近30天</Text>
          </View>

          {report.weightTrend.length > 0 && (
            <View style={styles.chartSection}>
              <View style={styles.chartHeader}>
                <Text style={styles.chartTitle}>体重趋势</Text>
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
                <Text style={styles.chartTitle}>BMI 趋势</Text>
                <Text style={styles.chartValue}>{report.summary.avgBmi.toFixed(1)}</Text>
              </View>
              <BarChart
                data={report.bmiTrend.map((d) => d.value)}
                color="#722ED1"
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
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 56,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  topTitle: { fontSize: 18, fontWeight: '600', color: COLORS.text },
  card: {
    backgroundColor: COLORS.white,
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 16,
  },
  profileHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  avatarCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: { fontSize: 24, color: COLORS.primary, fontWeight: 'bold' },
  profileInfo: { marginLeft: 12, flex: 1 },
  profileName: { fontSize: 18, fontWeight: '600', color: COLORS.text },
  profileDetail: { fontSize: 14, color: COLORS.textSecondary, marginTop: 2 },
  metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  metricCard: {
    width: (width - 56) / 2 - 4,
    backgroundColor: COLORS.background,
    borderRadius: 10,
    padding: 12,
    gap: 4,
  },
  metricLabel: { fontSize: 13, color: COLORS.textSecondary },
  metricValue: { fontSize: 20, fontWeight: 'bold', color: COLORS.text },
  badge: { alignSelf: 'flex-start', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  badgeText: { fontSize: 12, fontWeight: '500' },
  filterRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  filterTab: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: COLORS.background,
  },
  filterActive: { backgroundColor: COLORS.primary + '18' },
  filterActiveText: { color: COLORS.primary, fontWeight: '500' },
  reportHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  reportTitle: { fontSize: 16, fontWeight: '600', color: COLORS.text },
  reportPeriod: { fontSize: 13, color: COLORS.textSecondary },
  chartSection: { marginTop: 16 },
  chartHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  chartTitle: { fontSize: 14, fontWeight: '500', color: COLORS.text },
  chartValue: { fontSize: 14, color: COLORS.textSecondary },
  barRow: { flexDirection: 'row', alignItems: 'flex-end', height: 110, gap: 8 },
  barCol: { flex: 1, alignItems: 'center', justifyContent: 'flex-end' },
  bar: { borderRadius: 4, minHeight: 4 },
});
