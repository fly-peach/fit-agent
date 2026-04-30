import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { authApi } from '../../services/auth';
import { storage } from '../../utils/storage';
import { COLORS, SHADOWS } from '../../constants';

interface Props {
  onLoginSuccess: () => void;
}

export default function LoginScreen({ onLoginSuccess }: Props) {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!email || !password) {
      Alert.alert('提示', '请填写邮箱和密码');
      return;
    }
    if (isRegister && !name) {
      Alert.alert('提示', '请填写用户名');
      return;
    }

    setLoading(true);
    try {
      const result = isRegister
        ? await authApi.register({ name, email, password })
        : await authApi.login({ email, password });

      await storage.setItem('token', result.token);
      await storage.setItem('user', JSON.stringify(result.user));
      onLoginSuccess();
    } catch (err: any) {
      Alert.alert('错误', err.message || (isRegister ? '注册失败' : '登录失败'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <StatusBar />

      {/* Gradient Header */}
      <LinearGradient
        colors={[COLORS.gradientStart, COLORS.gradientEnd]}
        style={styles.header}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.logoCircle}>
          <Ionicons name="fitness" size={40} color={COLORS.white} />
        </View>
        <Text style={styles.title}>FitAgent</Text>
        <Text style={styles.subtitle}>你的智能健身助手</Text>
      </LinearGradient>

      {/* Form Card */}
      <View style={styles.formCard}>
        <Text style={styles.formTitle}>{isRegister ? '创建账号' : '欢迎回来'}</Text>
        <Text style={styles.formSubtitle}>
          {isRegister ? '注册开始你的健身之旅' : '登录继续你的健身计划'}
        </Text>

        <View style={styles.inputs}>
          {isRegister && (
            <View style={styles.inputWrap}>
              <Ionicons name="person-outline" size={20} color={COLORS.textTertiary} />
              <TextInput
                style={styles.input}
                placeholder="用户名"
                value={name}
                onChangeText={setName}
                placeholderTextColor={COLORS.textTertiary}
              />
            </View>
          )}
          <View style={styles.inputWrap}>
            <Ionicons name="mail-outline" size={20} color={COLORS.textTertiary} />
            <TextInput
              style={styles.input}
              placeholder="邮箱"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              placeholderTextColor={COLORS.textTertiary}
            />
          </View>
          <View style={styles.inputWrap}>
            <Ionicons name="lock-closed-outline" size={20} color={COLORS.textTertiary} />
            <TextInput
              style={styles.input}
              placeholder="密码"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              placeholderTextColor={COLORS.textTertiary}
            />
          </View>
        </View>

        <TouchableOpacity
          style={[styles.btn, loading && styles.btnDisabled]}
          onPress={handleSubmit}
          disabled={loading}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={[COLORS.gradientStart, COLORS.gradientEnd]}
            style={styles.btnGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          >
            <Text style={styles.btnText}>
              {loading ? '请稍候...' : isRegister ? '注册' : '登录'}
            </Text>
          </LinearGradient>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.switchBtn}
          onPress={() => setIsRegister(!isRegister)}
        >
          <Text style={styles.switchText}>
            {isRegister ? '已有账号？' : '没有账号？'}
            <Text style={styles.switchLink}>
              {isRegister ? '去登录' : '去注册'}
            </Text>
          </Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 48,
    alignItems: 'center',
    borderBottomLeftRadius: 32,
    borderBottomRightRadius: 32,
  },
  logoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: COLORS.white,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
  },
  formCard: {
    backgroundColor: COLORS.white,
    marginHorizontal: 20,
    marginTop: -24,
    borderRadius: 20,
    paddingHorizontal: 24,
    paddingVertical: 28,
    ...SHADOWS.card,
  },
  formTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 4,
  },
  formSubtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 24,
  },
  inputs: {
    gap: 12,
  },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 52,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 14,
    paddingHorizontal: 16,
    gap: 10,
    backgroundColor: '#FAFBFF',
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
  btn: {
    marginTop: 24,
    borderRadius: 14,
    overflow: 'hidden',
  },
  btnDisabled: {
    opacity: 0.6,
  },
  btnGradient: {
    height: 52,
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnText: {
    color: COLORS.white,
    fontSize: 17,
    fontWeight: '700',
  },
  switchBtn: {
    alignItems: 'center',
    marginTop: 16,
    paddingVertical: 8,
  },
  switchText: {
    color: COLORS.textSecondary,
    fontSize: 14,
  },
  switchLink: {
    color: COLORS.primary,
    fontWeight: '600',
  },
});
