import { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity,
  ActivityIndicator, Alert,
} from 'react-native';
import { router } from 'expo-router';
import { useTaskStore } from '@/store/task';
import { useAuthStore } from '@/store/auth';
import { TASK_CATEGORY_LABELS } from '@/utils/constants';

const categories = Object.entries(TASK_CATEGORY_LABELS);

// Quick date helpers
const addDays = (days: number): Date => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  d.setHours(12, 0, 0, 0);
  return d;
};

const DATE_PRESETS = [
  { label: 'Today', days: 0 },
  { label: 'Tomorrow', days: 1 },
  { label: 'In 3 days', days: 3 },
  { label: 'In 1 week', days: 7 },
  { label: 'In 2 weeks', days: 14 },
  { label: 'In 1 month', days: 30 },
];

export default function CreateTaskScreen() {
  const user = useAuthStore((s) => s.user);
  const { createTask, isLoading } = useTaskStore();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('general');
  const [priority, setPriority] = useState(5);
  const [dueDate, setDueDate] = useState<Date | null>(null);
  const [notes, setNotes] = useState('');

  const handleCreate = async () => {
    if (!title.trim()) {
      Alert.alert('Validation', 'Please enter a task title.');
      return;
    }
    if (!user?.farmerId) {
      Alert.alert('Error', 'No farmer profile found.');
      return;
    }
    try {
      await createTask({
        farmerId: user.farmerId,
        title: title.trim(),
        description: description.trim() || undefined,
        category,
        priority,
        dueDate: dueDate ? dueDate.toISOString() : undefined,
        notes: notes.trim() || undefined,
      });
      router.back();
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Failed to create task');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.heading}>Create Task</Text>

      {/* Title */}
      <Text style={styles.label}>Title *</Text>
      <TextInput
        style={styles.input}
        placeholder="What needs to be done?"
        value={title}
        onChangeText={setTitle}
        maxLength={300}
      />

      {/* Description */}
      <Text style={styles.label}>Description</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        placeholder="Add more details..."
        value={description}
        onChangeText={setDescription}
        multiline
        numberOfLines={3}
      />

      {/* Category */}
      <Text style={styles.label}>Category</Text>
      <View style={styles.chipContainer}>
        {categories.map(([key, label]) => (
          <TouchableOpacity
            key={key}
            style={[styles.chip, category === key && styles.chipActive]}
            onPress={() => setCategory(key)}
          >
            <Text style={[styles.chipText, category === key && styles.chipTextActive]}>{label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Priority */}
      <Text style={styles.label}>Priority: {priority}/10</Text>
      <View style={styles.priorityRow}>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((p) => (
          <TouchableOpacity
            key={p}
            style={[
              styles.priorityBtn,
              priority === p && styles.priorityBtnActive,
              priority === p && p <= 3 && styles.priorityHighActive,
              priority === p && p >= 4 && p <= 6 && styles.priorityMedActive,
              priority === p && p >= 7 && styles.priorityLowActive,
            ]}
            onPress={() => setPriority(p)}
          >
            <Text style={[styles.priorityText, priority === p && styles.priorityTextActive]}>{p}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Due Date */}
      <Text style={styles.label}>Due Date</Text>
      <View style={styles.chipContainer}>
        {DATE_PRESETS.map((preset) => {
          const presetDate = addDays(preset.days);
          const isSelected = dueDate && dueDate.toDateString() === presetDate.toDateString();
          return (
            <TouchableOpacity
              key={preset.days}
              style={[styles.chip, isSelected && styles.chipActive]}
              onPress={() => setDueDate(isSelected ? null : presetDate)}
            >
              <Text style={[styles.chipText, isSelected && styles.chipTextActive]}>{preset.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
      {dueDate && (
        <Text style={styles.dateDisplay}>
          Due: {dueDate.toLocaleDateString()}
          {'  '}
          <Text style={styles.clearDate} onPress={() => setDueDate(null)}>Clear</Text>
        </Text>
      )}

      {/* Notes */}
      <Text style={styles.label}>Notes</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        placeholder="Any additional notes..."
        value={notes}
        onChangeText={setNotes}
        multiline
        numberOfLines={2}
      />

      {/* Submit */}
      <TouchableOpacity style={styles.submitBtn} onPress={handleCreate} disabled={isLoading}>
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.submitText}>Create Task</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  content: { padding: 16, paddingBottom: 40 },
  heading: { fontSize: 22, fontWeight: '700', color: '#333', marginBottom: 20 },
  label: { fontSize: 14, fontWeight: '600', color: '#555', marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: '#fff', borderRadius: 10, padding: 14, fontSize: 15, borderWidth: 1, borderColor: '#ddd' },
  textArea: { minHeight: 70, textAlignVertical: 'top' },
  chipContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, backgroundColor: '#fff', borderWidth: 1, borderColor: '#ddd' },
  chipActive: { backgroundColor: '#1B5E20', borderColor: '#1B5E20' },
  chipText: { fontSize: 13, color: '#555' },
  chipTextActive: { color: '#fff', fontWeight: '600' },
  priorityRow: { flexDirection: 'row', gap: 4, justifyContent: 'space-between' },
  priorityBtn: { width: 30, height: 30, borderRadius: 15, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f0f0f0' },
  priorityBtnActive: { borderWidth: 2 },
  priorityHighActive: { borderColor: '#D32F2F', backgroundColor: '#FFEBEE' },
  priorityMedActive: { borderColor: '#FF9800', backgroundColor: '#FFF3E0' },
  priorityLowActive: { borderColor: '#4CAF50', backgroundColor: '#E8F5E9' },
  priorityText: { fontSize: 12, color: '#666', fontWeight: '500' },
  priorityTextActive: { fontWeight: '700' },
  dateDisplay: { fontSize: 14, color: '#333', marginTop: 8 },
  clearDate: { color: '#D32F2F', fontSize: 13 },
  submitBtn: { backgroundColor: '#1B5E20', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 24 },
  submitText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
