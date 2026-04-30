import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, StyleSheet, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import HealthScreen from '../screens/Health/HealthScreen';
import TrainingScreen from '../screens/Training/TrainingScreen';
import DietScreen from '../screens/Diet/DietScreen';
import ChatScreen from '../screens/Chat/ChatScreen';
import ProfileScreen from '../screens/Profile/ProfileScreen';
import { COLORS, SHADOWS } from '../constants';

const Tab = createBottomTabNavigator();

const TAB_CONFIG: Record<string, { icon: keyof typeof Ionicons.glyphMap; iconActive: keyof typeof Ionicons.glyphMap }> = {
  '健康': { icon: 'heart-outline', iconActive: 'heart' },
  '训练': { icon: 'barbell-outline', iconActive: 'barbell' },
  '饮食': { icon: 'nutrition-outline', iconActive: 'nutrition' },
  'AI': { icon: 'chatbubble-ellipses-outline', iconActive: 'chatbubble-ellipses' },
  '我的': { icon: 'person-outline', iconActive: 'person' },
};

export default function MainTabs({ onLogout }: { onLogout: () => void }) {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => {
        const config = TAB_CONFIG[route.name] || { icon: 'help-outline' as keyof typeof Ionicons.glyphMap, iconActive: 'help' as keyof typeof Ionicons.glyphMap };
        return {
          headerShown: false,
          tabBarIcon: ({ focused, size }) => (
            <Ionicons
              name={focused ? config.iconActive : config.icon}
              size={focused ? 26 : 22}
              color={focused ? COLORS.primary : COLORS.textTertiary}
            />
          ),
          tabBarActiveTintColor: COLORS.primary,
          tabBarInactiveTintColor: COLORS.textTertiary,
          tabBarStyle: {
            height: Platform.OS === 'ios' ? 84 : 64,
            paddingTop: 6,
            paddingBottom: Platform.OS === 'ios' ? 28 : 8,
            borderTopWidth: 0,
            backgroundColor: COLORS.white,
            ...SHADOWS.card,
          },
          tabBarLabelStyle: {
            fontSize: 11,
            fontWeight: '500',
            marginTop: 2,
          },
        };
      }}
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
});
