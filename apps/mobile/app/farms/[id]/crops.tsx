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
  Modal,
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

const COMMON_CROPS = [
  { value: 'maize', label: 'Maize', icon: '🌽' },
  { value: 'beans', label: 'Beans', icon: '🫘' },
  { value: 'wheat', label: 'Wheat', icon: '🌾' },
  { value: 'rice', label: 'Rice', icon: '🍚' },
  { value: 'potatoes', label: 'Potatoes', icon: '🥔' },
  { value: 'tomatoes', label: 'Tomatoes', icon: '🍅' },
  { value: 'onions', label: 'Onions', icon: '🧅' },
  { value: 'cabbage', label: 'Cabbage', icon: '🥬' },
  { value: 'kale', label: 'Kale/Sukuma Wiki', icon: '🥗' },
  { value: 'tea', label: 'Tea', icon: '🍵' },
  { value: 'coffee', label: 'Coffee', icon: '☕' },
  { value: 'sugarcane', label: 'Sugarcane', icon: '🎋' },
  { value: 'avocado', label: 'Avocado', icon: '🥑' },
  { value: 'mango', label: 'Mango', icon: '🥭' },
  { value: 'banana', label: 'Banana', icon: '🍌' },
  { value: 'sorghum', label: 'Sorghum', icon: '🌾' },
  { value: 'millet', label: 'Millet', icon: '🌾' },
  { value: 'groundnuts', label: 'Groundnuts', icon: '🥜' },
  { value: 'sunflower', label: 'Sunflower', icon: '🌻' },
  { value: 'other', label: 'Other', icon: '🌱' },
];

const SEASONS = [
  { value: 'long_rains', label: 'Long Rains (Mar-May)' },
  { value: 'short_rains', label: 'Short Rains (Oct-Dec)' },
  { value: 'dry_season', label: 'Dry Season (Irrigated)' },
  { value: 'year_round', label: 'Year Round' },
];

type CropRecord = {
  id: string;
  cropType: string;
  cropName?: string;
  season: string;
  year: number;
  acreage: number;
  yield?: number;
  yieldUnit?: string;
};

export default function CropsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { registrationDraft, addCropRecord, updateDraft, isLoading } = useFarmStore();

  const [crops, setCrops] = useState<CropRecord[]>(
    registrationDraft?.cropHistory || []
  );
  const [showAddModal, setShowAddModal] = useState(false);

  // Form state for new crop
  const [selectedCrop, setSelectedCrop] = useState('');
  const [customCropName, setCustomCropName] = useState('');
  const [selectedSeason, setSelectedSeason] = useState('');
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [acreage, setAcreage] = useState('');
  const [yieldAmount, setYieldAmount] = useState('');
  const [yieldUnit, setYieldUnit] = useState('bags');

  const getCropInfo = (value: string) => {
    return COMMON_CROPS.find((c) => c.value === value) || { label: value, icon: '🌱' };
  };

  const getSeasonLabel = (value: string) => {
    return SEASONS.find((s) => s.value === value)?.label || value;
  };

  const resetForm = () => {
    setSelectedCrop('');
    setCustomCropName('');
    setSelectedSeason('');
    setYear(new Date().getFullYear().toString());
    setAcreage('');
    setYieldAmount('');
    setYieldUnit('bags');
  };

  const handleAddCrop = () => {
    if (!selectedCrop) {
      Alert.alert('Error', 'Please select a crop type.');
      return;
    }

    if (selectedCrop === 'other' && !customCropName.trim()) {
      Alert.alert('Error', 'Please enter the crop name.');
      return;
    }

    if (!selectedSeason) {
      Alert.alert('Error', 'Please select a season.');
      return;
    }

    if (!acreage || isNaN(parseFloat(acreage))) {
      Alert.alert('Error', 'Please enter a valid acreage.');
      return;
    }

    const newCrop: CropRecord = {
      id: Date.now().toString(),
      cropType: selectedCrop,
      cropName: selectedCrop === 'other' ? customCropName : undefined,
      season: selectedSeason,
      year: parseInt(year),
      acreage: parseFloat(acreage),
      yield: yieldAmount ? parseFloat(yieldAmount) : undefined,
      yieldUnit: yieldAmount ? yieldUnit : undefined,
    };

    setCrops((prev) => [...prev, newCrop]);
    resetForm();
    setShowAddModal(false);
  };

  const handleRemoveCrop = (cropId: string) => {
    Alert.alert(
      'Remove Crop',
      'Are you sure you want to remove this crop record?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => setCrops((prev) => prev.filter((c) => c.id !== cropId)),
        },
      ]
    );
  };

  const handleSave = async () => {
    if (!id) {
      Alert.alert('Error', 'Farm ID not found.');
      return;
    }

    try {
      // Save each crop record
      for (const crop of crops) {
        await addCropRecord(id, {
          cropType: crop.cropType,
          cropName: crop.cropName,
          season: crop.season,
          year: crop.year,
          acreage: crop.acreage,
          yield: crop.yield,
          yieldUnit: crop.yieldUnit,
        });
      }

      // Save to draft for offline
      updateDraft({ cropHistory: crops });

      router.push(`/farms/${id}/review`);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to save crop records.');
    }
  };

  const handleSkip = () => {
    Alert.alert(
      'Skip Crop History',
      'You can add crop history later. Continue without adding?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Skip',
          onPress: () => {
            updateDraft({ cropHistory: crops });
            router.push(`/farms/${id}/review`);
          },
        },
      ]
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* Progress */}
      <StepIndicatorCompact
        steps={REGISTRATION_STEPS}
        currentStep="crops"
        completedSteps={['location', 'boundary', 'land_details', 'documents', 'soil_water']}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Crop History</Text>
          <Text style={styles.subtitle}>
            Add crops you've grown or are currently growing on this farm.
          </Text>
        </View>

        {/* Crop List */}
        {crops.length > 0 && (
          <View style={styles.cropList}>
            {crops.map((crop) => {
              const cropInfo = getCropInfo(crop.cropType);
              return (
                <View key={crop.id} style={styles.cropCard}>
                  <View style={styles.cropHeader}>
                    <Text style={styles.cropIcon}>{cropInfo.icon}</Text>
                    <View style={styles.cropInfo}>
                      <Text style={styles.cropName}>
                        {crop.cropName || cropInfo.label}
                      </Text>
                      <Text style={styles.cropDetails}>
                        {getSeasonLabel(crop.season)} {crop.year}
                      </Text>
                    </View>
                    <TouchableOpacity
                      onPress={() => handleRemoveCrop(crop.id)}
                      style={styles.removeButton}
                    >
                      <Text style={styles.removeButtonText}>×</Text>
                    </TouchableOpacity>
                  </View>
                  <View style={styles.cropStats}>
                    <View style={styles.cropStat}>
                      <Text style={styles.cropStatLabel}>Acreage</Text>
                      <Text style={styles.cropStatValue}>{crop.acreage} acres</Text>
                    </View>
                    {crop.yield && (
                      <View style={styles.cropStat}>
                        <Text style={styles.cropStatLabel}>Yield</Text>
                        <Text style={styles.cropStatValue}>
                          {crop.yield} {crop.yieldUnit}
                        </Text>
                      </View>
                    )}
                  </View>
                </View>
              );
            })}
          </View>
        )}

        {/* Add Crop Button */}
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setShowAddModal(true)}
        >
          <Text style={styles.addButtonIcon}>+</Text>
          <Text style={styles.addButtonText}>Add Crop</Text>
        </TouchableOpacity>

        {/* Empty State */}
        {crops.length === 0 && (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateIcon}>🌾</Text>
            <Text style={styles.emptyStateTitle}>No crops added yet</Text>
            <Text style={styles.emptyStateText}>
              Add your current or past crops to help us understand your farming history.
            </Text>
          </View>
        )}

        {/* Navigation Buttons */}
        <View style={styles.buttonContainer}>
          <Button
            title={crops.length > 0 ? 'Save & Continue' : 'Continue to Review'}
            onPress={handleSave}
            loading={isLoading}
            disabled={isLoading}
          />
        </View>

        {crops.length === 0 && (
          <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
            <Text style={styles.skipButtonText}>Skip for now</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Add Crop Modal */}
      <Modal visible={showAddModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <ScrollView>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Add Crop</Text>
                <TouchableOpacity onPress={() => setShowAddModal(false)}>
                  <Text style={styles.modalCloseText}>×</Text>
                </TouchableOpacity>
              </View>

              {/* Crop Selection */}
              <Text style={styles.modalLabel}>Crop Type *</Text>
              <View style={styles.cropGrid}>
                {COMMON_CROPS.map((crop) => (
                  <TouchableOpacity
                    key={crop.value}
                    style={[
                      styles.cropOption,
                      selectedCrop === crop.value && styles.cropOptionSelected,
                    ]}
                    onPress={() => setSelectedCrop(crop.value)}
                  >
                    <Text style={styles.cropOptionIcon}>{crop.icon}</Text>
                    <Text
                      style={[
                        styles.cropOptionLabel,
                        selectedCrop === crop.value && styles.cropOptionLabelSelected,
                      ]}
                    >
                      {crop.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              {/* Custom Crop Name */}
              {selectedCrop === 'other' && (
                <View style={styles.modalInputGroup}>
                  <Text style={styles.modalLabel}>Crop Name *</Text>
                  <TextInput
                    style={styles.modalInput}
                    value={customCropName}
                    onChangeText={setCustomCropName}
                    placeholder="Enter crop name"
                    placeholderTextColor={COLORS.gray[400]}
                  />
                </View>
              )}

              {/* Season */}
              <Text style={styles.modalLabel}>Season *</Text>
              <View style={styles.seasonOptions}>
                {SEASONS.map((season) => (
                  <TouchableOpacity
                    key={season.value}
                    style={[
                      styles.seasonOption,
                      selectedSeason === season.value && styles.seasonOptionSelected,
                    ]}
                    onPress={() => setSelectedSeason(season.value)}
                  >
                    <Text
                      style={[
                        styles.seasonOptionText,
                        selectedSeason === season.value && styles.seasonOptionTextSelected,
                      ]}
                    >
                      {season.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              {/* Year and Acreage */}
              <View style={styles.modalRow}>
                <View style={styles.modalHalf}>
                  <Text style={styles.modalLabel}>Year *</Text>
                  <TextInput
                    style={styles.modalInput}
                    value={year}
                    onChangeText={setYear}
                    keyboardType="numeric"
                    maxLength={4}
                  />
                </View>
                <View style={styles.modalHalf}>
                  <Text style={styles.modalLabel}>Acreage *</Text>
                  <TextInput
                    style={styles.modalInput}
                    value={acreage}
                    onChangeText={setAcreage}
                    placeholder="e.g., 2.5"
                    placeholderTextColor={COLORS.gray[400]}
                    keyboardType="decimal-pad"
                  />
                </View>
              </View>

              {/* Yield (Optional) */}
              <View style={styles.modalRow}>
                <View style={styles.modalHalf}>
                  <Text style={styles.modalLabel}>Yield (optional)</Text>
                  <TextInput
                    style={styles.modalInput}
                    value={yieldAmount}
                    onChangeText={setYieldAmount}
                    placeholder="e.g., 50"
                    placeholderTextColor={COLORS.gray[400]}
                    keyboardType="decimal-pad"
                  />
                </View>
                <View style={styles.modalHalf}>
                  <Text style={styles.modalLabel}>Unit</Text>
                  <View style={styles.unitOptions}>
                    {['bags', 'kg', 'tonnes'].map((unit) => (
                      <TouchableOpacity
                        key={unit}
                        style={[
                          styles.unitOption,
                          yieldUnit === unit && styles.unitOptionSelected,
                        ]}
                        onPress={() => setYieldUnit(unit)}
                      >
                        <Text
                          style={[
                            styles.unitOptionText,
                            yieldUnit === unit && styles.unitOptionTextSelected,
                          ]}
                        >
                          {unit}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              </View>

              {/* Add Button */}
              <TouchableOpacity style={styles.modalAddButton} onPress={handleAddCrop}>
                <Text style={styles.modalAddButtonText}>Add Crop</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.modalCancelButton}
                onPress={() => setShowAddModal(false)}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>
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
  cropList: {
    marginBottom: SPACING.lg,
  },
  cropCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  cropHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cropIcon: {
    fontSize: 32,
    marginRight: SPACING.sm,
  },
  cropInfo: {
    flex: 1,
  },
  cropName: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  cropDetails: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[500],
  },
  removeButton: {
    padding: SPACING.xs,
  },
  removeButtonText: {
    fontSize: 24,
    color: COLORS.gray[400],
  },
  cropStats: {
    flexDirection: 'row',
    marginTop: SPACING.sm,
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray[100],
  },
  cropStat: {
    marginRight: SPACING.xl,
  },
  cropStatLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[500],
  },
  cropStatValue: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '600',
    color: COLORS.gray[800],
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.md,
    backgroundColor: COLORS.white,
    borderRadius: 12,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: COLORS.primary,
    marginBottom: SPACING.lg,
  },
  addButtonIcon: {
    fontSize: 24,
    color: COLORS.primary,
    marginRight: SPACING.xs,
  },
  addButtonText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.primary,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    padding: SPACING.xl,
  },
  emptyStateIcon: {
    fontSize: 48,
    marginBottom: SPACING.md,
  },
  emptyStateTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.gray[700],
    marginBottom: SPACING.xs,
  },
  emptyStateText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[500],
    textAlign: 'center',
    lineHeight: 20,
  },
  buttonContainer: {
    marginTop: SPACING.lg,
    marginBottom: SPACING.md,
  },
  skipButton: {
    alignItems: 'center',
    padding: SPACING.sm,
  },
  skipButtonText: {
    color: COLORS.primary,
    fontSize: FONT_SIZES.md,
  },
  backButton: {
    alignItems: 'center',
    padding: SPACING.md,
  },
  backButtonText: {
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: COLORS.white,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: SPACING.lg,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  modalTitle: {
    fontSize: FONT_SIZES.xl,
    fontWeight: 'bold',
    color: COLORS.gray[900],
  },
  modalCloseText: {
    fontSize: 28,
    color: COLORS.gray[500],
  },
  modalLabel: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '600',
    color: COLORS.gray[700],
    marginBottom: SPACING.xs,
    marginTop: SPACING.md,
  },
  modalInputGroup: {
    marginBottom: SPACING.sm,
  },
  modalInput: {
    backgroundColor: COLORS.gray[50],
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 8,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[900],
  },
  cropGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  cropOption: {
    alignItems: 'center',
    padding: SPACING.sm,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
    backgroundColor: COLORS.gray[50],
    minWidth: 70,
  },
  cropOptionSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  cropOptionIcon: {
    fontSize: 24,
    marginBottom: 2,
  },
  cropOptionLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[700],
    textAlign: 'center',
  },
  cropOptionLabelSelected: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  seasonOptions: {
    gap: SPACING.xs,
  },
  seasonOption: {
    padding: SPACING.sm,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    backgroundColor: COLORS.white,
    marginBottom: SPACING.xs,
  },
  seasonOptionSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  seasonOptionText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
  },
  seasonOptionTextSelected: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  modalRow: {
    flexDirection: 'row',
    gap: SPACING.md,
  },
  modalHalf: {
    flex: 1,
  },
  unitOptions: {
    flexDirection: 'row',
    gap: SPACING.xs,
  },
  unitOption: {
    flex: 1,
    paddingVertical: SPACING.sm,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    alignItems: 'center',
  },
  unitOptionSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary,
  },
  unitOptionText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
  },
  unitOptionTextSelected: {
    color: COLORS.white,
    fontWeight: '500',
  },
  modalAddButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.md,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: SPACING.xl,
  },
  modalAddButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
  },
  modalCancelButton: {
    alignItems: 'center',
    padding: SPACING.md,
    marginTop: SPACING.sm,
  },
  modalCancelText: {
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
});
