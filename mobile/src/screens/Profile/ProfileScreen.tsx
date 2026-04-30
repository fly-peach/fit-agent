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
import { userApi } from '../../services/user';
import { authApi } from '../../services/auth';
import { storage } from '../../utils/storage';
import { COLORS } from '../../constants';
import type { UserProfile, UserSettings } from '../../types';

interface Props {
  onLogout: () => void;
}

export default function ProfileScreen({ onLogout }: Props) {
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

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.topBar}>
        <Text style={styles.topTitle}>个人中心</Text>
      </View>

      {/* Profile Card */}
      <View style={styles.card}>
        <View style={styles.profileHeader}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarText}>{profile?.name?.[0] || 'U'}</Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>{profile?.name || '加载中...'}</Text>
            <Text style={styles.profileEmail}>{profile?.email || ''}</Text>
          </View>
        </View>
      </View>

      {/* Settings */}
      {settings && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>目标设置</Text>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>每日热量目标</Text>
            <Text style={styles.settingValue}>{settings.calorieGoal} kcal</Text>
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>蛋白质目标</Text>
            <Text style={styles.settingValue}>{settings.proteinGoal}g</Text>
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>碳水目标</Text>
            <Text style={styles.settingValue}>{settings.carbsGoal}g</Text>
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>脂肪目标</Text>
            <Text style={styles.settingValue}>{settings.fatGoal}g</Text>
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>饮水目标</Text>
            <Text style={styles.settingValue}>{settings.waterGoal}ml</Text>
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>体重目标</Text>
            <Text style={styles.settingValue}>{settings.weightGoal || '--'}kg</Text>
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>每周训练目标</Text>
            <Text style={styles.settingValue}>{settings.weeklyTrainingGoal} 次</Text>
          </View>
        </View>
      )}

      {/* Logout */}
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>退出登录</Text>
      </TouchableOpacity>

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
  profileHeader: { flexDirection: 'row', alignItems: 'center' },
  avatarCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: COLORS.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: { fontSize: 28, color: COLORS.primary, fontWeight: 'bold' },
  profileInfo: { marginLeft: 16, flex: 1 },
  profileName: { fontSize: 20, fontWeight: '600', color: COLORS.text },
  profileEmail: { fontSize: 14, color: COLORS.textSecondary, marginTop: 4 },
  cardTitle: { fontSize: 16, fontWeight: '600', color: COLORS.text, marginBottom: 12 },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  settingLabel: { fontSize: 15, color: COLORS.text },
  settingValue: { fontSize: 15, color: COLORS.textSecondary },
  logoutBtn: {
    marginHorizontal: 16,
    marginTop: 24,
    height: 50,
    borderRadius: 10,
    backgroundColor: COLORS.danger + '18',
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoutText: { color: COLORS.danger, fontSize: 16, fontWeight: '600' },
});
