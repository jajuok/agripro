import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  SafeAreaView,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useFarmStore, GeoJSONPolygon } from '@/store/farm';
import { StepIndicatorCompact } from '@/components/StepIndicator';
import BoundaryMap from '@/components/BoundaryMap';
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

export default function BoundaryScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const {
    registrationDraft,
    saveBoundary,
    updateDraft,
    isLoading,
  } = useFarmStore();

  const [boundary, setBoundary] = useState<GeoJSONPolygon | null>(null);
  const [areaAcres, setAreaAcres] = useState<number | null>(null);

  // Initial location from draft
  const initialLocation = registrationDraft
    ? {
        latitude: registrationDraft.latitude || -1.286389,
        longitude: registrationDraft.longitude || 36.817223,
      }
    : undefined;

  const handleBoundaryChange = (newBoundary: GeoJSONPolygon | null) => {
    setBoundary(newBoundary);
  };

  const handleAreaCalculated = (acres: number) => {
    setAreaAcres(acres);
    updateDraft({ boundaryAreaAcres: acres });
  };

  const handleSave = async () => {
    if (!boundary) {
      Alert.alert('Error', 'Please draw your farm boundary on the map.');
      return;
    }

    if (!id) {
      Alert.alert('Error', 'Farm ID not found.');
      return;
    }

    try {
      await saveBoundary(id, boundary);
      router.push(`/farms/${id}/land-details`);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to save boundary.');
    }
  };

  const handleSkip = () => {
    Alert.alert(
      'Skip Boundary',
      'You can add the boundary later. Continue without a boundary?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Skip',
          onPress: () => router.push(`/farms/${id}/land-details`),
        },
      ]
    );
  };

  const handleBack = () => {
    if (boundary) {
      Alert.alert(
        'Unsaved Changes',
        'You have unsaved boundary data. Are you sure you want to go back?',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Go Back', style: 'destructive', onPress: () => router.back() },
        ]
      );
    } else {
      router.back();
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Farm Boundary</Text>
        <TouchableOpacity onPress={handleSkip} style={styles.skipButton}>
          <Text style={styles.skipButtonText}>Skip</Text>
        </TouchableOpacity>
      </View>

      {/* Progress */}
      <StepIndicatorCompact
        steps={REGISTRATION_STEPS}
        currentStep="boundary"
        completedSteps={['location']}
      />

      {/* Instructions */}
      <View style={styles.instructionsContainer}>
        <Text style={styles.instructionsTitle}>Draw Your Farm Boundary</Text>
        <Text style={styles.instructionsText}>
          Tap on the map to add points, or use "Walk Boundary" to trace it by walking around your farm.
        </Text>
      </View>

      {/* Map */}
      <View style={styles.mapContainer}>
        <BoundaryMap
          initialLocation={initialLocation}
          initialBoundary={registrationDraft?.boundaryGeojson || undefined}
          onBoundaryChange={handleBoundaryChange}
          onAreaCalculated={handleAreaCalculated}
          editable={true}
          showControls={true}
        />
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        {areaAcres !== null && (
          <View style={styles.areaSummary}>
            <Text style={styles.areaLabel}>Estimated Area:</Text>
            <Text style={styles.areaValue}>{areaAcres.toFixed(2)} acres</Text>
          </View>
        )}

        <Button
          title={boundary ? 'Save & Continue' : 'Draw Boundary to Continue'}
          onPress={handleSave}
          loading={isLoading}
          disabled={!boundary || isLoading}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.white,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    backgroundColor: COLORS.primary,
  },
  backButton: {
    padding: SPACING.xs,
  },
  backButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
  },
  headerTitle: {
    color: COLORS.white,
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
  },
  skipButton: {
    padding: SPACING.xs,
  },
  skipButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
  },
  instructionsContainer: {
    padding: SPACING.md,
    backgroundColor: COLORS.gray[50],
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[200],
  },
  instructionsTitle: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.xs,
  },
  instructionsText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
    lineHeight: 20,
  },
  mapContainer: {
    flex: 1,
  },
  footer: {
    padding: SPACING.md,
    backgroundColor: COLORS.white,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray[200],
  },
  areaSummary: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
    padding: SPACING.sm,
    backgroundColor: COLORS.success + '10',
    borderRadius: 8,
  },
  areaLabel: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
  },
  areaValue: {
    fontSize: FONT_SIZES.lg,
    fontWeight: 'bold',
    color: COLORS.success,
  },
});
