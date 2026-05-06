import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { COLORS, SHADOWS } from '../../constants';
import { dietApi } from '../../services/diet';
import type { FoodItem } from '../../types';

export default function CustomFoodScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [customFoods, setCustomFoods] = useState<FoodItem[]>([]);
  const [form, setForm] = useState({
    name: '',
    category: '',
    portionCalories: '',
    caloriesPer100g: '',
    protein: '',
    carbs: '',
    fat: '',
  });

  const loadCustomFoods = useCallback(async () => {
    try {
      const foods = await dietApi.searchFoods('', '', '');
      setCustomFoods(foods.filter(item => item.source === 'custom'));
    } catch {}
  }, []);

  useEffect(() => {
    loadCustomFoods();
  }, [loadCustomFoods]);

  const handleCreate = async () => {
    if (!form.name.trim() || !form.category.trim()) {
      Alert.alert('提示', '请填写名称和分类');
      return;
    }
    try {
      await dietApi.addCustomFood({
        name: form.name.trim(),
        category: form.category.trim(),
        portionCalories: parseInt(form.portionCalories, 10) || 0,
        caloriesPer100g: parseInt(form.caloriesPer100g, 10) || 0,
        protein: parseInt(form.protein, 10) || 0,
        carbs: parseInt(form.carbs, 10) || 0,
        fat: parseInt(form.fat, 10) || 0,
      });
      setForm({
        name: '',
        category: '',
        portionCalories: '',
        caloriesPer100g: '',
        protein: '',
        carbs: '',
        fat: '',
      });
      loadCustomFoods();
    } catch (e: any) {
      Alert.alert('错误', e.message || '添加失败');
    }
  };

  const handleDelete = async (foodId: number) => {
    try {
      await dietApi.deleteCustomFood(foodId);
      loadCustomFoods();
    } catch (e: any) {
      Alert.alert('错误', e.message || '删除失败');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingTop: insets.top + 8, paddingBottom: 24 }}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="chevron-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>自定义食物</Text>
        <View style={{ width: 24 }} />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>新增食物</Text>
        {[
          ['name', '名称'],
          ['category', '分类'],
          ['portionCalories', '份量热量'],
          ['caloriesPer100g', '每100g热量'],
          ['protein', '蛋白质'],
          ['carbs', '碳水'],
          ['fat', '脂肪'],
        ].map(([key, label]) => (
          <View key={key} style={{ marginTop: 10 }}>
            <Text style={styles.label}>{label}</Text>
            <TextInput
              style={styles.input}
              value={(form as any)[key]}
              onChangeText={value => setForm(prev => ({ ...prev, [key]: value }))}
              keyboardType={['portionCalories', 'caloriesPer100g', 'protein', 'carbs', 'fat'].includes(key) ? 'numeric' : 'default'}
            />
          </View>
        ))}
        <TouchableOpacity style={styles.saveBtn} onPress={handleCreate}>
          <Text style={styles.saveText}>保存食物</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>我的食物</Text>
        {customFoods.length ? customFoods.map(item => (
          <View key={item.foodId} style={styles.foodRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.foodName}>{item.name}</Text>
              <Text style={styles.foodMeta}>{item.category} · {item.portionCalories} kcal</Text>
            </View>
            <TouchableOpacity onPress={() => handleDelete(item.foodId)}>
              <Ionicons name="trash-outline" size={18} color={COLORS.danger} />
            </TouchableOpacity>
          </View>
        )) : (
          <Text style={styles.foodMeta}>暂无自定义食物</Text>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  headerTitle: { fontSize: 20, fontWeight: '700', color: COLORS.text },
  card: {
    marginHorizontal: 16,
    marginTop: 12,
    padding: 16,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    ...SHADOWS.card,
  },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: COLORS.text, marginBottom: 8 },
  label: { color: COLORS.textSecondary, marginBottom: 6 },
  input: {
    backgroundColor: COLORS.background,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  saveBtn: {
    marginTop: 16,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingVertical: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveText: { color: COLORS.white, fontWeight: '700' },
  foodRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    borderBottomColor: COLORS.divider,
    borderBottomWidth: 1,
  },
  foodName: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  foodMeta: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
});

