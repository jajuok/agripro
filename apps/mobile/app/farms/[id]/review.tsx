import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  TouchableOpacity,
  ActivityIndicator,
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

const OWNERSHIP_LABELS: Record<string, string> = {
  freehold: 'Freehold (Owned)',
  leasehold: 'Leasehold',
  communal: 'Communal/Community',
  trust: 'Trust Land',
  family: 'Family Land',
  rented: 'Rented',
};

const LAND_USE_LABELS: Record<string, string> = {
  crop_farming: 'Crop Farming',
  livestock: 'Livestock',
  mixed: 'Mixed Farming',
  horticulture: 'Horticulture',
  agroforestry: 'Agroforestry',
  other: 'Other',
};

const SOIL_TYPE_LABELS: Record<string, string> = {
  clay: 'Clay',
  sandy: 'Sandy',
  loam: 'Loam',
  silt: 'Silt',
  peat: 'Peat',
  chalky: 'Chalky',
  unknown: 'Unknown',
};

export default function ReviewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { registrationDraft, completeRegistration, isLoading, error } = useFarmStore();

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!id) {
      Alert.alert('Error', 'Farm ID not found.');
      return;
    }

    Alert.alert(
      'Submit Registration',
      'Are you sure you want to submit this farm registration? You can still edit the details later.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Submit',
          onPress: async () => {
            setIsSubmitting(true);
            try {
              await completeRegistration(id);
              Alert.alert(
                'Success',
                'Your farm has been registered successfully!',
                [
                  {
                    text: 'View Farm',
                    onPress: () => router.replace(`/farms/${id}`),
                  },
                ]
              );
            } catch (err: any) {
              Alert.alert('Error', err.message || 'Failed to complete registration.');
            } finally {
              setIsSubmitting(false);
            }
          },
        },
      ]
    );
  };

  const navigateToStep = (step: string) => {
    const routeMap: Record<string, string> = {
      location: `/farms/add`,
      boundary: `/farms/${id}/boundary`,
      land_details: `/farms/${id}/land-details`,
      documents: `/farms/${id}/documents`,
      soil_water: `/farms/${id}/soil-water`,
      crops: `/farms/${id}/crops`,
    };
    const route = routeMap[step];
    if (route) {
      router.push(route);
    }
  };

  if (!registrationDraft) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Loading farm data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Progress */}
      <StepIndicatorCompact
        steps={REGISTRATION_STEPS}
        currentStep="review"
        completedSteps={['location', 'boundary', 'land_details', 'documents', 'soil_water', 'crops']}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Review & Submit</Text>
          <Text style={styles.subtitle}>
            Please review your farm information before submitting.
          </Text>
        </View>

        {/* Location Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Location</Text>
            <TouchableOpacity onPress={() => navigateToStep('boundary')}>
              <Text style={styles.editButton}>Edit</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            <View style={styles.row}>
              <Text style={styles.label}>Farm Name</Text>
              <Text style={styles.value}>{registrationDraft.name || '-'}</Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Coordinates</Text>
              <Text style={styles.value}>
                {registrationDraft.latitude?.toFixed(6)},{' '}
                {registrationDraft.longitude?.toFixed(6)}
              </Text>
            </View>
            {registrationDraft.county && (
              <View style={styles.row}>
                <Text style={styles.label}>County</Text>
                <Text style={styles.value}>{registrationDraft.county}</Text>
              </View>
            )}
            {registrationDraft.subCounty && (
              <View style={styles.row}>
                <Text style={styles.label}>Sub-County</Text>
                <Text style={styles.value}>{registrationDraft.subCounty}</Text>
              </View>
            )}
            {registrationDraft.ward && (
              <View style={styles.row}>
                <Text style={styles.label}>Ward</Text>
                <Text style={styles.value}>{registrationDraft.ward}</Text>
              </View>
            )}
          </View>
        </View>

        {/* Boundary Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Boundary</Text>
            <TouchableOpacity onPress={() => navigateToStep('boundary')}>
              <Text style={styles.editButton}>Edit</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            <View style={styles.row}>
              <Text style={styles.label}>Boundary Status</Text>
              <Text style={[
                styles.value,
                registrationDraft.boundaryGeojson ? styles.statusComplete : styles.statusIncomplete,
              ]}>
                {registrationDraft.boundaryGeojson ? 'Captured' : 'Not Set'}
              </Text>
            </View>
            {registrationDraft.boundaryAreaAcres && (
              <View style={styles.row}>
                <Text style={styles.label}>Calculated Area</Text>
                <Text style={styles.value}>
                  {registrationDraft.boundaryAreaAcres.toFixed(2)} acres
                </Text>
              </View>
            )}
          </View>
        </View>

        {/* Land Details Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Land Details</Text>
            <TouchableOpacity onPress={() => navigateToStep('land_details')}>
              <Text style={styles.editButton}>Edit</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            <View style={styles.row}>
              <Text style={styles.label}>Ownership Type</Text>
              <Text style={styles.value}>
                {OWNERSHIP_LABELS[registrationDraft.ownershipType || ''] || '-'}
              </Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Land Use</Text>
              <Text style={styles.value}>
                {LAND_USE_LABELS[registrationDraft.landUseType || ''] || '-'}
              </Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Total Acreage</Text>
              <Text style={styles.value}>
                {registrationDraft.totalAcreage
                  ? `${registrationDraft.totalAcreage} acres`
                  : '-'}
              </Text>
            </View>
            {registrationDraft.cultivatedAcreage && (
              <View style={styles.row}>
                <Text style={styles.label}>Cultivated Acreage</Text>
                <Text style={styles.value}>
                  {registrationDraft.cultivatedAcreage} acres
                </Text>
              </View>
            )}
            {registrationDraft.landReferenceNumber && (
              <View style={styles.row}>
                <Text style={styles.label}>LR Number</Text>
                <Text style={styles.value}>{registrationDraft.landReferenceNumber}</Text>
              </View>
            )}
          </View>
        </View>

        {/* Soil & Water Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Soil & Water</Text>
            <TouchableOpacity onPress={() => navigateToStep('soil_water')}>
              <Text style={styles.editButton}>Edit</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            <View style={styles.row}>
              <Text style={styles.label}>Soil Type</Text>
              <Text style={styles.value}>
                {SOIL_TYPE_LABELS[registrationDraft.soilType || ''] || '-'}
              </Text>
            </View>
            {registrationDraft.soilPh && (
              <View style={styles.row}>
                <Text style={styles.label}>Soil pH</Text>
                <Text style={styles.value}>{registrationDraft.soilPh}</Text>
              </View>
            )}
            <View style={styles.row}>
              <Text style={styles.label}>Water Sources</Text>
              <Text style={styles.value}>
                {registrationDraft.waterSources?.length
                  ? registrationDraft.waterSources.join(', ')
                  : '-'}
              </Text>
            </View>
            {registrationDraft.irrigationMethod && (
              <View style={styles.row}>
                <Text style={styles.label}>Irrigation</Text>
                <Text style={styles.value}>
                  {registrationDraft.irrigationMethod.replace('_', ' ')}
                </Text>
              </View>
            )}
          </View>
        </View>

        {/* Crop History Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Crop History</Text>
            <TouchableOpacity onPress={() => navigateToStep('crops')}>
              <Text style={styles.editButton}>Edit</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            {registrationDraft.cropHistory && registrationDraft.cropHistory.length > 0 ? (
              registrationDraft.cropHistory.map((crop: any, index: number) => (
                <View
                  key={index}
                  style={[
                    styles.cropItem,
                    index < registrationDraft.cropHistory.length - 1 && styles.cropItemBorder,
                  ]}
                >
                  <Text style={styles.cropName}>
                    {crop.cropName || crop.cropType}
                  </Text>
                  <Text style={styles.cropDetails}>
                    {crop.season} {crop.year} • {crop.acreage} acres
                    {crop.yield ? ` • Yield: ${crop.yield} ${crop.yieldUnit}` : ''}
                  </Text>
                </View>
              ))
            ) : (
              <Text style={styles.emptyText}>No crop history added</Text>
            )}
          </View>
        </View>

        {/* Error Message */}
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Submit Button */}
        <View style={styles.submitContainer}>
          <Button
            title="Submit Registration"
            onPress={handleSubmit}
            loading={isSubmitting || isLoading}
            disabled={isSubmitting || isLoading}
          />
        </View>

        {/* Save Draft Button */}
        <TouchableOpacity
          style={styles.saveDraftButton}
          onPress={() => {
            Alert.alert('Saved', 'Your progress has been saved. You can continue later.');
            router.replace('/(tabs)/farms');
          }}
        >
          <Text style={styles.saveDraftButtonText}>Save & Continue Later</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.gray[50],
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.gray[50],
  },
  loadingText: {
    marginTop: SPACING.md,
    color: COLORS.gray[600],
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
    marginBottom: SPACING.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.gray[800],
  },
  editButton: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.primary,
    fontWeight: '500',
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.xs,
  },
  label: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
  },
  value: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[900],
    fontWeight: '500',
    maxWidth: '60%',
    textAlign: 'right',
  },
  statusComplete: {
    color: COLORS.success,
  },
  statusIncomplete: {
    color: COLORS.warning,
  },
  cropItem: {
    paddingVertical: SPACING.sm,
  },
  cropItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[100],
  },
  cropName: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '600',
    color: COLORS.gray[900],
    textTransform: 'capitalize',
  },
  cropDetails: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[500],
    marginTop: 2,
    textTransform: 'capitalize',
  },
  emptyText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[400],
    fontStyle: 'italic',
    textAlign: 'center',
    paddingVertical: SPACING.sm,
  },
  errorContainer: {
    padding: SPACING.md,
    backgroundColor: COLORS.error + '10',
    borderRadius: 8,
    marginBottom: SPACING.md,
  },
  errorText: {
    color: COLORS.error,
    fontSize: FONT_SIZES.sm,
  },
  submitContainer: {
    marginTop: SPACING.lg,
    marginBottom: SPACING.md,
  },
  saveDraftButton: {
    alignItems: 'center',
    padding: SPACING.md,
    backgroundColor: COLORS.gray[100],
    borderRadius: 8,
    marginBottom: SPACING.sm,
  },
  saveDraftButtonText: {
    color: COLORS.gray[700],
    fontSize: FONT_SIZES.md,
    fontWeight: '500',
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
