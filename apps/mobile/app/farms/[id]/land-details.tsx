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

const OWNERSHIP_TYPES = [
  { value: 'freehold', label: 'Freehold (Owned)' },
  { value: 'leasehold', label: 'Leasehold' },
  { value: 'communal', label: 'Communal/Community' },
  { value: 'trust', label: 'Trust Land' },
  { value: 'family', label: 'Family Land' },
  { value: 'rented', label: 'Rented' },
];

const LAND_USE_TYPES = [
  { value: 'crop_farming', label: 'Crop Farming' },
  { value: 'livestock', label: 'Livestock' },
  { value: 'mixed', label: 'Mixed Farming' },
  { value: 'horticulture', label: 'Horticulture' },
  { value: 'agroforestry', label: 'Agroforestry' },
  { value: 'other', label: 'Other' },
];

export default function LandDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { registrationDraft, saveLandDetails, updateDraft, isLoading } = useFarmStore();

  const [ownershipType, setOwnershipType] = useState(
    registrationDraft?.ownershipType || ''
  );
  const [landUseType, setLandUseType] = useState(
    registrationDraft?.landUseType || ''
  );
  const [totalAcreage, setTotalAcreage] = useState(
    registrationDraft?.totalAcreage?.toString() || ''
  );
  const [cultivatedAcreage, setCultivatedAcreage] = useState(
    registrationDraft?.cultivatedAcreage?.toString() || ''
  );
  const [landReferenceNumber, setLandReferenceNumber] = useState(
    registrationDraft?.landReferenceNumber || ''
  );
  const [plotIdSource, setPlotIdSource] = useState(
    registrationDraft?.plotIdSource || ''
  );
  const [addressDescription, setAddressDescription] = useState(
    registrationDraft?.addressDescription || ''
  );

  const handleSave = async () => {
    if (!ownershipType) {
      Alert.alert('Error', 'Please select an ownership type.');
      return;
    }

    if (!landUseType) {
      Alert.alert('Error', 'Please select a land use type.');
      return;
    }

    if (!totalAcreage || isNaN(parseFloat(totalAcreage))) {
      Alert.alert('Error', 'Please enter a valid total acreage.');
      return;
    }

    if (!id) {
      Alert.alert('Error', 'Farm ID not found.');
      return;
    }

    const landDetails = {
      ownershipType,
      landUseType,
      totalAcreage: parseFloat(totalAcreage),
      cultivatedAcreage: cultivatedAcreage ? parseFloat(cultivatedAcreage) : undefined,
      landReferenceNumber: landReferenceNumber || undefined,
      plotIdSource: plotIdSource || undefined,
      addressDescription: addressDescription || undefined,
    };

    try {
      await saveLandDetails(id, landDetails);
      router.push(`/farms/${id}/documents`);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to save land details.');
    }
  };

  const handleBack = () => {
    // Save current state to draft
    updateDraft({
      ownershipType,
      landUseType,
      totalAcreage: totalAcreage ? parseFloat(totalAcreage) : undefined,
      cultivatedAcreage: cultivatedAcreage ? parseFloat(cultivatedAcreage) : undefined,
      landReferenceNumber,
      plotIdSource,
      addressDescription,
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
        currentStep="land_details"
        completedSteps={['location', 'boundary']}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Text style={styles.title}>Land Details</Text>
          <Text style={styles.subtitle}>
            Provide information about your land ownership and usage.
          </Text>
        </View>

        {/* Ownership Type */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Ownership Type *</Text>
          <View style={styles.optionsGrid}>
            {OWNERSHIP_TYPES.map((type) => (
              <TouchableOpacity
                key={type.value}
                style={[
                  styles.optionButton,
                  ownershipType === type.value && styles.optionButtonSelected,
                ]}
                onPress={() => setOwnershipType(type.value)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    ownershipType === type.value && styles.optionButtonTextSelected,
                  ]}
                >
                  {type.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Land Use Type */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Primary Land Use *</Text>
          <View style={styles.optionsGrid}>
            {LAND_USE_TYPES.map((type) => (
              <TouchableOpacity
                key={type.value}
                style={[
                  styles.optionButton,
                  landUseType === type.value && styles.optionButtonSelected,
                ]}
                onPress={() => setLandUseType(type.value)}
              >
                <Text
                  style={[
                    styles.optionButtonText,
                    landUseType === type.value && styles.optionButtonTextSelected,
                  ]}
                >
                  {type.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Acreage */}
        <View style={styles.row}>
          <View style={[styles.inputGroup, styles.halfWidth]}>
            <Text style={styles.label}>Total Acreage *</Text>
            <TextInput
              style={styles.input}
              value={totalAcreage}
              onChangeText={setTotalAcreage}
              placeholder="e.g., 5.5"
              placeholderTextColor={COLORS.gray[400]}
              keyboardType="decimal-pad"
            />
            {registrationDraft?.boundaryAreaAcres && (
              <Text style={styles.hint}>
                Boundary area: {registrationDraft.boundaryAreaAcres.toFixed(2)} acres
              </Text>
            )}
          </View>

          <View style={[styles.inputGroup, styles.halfWidth]}>
            <Text style={styles.label}>Cultivated Acreage</Text>
            <TextInput
              style={styles.input}
              value={cultivatedAcreage}
              onChangeText={setCultivatedAcreage}
              placeholder="e.g., 4.0"
              placeholderTextColor={COLORS.gray[400]}
              keyboardType="decimal-pad"
            />
          </View>
        </View>

        {/* Land Reference Number */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Land Reference Number (LR)</Text>
          <TextInput
            style={styles.input}
            value={landReferenceNumber}
            onChangeText={setLandReferenceNumber}
            placeholder="e.g., LR 12345/1"
            placeholderTextColor={COLORS.gray[400]}
            autoCapitalize="characters"
          />
          <Text style={styles.hint}>
            If you have a title deed, enter the LR number here.
          </Text>
        </View>

        {/* Plot ID Source */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Plot ID Source</Text>
          <TextInput
            style={styles.input}
            value={plotIdSource}
            onChangeText={setPlotIdSource}
            placeholder="e.g., County Survey, Community Allocation"
            placeholderTextColor={COLORS.gray[400]}
          />
        </View>

        {/* Address Description */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Address / Directions</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={addressDescription}
            onChangeText={setAddressDescription}
            placeholder="Describe how to get to your farm..."
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
            disabled={!ownershipType || !landUseType || !totalAcreage || isLoading}
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
  optionButton: {
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    backgroundColor: COLORS.white,
  },
  optionButtonSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  optionButtonText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
  },
  optionButtonTextSelected: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  row: {
    flexDirection: 'row',
    gap: SPACING.md,
  },
  halfWidth: {
    flex: 1,
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
