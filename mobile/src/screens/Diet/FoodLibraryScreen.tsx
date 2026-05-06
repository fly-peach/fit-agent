import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
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

export default function FoodLibraryScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [keyword, setKeyword] = useState('');
  const [category, setCategory] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const [foods, setFoods] = useState<FoodItem[]>([]);
  const [loading, setLoading] = useState(false);

  const loadCategories = async () => {
    try {
      const data = await dietApi.getFoodCategories();
      setCategories(data);
    } catch {}
  };

  const searchFoods = async (nextKeyword = keyword, nextCategory = category) => {
    setLoading(true);
    try {
      const data = await dietApi.searchFoods(nextKeyword, nextCategory, '');
      setFoods(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
    searchFoods('', '');
  }, []);

  const selectFood = (food: FoodItem) => {
    navigation.navigate('DietHome', { selectedFood: food });
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingTop: insets.top + 8, paddingBottom: 24 }}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="chevron-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>食物库</Text>
        <TouchableOpacity onPress={() => navigation.navigate('CustomFood')}>
          <Ionicons name="add-circle-outline" size={24} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <TextInput
          style={styles.input}
          placeholder="搜索食物"
          value={keyword}
          onChangeText={setKeyword}
          onSubmitEditing={() => searchFoods(keyword, category)}
        />
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 10 }}>
          <TouchableOpacity style={[styles.chip, !category && styles.chipActive]} onPress={() => { setCategory(''); searchFoods(keyword, ''); }}>
            <Text style={[styles.chipText, !category && styles.chipTextActive]}>全部</Text>
          </TouchableOpacity>
          {categories.map(item => (
            <TouchableOpacity
              key={item}
              style={[styles.chip, category === item && styles.chipActive]}
              onPress={() => { setCategory(item); searchFoods(keyword, item); }}
            >
              <Text style={[styles.chipText, category === item && styles.chipTextActive]}>{item}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      <View style={styles.card}>
        {loading ? (
          <ActivityIndicator color={COLORS.primary} />
        ) : foods.map(food => (
          <TouchableOpacity key={food.foodId} style={styles.foodRow} onPress={() => selectFood(food)}>
            <View style={{ flex: 1 }}>
              <Text style={styles.foodName}>{food.name}</Text>
              <Text style={styles.foodMeta}>{food.category} · {food.portionCalories} kcal</Text>
              <Text style={styles.foodMeta}>P {food.protein} / C {food.carbs} / F {food.fat}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={COLORS.textTertiary} />
          </TouchableOpacity>
        ))}
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
  input: {
    backgroundColor: COLORS.background,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  chip: {
    backgroundColor: COLORS.background,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginRight: 8,
  },
  chipActive: { backgroundColor: COLORS.blueBg },
  chipText: { color: COLORS.textSecondary },
  chipTextActive: { color: COLORS.primary, fontWeight: '700' },
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

