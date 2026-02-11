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
import { COLORS, INPUT_CATEGORY_LABELS, PROCUREMENT_STATUS_COLORS } from '@/utils/constants';
import StatusBadge from '@/components/crop-planning/StatusBadge';
import type { InputRequirement } from '@/types/crop-planning';

const CATEGORY_FILTERS = ['all', 'seed', 'fertilizer', 'pesticide', 'herbicide', 'fungicide', 'other'];

export default function InputsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { inputs, fetchInputs, createInput, updateInput, isLoading } = useCropPlanningStore();
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showAddForm, setShowAddForm] = useState(false);

  // Add form state
  const [newName, setNewName] = useState('');
  const [newCategory, setNewCategory] = useState('seed');
  const [newQuantity, setNewQuantity] = useState('');
  const [newUnit, setNewUnit] = useState('kg');
  const [newUnitPrice, setNewUnitPrice] = useState('');

  useFocusEffect(
    useCallback(() => {
      if (id) fetchInputs(id);
    }, [id])
  );

  const filtered = categoryFilter === 'all'
    ? inputs
    : inputs.filter((i) => i.category === categoryFilter);

  const totalEstimated = inputs.reduce((sum, i) => sum + (i.totalEstimatedCost || 0), 0);
  const totalActual = inputs.reduce((sum, i) => sum + (i.actualCost || 0), 0);

  const handleAddInput = async () => {
    if (!newName.trim() || !newQuantity.trim()) {
      Alert.alert('Required', 'Name and quantity are required');
      return;
    }
    try {
      await createInput(id!, {
        name: newName.trim(),
        category: newCategory,
        quantity_required: parseFloat(newQuantity),
        unit: newUnit,
        unit_price: newUnitPrice ? parseFloat(newUnitPrice) : undefined,
      });
      setShowAddForm(false);
      setNewName('');
      setNewQuantity('');
      setNewUnitPrice('');
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  };

  const handleUpdateStatus = async (inputItem: InputRequirement, newStatus: string) => {
    try {
      await updateInput(inputItem.id, { procurement_status: newStatus });
      fetchInputs(id!);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  };

  const renderInputCard = ({ item }: { item: InputRequirement }) => (
    <View style={styles.inputCard} testID={`cp-input-${item.id}`}>
      <View style={styles.inputHeader}>
        <View style={styles.inputHeaderLeft}>
          <Text style={styles.inputName}>{item.name}</Text>
          <Text style={styles.inputCategory}>{INPUT_CATEGORY_LABELS[item.category] || item.category}</Text>
        </View>
        <StatusBadge status={item.procurementStatus} type="procurement" />
      </View>
      <View style={styles.inputDetails}>
        <Text style={styles.inputDetail}>Qty: {item.quantityRequired} {item.unit}</Text>
        {item.unitPrice && <Text style={styles.inputDetail}>Price: KES {item.unitPrice}/{item.unit}</Text>}
        {item.totalEstimatedCost && <Text style={styles.inputDetail}>Est: KES {item.totalEstimatedCost.toLocaleString()}</Text>}
        {item.brand && <Text style={styles.inputDetail}>Brand: {item.brand}</Text>}
      </View>
      {/* Status progression buttons */}
      <View style={styles.statusRow}>
        {['planned', 'ordered', 'received', 'applied'].map((s) => (
          <TouchableOpacity
            key={s}
            style={[
              styles.statusChip,
              item.procurementStatus === s && { backgroundColor: PROCUREMENT_STATUS_COLORS[s] },
            ]}
            onPress={() => handleUpdateStatus(item, s)}
            testID={`cp-input-${item.id}-status-${s}`}
          >
            <Text
              style={[
                styles.statusChipText,
                item.procurementStatus === s && { color: '#fff' },
              ]}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      testID="cp-inputs-screen"
    >
      {/* Cost Summary */}
      <View style={styles.costSummary}>
        <View style={styles.costItem}>
          <Text style={styles.costLabel}>Estimated</Text>
          <Text style={styles.costValue}>KES {totalEstimated.toLocaleString()}</Text>
        </View>
        <View style={styles.costDivider} />
        <View style={styles.costItem}>
          <Text style={styles.costLabel}>Actual</Text>
          <Text style={styles.costValue}>KES {totalActual.toLocaleString()}</Text>
        </View>
      </View>

      {/* Filter chips */}
      <View style={styles.filterRow}>
        {CATEGORY_FILTERS.map((c) => (
          <TouchableOpacity
            key={c}
            style={[styles.filterChip, categoryFilter === c && styles.filterChipActive]}
            onPress={() => setCategoryFilter(c)}
          >
            <Text style={[styles.filterChipText, categoryFilter === c && styles.filterChipTextActive]}>
              {c === 'all' ? 'All' : INPUT_CATEGORY_LABELS[c] || c}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Add Input Form */}
      {showAddForm && (
        <View style={styles.addForm}>
          <Text style={styles.addFormTitle}>Add Input</Text>
          <TextInput style={styles.formInput} value={newName} onChangeText={setNewName} placeholder="Input name" testID="cp-input-add-name" />
          <View style={styles.formRow}>
            <TextInput style={[styles.formInput, { flex: 1 }]} value={newQuantity} onChangeText={setNewQuantity} placeholder="Quantity" keyboardType="decimal-pad" testID="cp-input-add-qty" />
            <TextInput style={[styles.formInput, { width: 80, marginLeft: 8 }]} value={newUnit} onChangeText={setNewUnit} placeholder="Unit" testID="cp-input-add-unit" />
          </View>
          <TextInput style={styles.formInput} value={newUnitPrice} onChangeText={setNewUnitPrice} placeholder="Unit price (optional)" keyboardType="decimal-pad" testID="cp-input-add-price" />
          <View style={styles.formRow}>
            {['seed', 'fertilizer', 'pesticide', 'other'].map((c) => (
              <TouchableOpacity
                key={c}
                style={[styles.formChip, newCategory === c && styles.formChipActive]}
                onPress={() => setNewCategory(c)}
              >
                <Text style={[styles.formChipText, newCategory === c && { color: '#fff' }]}>
                  {INPUT_CATEGORY_LABELS[c] || c}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <View style={styles.formActions}>
            <TouchableOpacity style={styles.formCancel} onPress={() => setShowAddForm(false)}>
              <Text style={{ color: '#666' }}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.formSubmit} onPress={handleAddInput} testID="cp-input-add-submit">
              <Text style={{ color: '#fff', fontWeight: '600' }}>Add</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <FlatList
        data={filtered}
        renderItem={renderInputCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={() => fetchInputs(id!)} colors={[COLORS.primary]} />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>📦</Text>
            <Text style={styles.emptyText}>No inputs yet</Text>
          </View>
        }
      />

      {!showAddForm && (
        <TouchableOpacity style={styles.fab} onPress={() => setShowAddForm(true)} testID="cp-inputs-add-fab">
          <Text style={{ fontSize: 28, color: '#fff' }}>+</Text>
        </TouchableOpacity>
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  costSummary: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  costItem: { flex: 1, alignItems: 'center' },
  costLabel: { fontSize: 12, color: '#666' },
  costValue: { fontSize: 18, fontWeight: '700', color: COLORS.primary, marginTop: 4 },
  costDivider: { width: 1, backgroundColor: '#E0E0E0' },
  filterRow: { flexDirection: 'row', flexWrap: 'wrap', padding: 10, gap: 6, backgroundColor: '#fff' },
  filterChip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, backgroundColor: COLORS.gray[100] },
  filterChipActive: { backgroundColor: COLORS.primary },
  filterChipText: { fontSize: 12, color: COLORS.gray[600] },
  filterChipTextActive: { color: '#fff' },
  list: { padding: 16, paddingBottom: 80 },
  inputCard: {
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
  inputHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  inputHeaderLeft: { flex: 1 },
  inputName: { fontSize: 15, fontWeight: '600', color: '#333' },
  inputCategory: { fontSize: 12, color: '#666', marginTop: 2 },
  inputDetails: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 10 },
  inputDetail: { fontSize: 12, color: '#666' },
  statusRow: { flexDirection: 'row', gap: 6 },
  statusChip: {
    flex: 1,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: COLORS.gray[100],
    alignItems: 'center',
  },
  statusChipText: { fontSize: 11, fontWeight: '500', color: '#666' },
  addForm: { backgroundColor: '#fff', padding: 16, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  addFormTitle: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 10 },
  formInput: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  formRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 8 },
  formChip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12, backgroundColor: COLORS.gray[100] },
  formChipActive: { backgroundColor: COLORS.primary },
  formChipText: { fontSize: 12, color: '#333' },
  formActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 10, marginTop: 4 },
  formCancel: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8 },
  formSubmit: { paddingHorizontal: 20, paddingVertical: 10, borderRadius: 8, backgroundColor: COLORS.primary },
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
});
