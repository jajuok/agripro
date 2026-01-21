import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useFarmStore } from '@/store/farm';
import { StepIndicatorCompact } from '@/components/StepIndicator';
import { Button } from '@/components/Button';

const REGISTRATION_STEPS = [
  { key: 'location', label: 'Location' },
  { key: 'boundary', label: 'Boundary' },
  { key: 'land_details', label: 'Land' },
  { key: 'documents', label: 'Documents' },
  { key: 'soil_water', label: 'Soil & Water' },
  { key: 'crops', label: 'Crops' },
  { key: 'review', label: 'Review' },
];

const SOIL_TYPES = [
  { value: 'clay', label: 'Clay', description: 'Heavy, retains water' },
  { value: 'sandy', label: 'Sandy', description: 'Light, drains quickly' },
  { value: 'loam', label: 'Loam', description: 'Balanced, ideal for farming' },
  { value: 'silt', label: 'Silt', description: 'Smooth, fertile' },
  { value: 'peat', label: 'Peat', description: 'Dark, high organic matter' },
  { value: 'chalky', label: 'Chalky', description: 'Alkaline, stony' },
  { value: 'unknown', label: 'Unknown', description: 'Not sure' },
];

const WATER_SOURCES = [
  { value: 'rain_fed', label: 'Rain-fed Only' },
  { value: 'river', label: 'River/Stream' },
  { value: 'borehole', label: 'Borehole' },
  { value: 'dam', label: 'Dam/Reservoir' },
  { value: 'piped', label: 'Piped Water' },
  { value: 'spring', label: 'Spring' },
  { value: 'well', label: 'Well' },
  { value: 'canal', label: 'Canal/Furrow' },
];

const IRRIGATION_METHODS = [
  { value: 'none', label: 'None (Rain-fed)' },
  { value: 'drip', label: 'Drip Irrigation' },
  { value: 'sprinkler', label: 'Sprinkler' },
  { value: 'flood', label: 'Flood/Basin' },
  { value: 'furrow', label: 'Furrow' },
  { value: 'manual', label: 'Manual (Bucket/Watering Can)' },
];

const DRAINAGE_LEVELS = [
  { value: 'excellent', label: 'Excellent', color: COLORS.success },
  { value: 'good', label: 'Good', color: COLORS.primary },
  { value: 'moderate', label: 'Moderate', color: COLORS.warning },
  { value: 'poor', label: 'Poor', color: COLORS.error },
];

export default function SoilWaterScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { registrationDraft, saveSoilWater, updateDraft, isLoading } = useFarmStore();

  const [soilType, setSoilType] = useState(registrationDraft?.soilType || '');
  const [soilPh, setSoilPh] = useState(registrationDraft?.soilPh?.toString() || '');
  const [waterSources, setWaterSources] = useState<string[]>(
    registrationDraft?.waterSources || []
  );
  const [irrigationMethod, setIrrigationMethod] = useState(
    registrationDraft?.irrigationMethod || ''
  );
  const [drainage, setDrainage] = useState(registrationDraft?.drainage || '');
  const [waterAvailability, setWaterAvailability] = useState(
    registrationDraft?.waterAvailability || ''
  );
  const [notes, setNotes] = useState(registrationDraft?.soilWaterNotes || '');

  const toggleWaterSource = (source: string) => {
    setWaterSources((prev) =>
      prev.includes(source)
        ? prev.filter((s) => s !== source)
        : [...prev, source]
    );
  };

  const handleSave = async () => {
    if (!soilType) {
      Alert.alert('Error', 'Please select a soil type.');
      return;
    }

    if (waterSources.length === 0) {
      Alert.alert('Error', 'Please select at least one water source.');
      return;
    }

    if (!id) {
      Alert.alert('Error', 'Farm ID not found.');
      return;
    }

    const soilWaterData = {
      soilType,
      soilPh: soilPh ? parseFloat(soilPh) : undefined,
      waterSources,
      irrigationMethod: irrigationMethod || undefined,
      drainage: drainage || undefined,
      waterAvailability: waterAvailability || undefined,
      notes: notes || undefined,
    };

    try {
      await saveSoilWater(id, soilWaterData);
      router.push(`/farms/${id}/crops`);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to save soil & water data.');
    }
  };

  const handleBack = () => {
    updateDraft({
      soilType,
      soilPh: soilPh ? parseFloat(soilPh) : undefined,
      waterSources,
      irrigationMethod,
      drainage,
      waterAvailability,
      soilWaterNotes: notes,
    });
    router.back();
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* Progress */}
      <StepIndicatorCompact
        steps={REGISTRATION_STEPS}
        currentStep="soil_water"
        completedSteps={['location', 'boundary', 'land_details', 'documents']}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Text style={styles.title}>Soil & Water</Text>
          <Text style={styles.subtitle}>
            Tell us about your soil conditions and water availability.
          </Text>
        </View>

        {/* Soil Type */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Soil Type *</Text>
          <View style={styles.optionsGrid}>
            {SOIL_TYPES.map((type) => (
              <TouchableOpacity
                key={type.value}
                style={[
                  styles.optionCard,
                  soilType === type.value && styles.optionCardSelected,
                ]}
                onPress={() => setSoilType(type.value)}
              >
                <Text
                  style={[
                    styles.optionCardLabel,
                    soilType === type.value && styles.optionCardLabelSelected,
                  ]}
                >
                  {type.label}
                </Text>
                <Text style={styles.optionCardDescription}>{type.description}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Soil pH */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Soil pH (if known)</Text>
          <TextInput
            style={[styles.input, styles.smallInput]}
            value={soilPh}
            onChangeText={setSoilPh}
            placeholder="e.g., 6.5"
            placeholderTextColor={COLORS.gray[400]}
            keyboardType="decimal-pad"
          />
          <Text style={styles.hint}>
            pH range: 0-14. Most crops grow best in pH 6.0-7.0.
          </Text>
        </View>

        {/* Water Sources */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Water Sources *</Text>
          <Text style={styles.sectionSubtitle}>Select all that apply</Text>
          <View style={styles.chipContainer}>
            {WATER_SOURCES.map((source) => (
              <TouchableOpacity
                key={source.value}
                style={[
                  styles.chip,
                  waterSources.includes(source.value) && styles.chipSelected,
                ]}
                onPress={() => toggleWaterSource(source.value)}
              >
                <Text
                  style={[
                    styles.chipText,
                    waterSources.includes(source.value) && styles.chipTextSelected,
                  ]}
                >
                  {source.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Irrigation Method */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Irrigation Method</Text>
          <View style={styles.chipContainer}>
            {IRRIGATION_METHODS.map((method) => (
              <TouchableOpacity
                key={method.value}
                style={[
                  styles.chip,
                  irrigationMethod === method.value && styles.chipSelected,
                ]}
                onPress={() => setIrrigationMethod(method.value)}
              >
                <Text
                  style={[
                    styles.chipText,
                    irrigationMethod === method.value && styles.chipTextSelected,
                  ]}
                >
                  {method.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Drainage */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Drainage Quality</Text>
          <View style={styles.drainageOptions}>
            {DRAINAGE_LEVELS.map((level) => (
              <TouchableOpacity
                key={level.value}
                style={[
                  styles.drainageOption,
                  drainage === level.value && {
                    backgroundColor: level.color + '20',
                    borderColor: level.color,
                  },
                ]}
                onPress={() => setDrainage(level.value)}
              >
                <View
                  style={[
                    styles.drainageIndicator,
                    { backgroundColor: level.color },
                  ]}
                />
                <Text
                  style={[
                    styles.drainageLabel,
                    drainage === level.value && { color: level.color },
                  ]}
                >
                  {level.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Water Availability */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Water Availability</Text>
          <View style={styles.chipContainer}>
            {['year_round', 'seasonal', 'unreliable'].map((option) => (
              <TouchableOpacity
                key={option}
                style={[
                  styles.chip,
                  waterAvailability === option && styles.chipSelected,
                ]}
                onPress={() => setWaterAvailability(option)}
              >
                <Text
                  style={[
                    styles.chipText,
                    waterAvailability === option && styles.chipTextSelected,
                  ]}
                >
                  {option === 'year_round'
                    ? 'Year Round'
                    : option === 'seasonal'
                    ? 'Seasonal'
                    : 'Unreliable'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Additional Notes */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Additional Notes</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={notes}
            onChangeText={setNotes}
            placeholder="Any other soil or water information..."
            placeholderTextColor={COLORS.gray[400]}
            multiline
            numberOfLines={3}
            textAlignVertical="top"
          />
        </View>

        {/* Navigation Buttons */}
        <View style={styles.buttonContainer}>
          <Button
            title="Save & Continue"
            onPress={handleSave}
            loading={isLoading}
            disabled={!soilType || waterSources.length === 0 || isLoading}
          />
        </View>

        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.gray[50],
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: SPACING.lg,
  },
  header: {
    marginBottom: SPACING.xl,
  },
  title: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: SPACING.xs,
  },
  subtitle: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[600],
    lineHeight: 22,
  },
  section: {
    marginBottom: SPACING.xl,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.gray[800],
    marginBottom: SPACING.xs,
  },
  sectionSubtitle: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[500],
    marginBottom: SPACING.md,
  },
  inputGroup: {
    marginBottom: SPACING.lg,
  },
  label: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '600',
    color: COLORS.gray[700],
    marginBottom: SPACING.xs,
  },
  input: {
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 8,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[900],
  },
  smallInput: {
    width: 100,
  },
  textArea: {
    minHeight: 80,
    paddingTop: SPACING.sm,
  },
  hint: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[500],
    marginTop: SPACING.xs,
  },
  optionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  optionCard: {
    padding: SPACING.sm,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    backgroundColor: COLORS.white,
    minWidth: 100,
  },
  optionCardSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  optionCardLabel: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '600',
    color: COLORS.gray[800],
  },
  optionCardLabelSelected: {
    color: COLORS.primary,
  },
  optionCardDescription: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[500],
    marginTop: 2,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  chip: {
    paddingVertical: SPACING.xs,
    paddingHorizontal: SPACING.md,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    backgroundColor: COLORS.white,
  },
  chipSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary,
  },
  chipText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
  },
  chipTextSelected: {
    color: COLORS.white,
    fontWeight: '500',
  },
  drainageOptions: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  drainageOption: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.sm,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    backgroundColor: COLORS.white,
  },
  drainageIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: SPACING.xs,
  },
  drainageLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[700],
    fontWeight: '500',
  },
  buttonContainer: {
    marginTop: SPACING.lg,
    marginBottom: SPACING.md,
  },
  backButton: {
    alignItems: 'center',
    padding: SPACING.md,
  },
  backButtonText: {
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
});
