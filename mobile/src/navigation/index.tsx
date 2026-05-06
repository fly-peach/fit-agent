import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import HealthScreen from '../screens/Health/HealthScreen';
import TrainingScreen from '../screens/Training/TrainingScreen';
import TrainingCreateScreen from '../screens/Training/TrainingCreateScreen';
import TrainingPlanDetailScreen from '../screens/Training/TrainingPlanDetailScreen';
import TrainingCalendarScreen from '../screens/Training/TrainingCalendarScreen';
import DietScreen from '../screens/Diet/DietScreen';
import DietTrendScreen from '../screens/Diet/DietTrendScreen';
import FoodLibraryScreen from '../screens/Diet/FoodLibraryScreen';
import CustomFoodScreen from '../screens/Diet/CustomFoodScreen';
import ChatScreen from '../screens/Chat/ChatScreen';
import ProfileScreen from '../screens/Profile/ProfileScreen';
import { COLORS, SHADOWS } from '../constants';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const TAB_CONFIG: Record<string, { icon: keyof typeof Ionicons.glyphMap; iconActive: keyof typeof Ionicons.glyphMap }> = {
  '健康': { icon: 'heart-outline', iconActive: 'heart' },
  '训练': { icon: 'barbell-outline', iconActive: 'barbell' },
  '饮食': { icon: 'nutrition-outline', iconActive: 'nutrition' },
  'AI': { icon: 'chatbubble-ellipses-outline', iconActive: 'chatbubble-ellipses' },
  '我的': { icon: 'person-outline', iconActive: 'person' },
};

export default function MainTabs({ onLogout }: { onLogout: () => void }) {
  const HealthStack = () => (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HealthHome" component={HealthScreen} />
    </Stack.Navigator>
  );

  const TrainingStack = () => (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="TrainingHome" component={TrainingScreen} />
      <Stack.Screen name="TrainingCreate" component={TrainingCreateScreen} />
      <Stack.Screen name="TrainingPlanDetail" component={TrainingPlanDetailScreen} />
      <Stack.Screen name="TrainingCalendar" component={TrainingCalendarScreen} />
    </Stack.Navigator>
  );

  const DietStack = () => (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="DietHome" component={DietScreen} />
      <Stack.Screen name="DietTrend" component={DietTrendScreen} />
      <Stack.Screen name="FoodLibrary" component={FoodLibraryScreen} />
      <Stack.Screen name="CustomFood" component={CustomFoodScreen} />
    </Stack.Navigator>
  );

  const ProfileStack = () => (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="ProfileHome">
        {() => <ProfileScreen onLogout={onLogout} />}
      </Stack.Screen>
    </Stack.Navigator>
  );

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
      <Tab.Screen name="健康" component={HealthStack} />
      <Tab.Screen name="训练" component={TrainingStack} />
      <Tab.Screen name="饮食" component={DietStack} />
      <Tab.Screen name="AI" component={ChatScreen} />
      <Tab.Screen name="我的" component={ProfileStack} />
    </Tab.Navigator>
  );
}
