import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { storage } from './src/utils/storage';
import LoginScreen from './src/screens/Auth/LoginScreen';
import MainTabs from './src/navigation';
import { COLORS, SHADOWS } from './src/constants';

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    (async () => {
      const token = await storage.getItem('token');
      setIsLoggedIn(!!token);
      setChecking(false);
    })();
  }, []);

  return (
    <SafeAreaProvider>
    <NavigationContainer>
      <StatusBar style="dark" />
      {checking ? (
        <View style={styles.loading}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : isLoggedIn ? (
        <MainTabs onLogout={() => setIsLoggedIn(false)} />
      ) : (
        <LoginScreen onLoginSuccess={() => setIsLoggedIn(true)} />
      )}
    </NavigationContainer>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.background },
});
