import { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useLocalSearchParams, useFocusEffect } from 'expo-router';
import { useCropPlanningStore } from '@/store/crop-planning';
import { COLORS, IRRIGATION_METHOD_LABELS } from '@/utils/constants';
import StatusBadge from '@/components/crop-planning/StatusBadge';
import type { IrrigationSchedule } from '@/types/crop-planning';

export default function IrrigationScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const {
    irrigationSchedules,
    fetchIrrigation,
    generateIrrigation,
    completeIrrigation,
    isLoading,
  } = useCropPlanningStore();

  const [showGenerate, setShowGenerate] = useState(false);
  const [genMethod, setGenMethod] = useState('drip');
  const [genStartDate, setGenStartDate] = useState('');
  const [genEndDate, setGenEndDate] = useState('');
  const [genFrequency, setGenFrequency] = useState('7');
  const [genWaterAmount, setGenWaterAmount] = useState('');

  const [completingId, setCompletingId] = useState<string | null>(null);
  const [compDuration, setCompDuration] = useState('');
  const [compWater, setCompWater] = useState('');
  const [compMoistureBefore, setCompMoistureBefore] = useState('');
  const [compMoistureAfter, setCompMoistureAfter] = useState('');

  useFocusEffect(
    useCallback(() => {
      if (id) fetchIrrigation(id);
    }, [id])
  );

  const totalPlanned = irrigationSchedules.reduce((s, i) => s + (i.waterAmountLiters || 0), 0);
  const totalUsed = irrigationSchedules.reduce((s, i) => s + (i.actualWaterUsedLiters || 0), 0);
  const completed = irrigationSchedules.filter((i) => i.status === 'completed').length;

  const handleGenerate = async () => {
    if (!genStartDate || !genEndDate) {
      Alert.alert('Required', 'Start and end dates are required');
      return;
    }
    try {
      await generateIrrigation(id!, {
        startDate: new Date(genStartDate).toISOString(),
        endDate: new Date(genEndDate).toISOString(),
        method: genMethod,
        frequencyDays: parseInt(genFrequency) || 7,
        waterAmountPerEventLiters: genWaterAmount ? parseFloat(genWaterAmount) : undefined,
      });
      setShowGenerate(false);
      fetchIrrigation(id!);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  };

  const handleComplete = async (scheduleId: string) => {
    try {
      await completeIrrigation(scheduleId, {
        actualDurationMinutes: compDuration ? parseInt(compDuration) : undefined,
        actualWaterUsedLiters: compWater ? parseFloat(compWater) : undefined,
        soilMoistureBefore: compMoistureBefore ? parseFloat(compMoistureBefore) : undefined,
        soilMoistureAfter: compMoistureAfter ? parseFloat(compMoistureAfter) : undefined,
      });
      setCompletingId(null);
      setCompDuration('');
      setCompWater('');
      setCompMoistureBefore('');
      setCompMoistureAfter('');
      fetchIrrigation(id!);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  };

  const renderScheduleCard = ({ item }: { item: IrrigationSchedule }) => (
    <View style={styles.scheduleCard} testID={`cp-irrigation-${item.id}`}>
      <View style={styles.scheduleHeader}>
        <View>
          <Text style={styles.scheduleDate}>
            {new Date(item.scheduledDate).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
          </Text>
          <Text style={styles.scheduleMethod}>
            {IRRIGATION_METHOD_LABELS[item.method] || item.method}
            {item.waterAmountLiters ? ` - ${item.waterAmountLiters}L` : ''}
          </Text>
        </View>
        <StatusBadge status={item.status} type="activity" />
      </View>

      {item.status === 'completed' && item.actualWaterUsedLiters && (
        <View style={styles.completionInfo}>
          <Text style={styles.completionText}>Used: {item.actualWaterUsedLiters}L</Text>
          {item.actualDurationMinutes && <Text style={styles.completionText}>Duration: {item.actualDurationMinutes}min</Text>}
        </View>
      )}

      {item.status === 'scheduled' && completingId !== item.id && (
        <TouchableOpacity
          style={styles.completeBtn}
          onPress={() => setCompletingId(item.id)}
          testID={`cp-irrigation-complete-${item.id}`}
        >
          <Text style={styles.completeBtnText}>Mark Complete</Text>
        </TouchableOpacity>
      )}

      {completingId === item.id && (
        <View style={styles.completeForm}>
          <TextInput style={styles.formInput} value={compDuration} onChangeText={setCompDuration} placeholder="Duration (min)" keyboardType="number-pad" />
          <TextInput style={styles.formInput} value={compWater} onChangeText={setCompWater} placeholder="Water used (L)" keyboardType="decimal-pad" />
          <TextInput style={styles.formInput} value={compMoistureBefore} onChangeText={setCompMoistureBefore} placeholder="Soil moisture before (%)" keyboardType="decimal-pad" />
          <TextInput style={styles.formInput} value={compMoistureAfter} onChangeText={setCompMoistureAfter} placeholder="Soil moisture after (%)" keyboardType="decimal-pad" />
          <View style={styles.completeFormActions}>
            <TouchableOpacity onPress={() => setCompletingId(null)}>
              <Text style={{ color: '#666' }}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.completeFormSubmit}
              onPress={() => handleComplete(item.id)}
            >
              <Text style={{ color: '#fff', fontWeight: '600' }}>Complete</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      testID="cp-irrigation-screen"
    >
      {/* Water Summary */}
      <View style={styles.waterSummary}>
        <View style={styles.waterItem}>
          <Text style={styles.waterLabel}>Planned</Text>
          <Text style={styles.waterValue}>{totalPlanned.toLocaleString()}L</Text>
        </View>
        <View style={styles.waterDivider} />
        <View style={styles.waterItem}>
          <Text style={styles.waterLabel}>Used</Text>
          <Text style={styles.waterValue}>{totalUsed.toLocaleString()}L</Text>
        </View>
        <View style={styles.waterDivider} />
        <View style={styles.waterItem}>
          <Text style={styles.waterLabel}>Done</Text>
          <Text style={styles.waterValue}>{completed}/{irrigationSchedules.length}</Text>
        </View>
      </View>

      {/* Generate Form */}
      {showGenerate && (
        <View style={styles.generateForm}>
          <Text style={styles.generateTitle}>Generate Schedule</Text>
          <View style={styles.methodRow}>
            {['drip', 'sprinkler', 'furrow', 'manual'].map((m) => (
              <TouchableOpacity
                key={m}
                style={[styles.methodChip, genMethod === m && styles.methodChipActive]}
                onPress={() => setGenMethod(m)}
              >
                <Text style={[styles.methodChipText, genMethod === m && { color: '#fff' }]}>
                  {IRRIGATION_METHOD_LABELS[m] || m}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <TextInput style={styles.formInput} value={genStartDate} onChangeText={setGenStartDate} placeholder="Start date (YYYY-MM-DD)" testID="cp-irrigation-gen-start" />
          <TextInput style={styles.formInput} value={genEndDate} onChangeText={setGenEndDate} placeholder="End date (YYYY-MM-DD)" testID="cp-irrigation-gen-end" />
          <TextInput style={styles.formInput} value={genFrequency} onChangeText={setGenFrequency} placeholder="Frequency (days)" keyboardType="number-pad" />
          <TextInput style={styles.formInput} value={genWaterAmount} onChangeText={setGenWaterAmount} placeholder="Water per event (L, optional)" keyboardType="decimal-pad" />
          <View style={styles.generateActions}>
            <TouchableOpacity onPress={() => setShowGenerate(false)}>
              <Text style={{ color: '#666' }}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.generateSubmit} onPress={handleGenerate} testID="cp-irrigation-gen-submit">
              {isLoading ? <ActivityIndicator color="#fff" size="small" /> : <Text style={{ color: '#fff', fontWeight: '600' }}>Generate</Text>}
            </TouchableOpacity>
          </View>
        </View>
      )}

      <FlatList
        data={irrigationSchedules}
        renderItem={renderScheduleCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={() => fetchIrrigation(id!)} colors={[COLORS.primary]} />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>💧</Text>
            <Text style={styles.emptyText}>No irrigation schedule</Text>
            <Text style={styles.emptySubtext}>Generate a schedule to get started</Text>
          </View>
        }
      />

      {!showGenerate && (
        <TouchableOpacity style={styles.fab} onPress={() => setShowGenerate(true)} testID="cp-irrigation-gen-fab">
          <Text style={{ fontSize: 28, color: '#fff' }}>+</Text>
        </TouchableOpacity>
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  waterSummary: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  waterItem: { flex: 1, alignItems: 'center' },
  waterLabel: { fontSize: 12, color: '#666' },
  waterValue: { fontSize: 18, fontWeight: '700', color: COLORS.primary, marginTop: 4 },
  waterDivider: { width: 1, backgroundColor: '#E0E0E0' },
  list: { padding: 16, paddingBottom: 80 },
  scheduleCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  scheduleHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  scheduleDate: { fontSize: 15, fontWeight: '600', color: '#333' },
  scheduleMethod: { fontSize: 12, color: '#666', marginTop: 2 },
  completionInfo: { flexDirection: 'row', gap: 16, marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: '#f0f0f0' },
  completionText: { fontSize: 12, color: '#666' },
  completeBtn: { marginTop: 10, paddingVertical: 8, borderRadius: 8, backgroundColor: COLORS.gray[100], alignItems: 'center' },
  completeBtnText: { fontSize: 13, color: COLORS.primary, fontWeight: '500' },
  completeForm: { marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#f0f0f0' },
  formInput: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 10,
    fontSize: 14,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  completeFormActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 12, marginTop: 4 },
  completeFormSubmit: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8, backgroundColor: COLORS.primary },
  generateForm: { backgroundColor: '#fff', padding: 16, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  generateTitle: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 10 },
  methodRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 10 },
  methodChip: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 14, backgroundColor: COLORS.gray[100] },
  methodChipActive: { backgroundColor: COLORS.primary },
  methodChipText: { fontSize: 13, color: '#333' },
  generateActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 12, marginTop: 4 },
  generateSubmit: { paddingHorizontal: 20, paddingVertical: 10, borderRadius: 8, backgroundColor: COLORS.primary },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 6,
  },
  emptyState: { alignItems: 'center', paddingVertical: 48 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#333' },
  emptySubtext: { fontSize: 13, color: '#666', marginTop: 4 },
});
