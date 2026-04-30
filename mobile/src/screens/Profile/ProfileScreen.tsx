import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { userApi } from '../../services/user';
import { authApi } from '../../services/auth';
import { storage } from '../../utils/storage';
import { COLORS, SHADOWS } from '../../constants';
import type { UserProfile, UserSettings } from '../../types';

interface Props {
  onLogout: () => void;
}

const SETTING_ICONS: Record<string, { icon: keyof typeof Ionicons.glyphMap; color: string; bg: string }> = {
  calorieGoal: { icon: 'flame', color: '#EF4444', bg: '#FEE2E2' },
  proteinGoal: { icon: 'egg', color: '#3B82F6', bg: '#DBEAFE' },
  carbsGoal: { icon: 'pizza', color: '#F59E0B', bg: '#FEF3C7' },
  fatGoal: { icon: 'water', color: '#8B5CF6', bg: '#EDE9FE' },
  waterGoal: { icon: 'water-outline', color: '#06B6D4', bg: '#CFFAFE' },
  weightGoal: { icon: 'scale', color: '#10B981', bg: '#D1FAE5' },
  weeklyTrainingGoal: { icon: 'barbell', color: '#6366F1', bg: '#E0E7FF' },
};

const SETTING_LABELS: Record<string, string> = {
  calorieGoal: '每日热量目标',
  proteinGoal: '蛋白质目标',
  carbsGoal: '碳水目标',
  fatGoal: '脂肪目标',
  waterGoal: '饮水目标',
  weightGoal: '体重目标',
  weeklyTrainingGoal: '每周训练目标',
};

const SETTING_UNITS: Record<string, string> = {
  calorieGoal: 'kcal',
  proteinGoal: 'g',
  carbsGoal: 'g',
  fatGoal: 'g',
  waterGoal: 'ml',
  weightGoal: 'kg',
  weeklyTrainingGoal: '次',
};

export default function ProfileScreen({ onLogout }: Props) {
  const insets = useSafeAreaInsets();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [p, s] = await Promise.all([
        userApi.getProfile().catch(() => null),
        userApi.getSettings().catch(() => null),
      ]);
      if (p) setProfile(p);
      if (s) setSettings(s);
    } catch {}
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleLogout = async () => {
    Alert.alert('确认', '确定退出登录？', [
      { text: '取消', style: 'cancel' },
      {
        text: '退出',
        style: 'destructive',
        onPress: async () => {
          try { await authApi.logout(); } catch {}
          await storage.removeItem('token');
          await storage.removeItem('user');
          onLogout();
        },
      },
    ]);
  };

  const settingEntries = settings
    ? Object.entries(SETTING_LABELS).filter(([key]) => settings[key as keyof UserSettings] != null)
    : [];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      showsVerticalScrollIndicator={false}
    >
      {/* Compact Header */}
      <View style={[styles.header, { paddingTop: insets.top + 6 }]}>
        <Text style={styles.headerTitle}>个人中心</Text>
      </View>

      {/* Profile Card */}
      <View style={[styles.card, styles.profileCard]}>
        <LinearGradient
          colors={[COLORS.gradientStart, COLORS.gradientEnd]}
          style={styles.avatarCircle}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <Text style={styles.avatarText}>{profile?.name?.[0] || 'U'}</Text>
        </LinearGradient>
        <Text style={styles.profileName}>{profile?.name || '加载中...'}</Text>
        <View style={styles.emailRow}>
          <Ionicons name="mail-outline" size={14} color={COLORS.textSecondary} />
          <Text style={styles.profileEmail}>{profile?.email || ''}</Text>
        </View>
      </View>

      {/* Settings */}
      {settings && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>目标设置</Text>
          {settingEntries.map(([key, label], idx) => {
            const config = SETTING_ICONS[key] || { icon: 'settings-outline' as keyof typeof Ionicons.glyphMap, color: COLORS.textSecondary, bg: COLORS.background };
            const value = settings[key as keyof UserSettings];
            const unit = SETTING_UNITS[key] || '';
            return (
              <View key={key} style={[styles.settingRow, idx === settingEntries.length - 1 && { borderBottomWidth: 0 }]}>
                <View style={[styles.settingIcon, { backgroundColor: config.bg }]}>
                  <Ionicons name={config.icon} size={18} color={config.color} />
                </View>
                <Text style={styles.settingLabel}>{label}</Text>
                <Text style={styles.settingValue}>{value} {unit}</Text>
                <Ionicons name="chevron-forward" size={16} color={COLORS.textTertiary} />
              </View>
            );
          })}
        </View>
      )}

      {/* Quick Actions */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>快捷操作</Text>
        <TouchableOpacity style={styles.actionRow}>
          <View style={[styles.settingIcon, { backgroundColor: COLORS.blueBg }]}>
            <Ionicons name="notifications-outline" size={18} color={COLORS.primary} />
          </View>
          <Text style={styles.settingLabel}>消息通知</Text>
          <Ionicons name="chevron-forward" size={16} color={COLORS.textTertiary} />
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionRow}>
          <View style={[styles.settingIcon, { backgroundColor: COLORS.purpleBg }]}>
            <Ionicons name="help-circle-outline" size={18} color="#7C3AED" />
          </View>
          <Text style={styles.settingLabel}>帮助与反馈</Text>
          <Ionicons name="chevron-forward" size={16} color={COLORS.textTertiary} />
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionRow, { borderBottomWidth: 0 }]}>
          <View style={[styles.settingIcon, { backgroundColor: COLORS.greenBg }]}>
            <Ionicons name="information-circle-outline" size={18} color={COLORS.success} />
          </View>
          <Text style={styles.settingLabel}>关于我们</Text>
          <Ionicons name="chevron-forward" size={16} color={COLORS.textTertiary} />
        </TouchableOpacity>
      </View>

      {/* Logout */}
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout} activeOpacity={0.7}>
        <Ionicons name="log-out-outline" size={20} color={COLORS.danger} />
        <Text style={styles.logoutText}>退出登录</Text>
      </TouchableOpacity>

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
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: COLORS.text },
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
    alignItems: 'center',
    paddingTop: 28,
  },
  avatarCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatarText: { fontSize: 30, color: COLORS.white, fontWeight: 'bold' },
  profileName: { fontSize: 22, fontWeight: '700', color: COLORS.text, marginBottom: 6 },
  emailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: COLORS.background,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 12,
  },
  profileEmail: { fontSize: 13, color: COLORS.textSecondary },
  cardTitle: { fontSize: 18, fontWeight: '700', color: COLORS.text, marginBottom: 16 },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
    gap: 12,
  },
  settingIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  settingLabel: { fontSize: 15, color: COLORS.text, flex: 1 },
  settingValue: { fontSize: 14, color: COLORS.textSecondary, fontWeight: '500' },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
    gap: 12,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 16,
    marginTop: 24,
    height: 52,
    borderRadius: 14,
    backgroundColor: COLORS.dangerLight,
    gap: 8,
  },
  logoutText: { color: COLORS.danger, fontSize: 16, fontWeight: '600' },
});
