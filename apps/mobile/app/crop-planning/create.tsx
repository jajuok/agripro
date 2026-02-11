import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Switch,
} from 'react-native';
import { router } from 'expo-router';
import { useCropPlanningStore } from '@/store/crop-planning';
import { useAuthStore } from '@/store/auth';
import { useFarmStore } from '@/store/farm';
import { COLORS, SEASONS, SEASON_LABELS } from '@/utils/constants';
import { StepIndicatorCompact } from '@/components/StepIndicator';

const steps = [
  { key: 'farm', label: 'Farm & Crop' },
  { key: 'details', label: 'Details' },
  { key: 'review', label: 'Review' },
];

export default function CreatePlanScreen() {
  const user = useAuthStore((s) => s.user);
  const { farms, fetchFarms } = useFarmStore();
  const { updateCreateDraft, createPlan, isLoading } = useCropPlanningStore();

  const [currentStep, setCurrentStep] = useState('farm');
  const [farmId, setFarmId] = useState('');
  const [farmName, setFarmName] = useState('');
  const [cropName, setCropName] = useState('');
  const [variety, setVariety] = useState('');
  const [season, setSeason] = useState('long_rains');
  const [plantingDate, setPlantingDate] = useState('');
  const [harvestDate, setHarvestDate] = useState('');
  const [acreage, setAcreage] = useState('');
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [notes, setNotes] = useState('');
  const [generateActivities, setGenerateActivities] = useState(true);

  useEffect(() => {
    if (user?.farmerId) fetchFarms(user.farmerId);
  }, [user?.farmerId]);

  const goNext = () => {
    if (currentStep === 'farm') {
      if (!farmId) return Alert.alert('Required', 'Please select a farm');
      if (!cropName.trim()) return Alert.alert('Required', 'Please enter a crop name');
      setCurrentStep('details');
    } else if (currentStep === 'details') {
      if (!plantingDate.trim()) return Alert.alert('Required', 'Please enter a planting date');
      if (!acreage.trim()) return Alert.alert('Required', 'Please enter acreage');
      setCurrentStep('review');
    }
  };

  const goBack = () => {
    if (currentStep === 'details') setCurrentStep('farm');
    else if (currentStep === 'review') setCurrentStep('details');
    else router.back();
  };

  const handleCreate = async () => {
    try {
      const planName = `${cropName} - ${SEASON_LABELS[season]} ${year}`;
      updateCreateDraft({
        farmerId: user!.farmerId!,
        farmId,
        name: planName,
        cropName: cropName.trim(),
        variety: variety.trim() || undefined,
        season: season as any,
        year: parseInt(year),
        plannedPlantingDate: new Date(plantingDate).toISOString(),
        plannedAcreage: parseFloat(acreage),
        expectedHarvestDate: harvestDate ? new Date(harvestDate).toISOString() : undefined,
        notes: notes.trim() || undefined,
        generateActivities,
      });
      const plan = await createPlan();
      router.replace(`/crop-planning/${plan.id}`);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to create plan');
    }
  };

  const renderStep1 = () => (
    <View>
      <Text style={styles.label}>Select Farm *</Text>
      <View style={styles.chipRow}>
        {farms.map((f) => (
          <TouchableOpacity
            key={f.id}
            style={[styles.chip, farmId === f.id && styles.chipActive]}
            onPress={() => { setFarmId(f.id); setFarmName(f.name); }}
            testID={`cp-create-farm-${f.id}`}
          >
            <Text style={[styles.chipText, farmId === f.id && styles.chipTextActive]}>{f.name}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Crop Name *</Text>
      <TextInput
        style={styles.input}
        value={cropName}
        onChangeText={setCropName}
        placeholder="e.g. Maize, Tea, Coffee"
        testID="cp-create-crop-name"
      />

      <Text style={styles.label}>Variety</Text>
      <TextInput
        style={styles.input}
        value={variety}
        onChangeText={setVariety}
        placeholder="e.g. H614D, Purple Gold"
        testID="cp-create-variety"
      />

      <Text style={styles.label}>Season *</Text>
      <View style={styles.chipRow}>
        {Object.entries(SEASONS).map(([key, val]) => (
          <TouchableOpacity
            key={key}
            style={[styles.chip, season === val && styles.chipActive]}
            onPress={() => setSeason(val)}
            testID={`cp-create-season-${val}`}
          >
            <Text style={[styles.chipText, season === val && styles.chipTextActive]}>
              {SEASON_LABELS[val]}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const renderStep2 = () => (
    <View>
      <Text style={styles.label}>Planting Date * (YYYY-MM-DD)</Text>
      <TextInput
        style={styles.input}
        value={plantingDate}
        onChangeText={setPlantingDate}
        placeholder="2025-03-15"
        testID="cp-create-planting-date"
      />

      <Text style={styles.label}>Expected Harvest Date (YYYY-MM-DD)</Text>
      <TextInput
        style={styles.input}
        value={harvestDate}
        onChangeText={setHarvestDate}
        placeholder="2025-09-15"
        testID="cp-create-harvest-date"
      />

      <Text style={styles.label}>Acreage *</Text>
      <TextInput
        style={styles.input}
        value={acreage}
        onChangeText={setAcreage}
        placeholder="e.g. 2.5"
        keyboardType="decimal-pad"
        testID="cp-create-acreage"
      />

      <Text style={styles.label}>Year</Text>
      <TextInput
        style={styles.input}
        value={year}
        onChangeText={setYear}
        keyboardType="number-pad"
        testID="cp-create-year"
      />

      <Text style={styles.label}>Notes</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        value={notes}
        onChangeText={setNotes}
        placeholder="Optional notes..."
        multiline
        numberOfLines={3}
        testID="cp-create-notes"
      />
    </View>
  );

  const renderStep3 = () => (
    <View>
      <View style={styles.reviewCard}>
        <Text style={styles.reviewTitle}>Plan Summary</Text>
        <View style={styles.reviewRow}>
          <Text style={styles.reviewLabel}>Farm</Text>
          <Text style={styles.reviewValue}>{farmName}</Text>
        </View>
        <View style={styles.reviewRow}>
          <Text style={styles.reviewLabel}>Crop</Text>
          <Text style={styles.reviewValue}>{cropName}{variety ? ` (${variety})` : ''}</Text>
        </View>
        <View style={styles.reviewRow}>
          <Text style={styles.reviewLabel}>Season</Text>
          <Text style={styles.reviewValue}>{SEASON_LABELS[season]} {year}</Text>
        </View>
        <View style={styles.reviewRow}>
          <Text style={styles.reviewLabel}>Planting</Text>
          <Text style={styles.reviewValue}>{plantingDate}</Text>
        </View>
        {harvestDate ? (
          <View style={styles.reviewRow}>
            <Text style={styles.reviewLabel}>Harvest</Text>
            <Text style={styles.reviewValue}>{harvestDate}</Text>
          </View>
        ) : null}
        <View style={styles.reviewRow}>
          <Text style={styles.reviewLabel}>Acreage</Text>
          <Text style={styles.reviewValue}>{acreage} acres</Text>
        </View>
        {notes ? (
          <View style={styles.reviewRow}>
            <Text style={styles.reviewLabel}>Notes</Text>
            <Text style={styles.reviewValue}>{notes}</Text>
          </View>
        ) : null}
      </View>

      <View style={styles.toggleRow}>
        <View style={styles.toggleInfo}>
          <Text style={styles.toggleLabel}>Generate Activities</Text>
          <Text style={styles.toggleDesc}>Auto-create tasks from crop template</Text>
        </View>
        <Switch
          value={generateActivities}
          onValueChange={setGenerateActivities}
          trackColor={{ true: COLORS.primaryLight }}
          thumbColor={generateActivities ? COLORS.primary : '#ccc'}
          testID="cp-create-gen-activities"
        />
      </View>
    </View>
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      testID="cp-create-screen"
    >
      <StepIndicatorCompact steps={steps} currentStep={currentStep} />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {currentStep === 'farm' && renderStep1()}
        {currentStep === 'details' && renderStep2()}
        {currentStep === 'review' && renderStep3()}
      </ScrollView>
      <View style={styles.footer}>
        <TouchableOpacity style={styles.backButton} onPress={goBack} testID="cp-create-back">
          <Text style={styles.backButtonText}>
            {currentStep === 'farm' ? 'Cancel' : 'Back'}
          </Text>
        </TouchableOpacity>
        {currentStep === 'review' ? (
          <TouchableOpacity
            style={[styles.nextButton, isLoading && { opacity: 0.6 }]}
            onPress={handleCreate}
            disabled={isLoading}
            testID="cp-create-submit"
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={styles.nextButtonText}>Create Plan</Text>
            )}
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.nextButton} onPress={goNext} testID="cp-create-next">
            <Text style={styles.nextButtonText}>Next</Text>
          </TouchableOpacity>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  content: { padding: 16, paddingBottom: 100 },
  label: { fontSize: 14, fontWeight: '600', color: '#333', marginTop: 16, marginBottom: 6 },
  input: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  textArea: { minHeight: 80, textAlignVertical: 'top' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  chipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  chipText: { fontSize: 14, color: '#333' },
  chipTextActive: { color: '#fff', fontWeight: '600' },
  reviewCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
  },
  reviewTitle: { fontSize: 16, fontWeight: '700', color: '#333', marginBottom: 12 },
  reviewRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  reviewLabel: { fontSize: 14, color: '#666' },
  reviewValue: { fontSize: 14, fontWeight: '500', color: '#333', maxWidth: '60%', textAlign: 'right' },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
  },
  toggleInfo: { flex: 1 },
  toggleLabel: { fontSize: 14, fontWeight: '600', color: '#333' },
  toggleDesc: { fontSize: 12, color: '#666', marginTop: 2 },
  footer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
    gap: 12,
  },
  backButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    alignItems: 'center',
  },
  backButtonText: { fontSize: 16, color: '#666', fontWeight: '500' },
  nextButton: {
    flex: 2,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
  },
  nextButtonText: { fontSize: 16, color: '#fff', fontWeight: '600' },
});
