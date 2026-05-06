import React, { useMemo, useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { COLORS, SHADOWS, TRAINING_TYPE_LABELS } from '../../constants';
import { trainingApi } from '../../services/training';
import { exerciseApi } from '../../services/exercise';
import type { ExerciseItem, PlanExerciseInput, TrainingPlan } from '../../types';

const TYPE_OPTIONS = ['strength', 'cardio', 'flexibility'];

export default function TrainingCreateScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [planName, setPlanName] = useState('');
  const [planType, setPlanType] = useState('strength');
  const [duration, setDuration] = useState('30');
  const [note, setNote] = useState('');
  const [isRecurring, setIsRecurring] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<ExerciseItem[]>([]);
  const [selectedExercises, setSelectedExercises] = useState<PlanExerciseInput[]>([]);
  const [saving, setSaving] = useState(false);

  const dateStr = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const searchExercises = async () => {
    setSearching(true);
    try {
      const list = await exerciseApi.listExercises({ keyword, limit: 20 });
      setResults(list);
    } catch (e: any) {
      Alert.alert('错误', e.message || '动作搜索失败');
    } finally {
      setSearching(false);
    }
  };

  const addExercise = (exercise: ExerciseItem) => {
    if (selectedExercises.some(item => item.exerciseId === exercise.exerciseId)) {
      return;
    }
    setSelectedExercises(prev => [
      ...prev,
      { exerciseId: exercise.exerciseId, sets: 3, reps: 10 },
    ]);
  };

  const addCustomExercise = () => {
    if (!keyword.trim()) {
      Alert.alert('提示', '请输入自定义动作名称');
      return;
    }
    setSelectedExercises(prev => [
      ...prev,
      { customName: keyword.trim(), sets: 3, reps: 10 },
    ]);
    setKeyword('');
  };

  const updateExercise = (index: number, field: 'sets' | 'reps', value: string) => {
    setSelectedExercises(prev => prev.map((item, idx) => (
      idx === index ? { ...item, [field]: parseInt(value, 10) || 0 } : item
    )));
  };

  const removeExercise = (index: number) => {
    setSelectedExercises(prev => prev.filter((_, idx) => idx !== index));
  };

  const handleSave = async () => {
    if (!planName.trim()) {
      Alert.alert('提示', '请输入训练名称');
      return;
    }
    setSaving(true);
    try {
      const payload: TrainingPlan = {
        planName: planName.trim(),
        planType,
        estimatedDuration: parseInt(duration, 10) || 30,
        scheduledDate: dateStr,
        note: note.trim() || undefined,
        isRecurring,
        exercises: selectedExercises.length > 0 ? selectedExercises : undefined,
      };
      await trainingApi.createPlan(payload);
      Alert.alert('成功', '训练计划已创建');
      navigation.goBack();
    } catch (e: any) {
      Alert.alert('错误', e.message || '创建失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingTop: insets.top + 8, paddingBottom: 24 }}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="chevron-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>创建训练计划</Text>
        <TouchableOpacity onPress={handleSave} disabled={saving}>
          <Text style={[styles.saveText, saving && { opacity: 0.5 }]}>保存</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>训练类型</Text>
        <View style={styles.chipRow}>
          {TYPE_OPTIONS.map(type => (
            <TouchableOpacity
              key={type}
              style={[styles.chip, planType === type && styles.chipActive]}
              onPress={() => setPlanType(type)}
            >
              <Text style={[styles.chipText, planType === type && styles.chipActiveText]}>
                {TRAINING_TYPE_LABELS[type] || type}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>训练名称</Text>
        <TextInput style={styles.input} value={planName} onChangeText={setPlanName} placeholder="例如：上肢力量训练" />

        <Text style={styles.label}>预计时长（分钟）</Text>
        <TextInput style={styles.input} value={duration} onChangeText={setDuration} keyboardType="numeric" placeholder="30" />

        <Text style={styles.label}>备注</Text>
        <TextInput style={[styles.input, styles.textarea]} value={note} onChangeText={setNote} multiline placeholder="可选" />

        <View style={styles.switchRow}>
          <Text style={styles.labelInline}>循环计划</Text>
          <Switch value={isRecurring} onValueChange={setIsRecurring} />
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>动作项编排</Text>
        <View style={styles.searchRow}>
          <TextInput
            style={[styles.input, styles.searchInput]}
            value={keyword}
            onChangeText={setKeyword}
            placeholder="搜索动作或输入自定义动作"
          />
          <TouchableOpacity style={styles.actionBtn} onPress={searchExercises} disabled={searching}>
            <Text style={styles.actionBtnText}>{searching ? '搜索中' : '搜索'}</Text>
          </TouchableOpacity>
        </View>
        <TouchableOpacity style={[styles.actionBtn, { marginTop: 8 }]} onPress={addCustomExercise}>
          <Text style={styles.actionBtnText}>添加自定义动作</Text>
        </TouchableOpacity>

        {results.map(item => (
          <View key={item.exerciseId} style={styles.resultRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.resultTitle}>{item.nameCn}</Text>
              <Text style={styles.resultMeta}>{item.targetMuscle} · {item.difficulty || '未分级'}</Text>
            </View>
            <TouchableOpacity style={styles.addBtn} onPress={() => addExercise(item)}>
              <Ionicons name="add" size={18} color={COLORS.white} />
            </TouchableOpacity>
          </View>
        ))}

        {selectedExercises.length > 0 && (
          <View style={{ marginTop: 12 }}>
            <Text style={styles.sectionTitle}>已选动作</Text>
            {selectedExercises.map((item, index) => (
              <View key={`${item.exerciseId || item.customName}-${index}`} style={styles.selectedRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.resultTitle}>{item.customName || `动作 #${item.exerciseId}`}</Text>
                  <Text style={styles.resultMeta}>可在详情页继续调整</Text>
                </View>
                <TextInput
                  style={styles.smallInput}
                  value={String(item.sets || 0)}
                  onChangeText={value => updateExercise(index, 'sets', value)}
                  keyboardType="numeric"
                  placeholder="组"
                />
                <TextInput
                  style={styles.smallInput}
                  value={String(item.reps || 0)}
                  onChangeText={value => updateExercise(index, 'reps', value)}
                  keyboardType="numeric"
                  placeholder="次"
                />
                <TouchableOpacity onPress={() => removeExercise(index)}>
                  <Ionicons name="trash-outline" size={18} color={COLORS.danger} />
                </TouchableOpacity>
              </View>
            ))}
          </View>
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
  saveText: { fontSize: 16, fontWeight: '600', color: COLORS.primary },
  card: {
    marginHorizontal: 16,
    marginTop: 12,
    padding: 16,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    ...SHADOWS.card,
  },
  label: { fontSize: 14, fontWeight: '600', color: COLORS.text, marginBottom: 8, marginTop: 8 },
  labelInline: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  input: {
    backgroundColor: COLORS.background,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: COLORS.text,
  },
  textarea: { minHeight: 88, textAlignVertical: 'top' },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 },
  chipRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: COLORS.background,
    borderRadius: 999,
  },
  chipActive: { backgroundColor: COLORS.blueBg },
  chipText: { color: COLORS.textSecondary },
  chipActiveText: { color: COLORS.primary, fontWeight: '700' },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: COLORS.text, marginBottom: 10 },
  searchRow: { flexDirection: 'row', gap: 8 },
  searchInput: { flex: 1 },
  actionBtn: {
    paddingHorizontal: 14,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: 12,
  },
  actionBtnText: { color: COLORS.white, fontWeight: '600' },
  resultRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    borderBottomColor: COLORS.divider,
    borderBottomWidth: 1,
  },
  resultTitle: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  resultMeta: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  addBtn: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  selectedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 10,
    borderBottomColor: COLORS.divider,
    borderBottomWidth: 1,
  },
  smallInput: {
    width: 44,
    backgroundColor: COLORS.background,
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 8,
    textAlign: 'center',
  },
});

