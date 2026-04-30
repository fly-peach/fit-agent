import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, StyleSheet } from 'react-native';
import HealthScreen from '../screens/Health/HealthScreen';
import TrainingScreen from '../screens/Training/TrainingScreen';
import DietScreen from '../screens/Diet/DietScreen';
import ChatScreen from '../screens/Chat/ChatScreen';
import ProfileScreen from '../screens/Profile/ProfileScreen';
import { COLORS } from '../constants';

const Tab = createBottomTabNavigator();

function TabIcon({ name, focused }: { name: string; focused: boolean }) {
  const icons: Record<string, string> = {
    健康: '♥',
    训练: '📋',
    饮食: '🍎',
    AI: '✨',
    我的: '👤',
  };
  return (
    <View style={styles.iconContainer}>
      <Text style={[styles.icon, focused && styles.iconActive]}>{icons[name] || '?'}</Text>
      {focused && <View style={styles.indicator} />}
    </View>
  );
}

export default function MainTabs({ onLogout }: { onLogout: () => void }) {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused }) => <TabIcon name={route.name} focused={focused} />,
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: COLORS.textSecondary,
        tabBarStyle: {
          height: 60,
          borderTopWidth: 1,
          borderTopColor: COLORS.border,
          backgroundColor: COLORS.white,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          marginBottom: 4,
        },
      })}
    >
      <Tab.Screen name="健康" component={HealthScreen} />
      <Tab.Screen name="训练" component={TrainingScreen} />
      <Tab.Screen name="饮食" component={DietScreen} />
      <Tab.Screen name="AI" component={ChatScreen} />
      <Tab.Screen name="我的">
        {() => <ProfileScreen onLogout={onLogout} />}
      </Tab.Screen>
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  iconContainer: { alignItems: 'center', justifyContent: 'center' },
  icon: { fontSize: 22, color: COLORS.textSecondary },
  iconActive: { color: COLORS.primary },
  indicator: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: COLORS.primary,
    marginTop: 2,
  },
});
