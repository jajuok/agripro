import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useFarmStore } from '@/store/farm';
import { useAuthStore } from '@/store/auth';
import { gisApi } from '@/services/api';
import { Button } from '@/components/Button';

export default function AddFarmScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { startRegistration, isLoading, error } = useFarmStore();

  const [name, setName] = useState('');
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [isGettingLocation, setIsGettingLocation] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [adminLocation, setAdminLocation] = useState<{
    county: string | null;
    subCounty: string | null;
    ward: string | null;
  } | null>(null);

  // Get current location on mount
  useEffect(() => {
    getCurrentLocation();
  }, []);

  const getCurrentLocation = async () => {
    setIsGettingLocation(true);
    setLocationError(null);

    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLocationError('Location permission is required to register a farm.');
        return;
      }

      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });

      setLatitude(location.coords.latitude);
      setLongitude(location.coords.longitude);

      // Get administrative location
      try {
        const adminData = await gisApi.reverseGeocode(
          location.coords.latitude,
          location.coords.longitude
        );
        if (adminData.is_valid) {
          setAdminLocation({
            county: adminData.county,
            subCounty: adminData.sub_county,
            ward: adminData.ward,
          });
        }
      } catch {
        // Silently fail - admin location is not critical
      }
    } catch (err) {
      setLocationError('Failed to get current location. Please try again.');
    } finally {
      setIsGettingLocation(false);
    }
  };

  const handleSubmit = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter a farm name.');
      return;
    }

    if (!latitude || !longitude) {
      Alert.alert('Error', 'Please capture your location first.');
      return;
    }

    if (!user?.id) {
      Alert.alert('Error', 'User not authenticated.');
      return;
    }

    try {
      const farmId = await startRegistration(user.id, name.trim(), latitude, longitude);
      router.replace(`/farms/${farmId}/boundary`);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to start registration.');
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      testID="farms-add-screen"
    >
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        testID="farms-add-scroll"
      >
        <View style={styles.header} testID="farms-add-header">
          <Text style={styles.title} testID="farms-add-title">Register Your Farm</Text>
          <Text style={styles.subtitle} testID="farms-add-subtitle">
            Start by giving your farm a name and capturing your current location.
          </Text>
        </View>

        {/* Farm Name */}
        <View style={styles.inputGroup} testID="farms-add-name-group">
          <Text style={styles.label} testID="farms-add-name-label">Farm Name *</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="e.g., Kijani Shamba"
            placeholderTextColor={COLORS.gray[400]}
            testID="farms-add-name-input"
          />
        </View>

        {/* Location */}
        <View style={styles.inputGroup} testID="farms-add-location-group">
          <Text style={styles.label} testID="farms-add-location-label">Location *</Text>

          {isGettingLocation ? (
            <View style={styles.locationLoading} testID="farms-add-location-loading">
              <ActivityIndicator color={COLORS.primary} testID="farms-add-location-loading-indicator" />
              <Text style={styles.locationLoadingText} testID="farms-add-location-loading-text">Getting your location...</Text>
            </View>
          ) : locationError ? (
            <View style={styles.locationError} testID="farms-add-location-error">
              <Text style={styles.locationErrorText} testID="farms-add-location-error-text">{locationError}</Text>
              <TouchableOpacity onPress={getCurrentLocation} testID="farms-add-location-error-retry">
                <Text style={styles.retryText}>Tap to retry</Text>
              </TouchableOpacity>
            </View>
          ) : latitude && longitude ? (
            <View style={styles.locationSuccess} testID="farms-add-location-success">
              <Text style={styles.coordinatesText} testID="farms-add-location-coordinates">
                📍 {latitude.toFixed(6)}, {longitude.toFixed(6)}
              </Text>

              {adminLocation && (
                <View style={styles.adminLocation} testID="farms-add-admin-location">
                  {adminLocation.county && (
                    <Text style={styles.adminLocationText} testID="farms-add-admin-county">
                      County: {adminLocation.county}
                    </Text>
                  )}
                  {adminLocation.subCounty && (
                    <Text style={styles.adminLocationText} testID="farms-add-admin-subcounty">
                      Sub-County: {adminLocation.subCounty}
                    </Text>
                  )}
                  {adminLocation.ward && (
                    <Text style={styles.adminLocationText} testID="farms-add-admin-ward">
                      Ward: {adminLocation.ward}
                    </Text>
                  )}
                </View>
              )}

              <TouchableOpacity style={styles.refreshButton} onPress={getCurrentLocation} testID="farms-add-location-refresh">
                <Text style={styles.refreshButtonText}>Refresh Location</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <TouchableOpacity style={styles.captureButton} onPress={getCurrentLocation} testID="farms-add-location-capture">
              <Text style={styles.captureButtonText}>📍 Capture Location</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Info card */}
        <View style={styles.infoCard} testID="farms-add-info-card">
          <Text style={styles.infoTitle} testID="farms-add-info-title">What happens next?</Text>
          <View style={styles.infoItem} testID="farms-add-info-step-1">
            <Text style={styles.infoNumber}>1</Text>
            <Text style={styles.infoText}>Mark your farm boundaries on a map</Text>
          </View>
          <View style={styles.infoItem} testID="farms-add-info-step-2">
            <Text style={styles.infoNumber}>2</Text>
            <Text style={styles.infoText}>Enter land details and ownership info</Text>
          </View>
          <View style={styles.infoItem} testID="farms-add-info-step-3">
            <Text style={styles.infoNumber}>3</Text>
            <Text style={styles.infoText}>Upload documents and photos</Text>
          </View>
          <View style={styles.infoItem} testID="farms-add-info-step-4">
            <Text style={styles.infoNumber}>4</Text>
            <Text style={styles.infoText}>Add soil, water, and crop information</Text>
          </View>
        </View>

        {/* Error message */}
        {error && (
          <View style={styles.errorContainer} testID="farms-add-error">
            <Text style={styles.errorText} testID="farms-add-error-text">{error}</Text>
          </View>
        )}

        {/* Submit button */}
        <View style={styles.buttonContainer} testID="farms-add-submit-container">
          <Button
            title="Continue"
            onPress={handleSubmit}
            loading={isLoading}
            disabled={!name.trim() || !latitude || !longitude || isLoading}
            testID="farms-add-submit-button"
          />
        </View>

        {/* Cancel */}
        <TouchableOpacity style={styles.cancelButton} onPress={() => router.back()} testID="farms-add-cancel-button">
          <Text style={styles.cancelButtonText}>Cancel</Text>
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
  locationLoading: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
  },
  locationLoadingText: {
    marginLeft: SPACING.sm,
    color: COLORS.gray[600],
  },
  locationError: {
    padding: SPACING.md,
    backgroundColor: COLORS.error + '10',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.error,
  },
  locationErrorText: {
    color: COLORS.error,
    marginBottom: SPACING.xs,
  },
  retryText: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  locationSuccess: {
    padding: SPACING.md,
    backgroundColor: COLORS.success + '10',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.success,
  },
  coordinatesText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.success,
    fontWeight: '600',
  },
  adminLocation: {
    marginTop: SPACING.sm,
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.success + '30',
  },
  adminLocationText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
    marginBottom: 2,
  },
  refreshButton: {
    marginTop: SPACING.sm,
  },
  refreshButtonText: {
    color: COLORS.primary,
    fontWeight: '600',
    fontSize: FONT_SIZES.sm,
  },
  captureButton: {
    padding: SPACING.md,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: COLORS.primary,
    alignItems: 'center',
  },
  captureButtonText: {
    color: COLORS.primary,
    fontWeight: '600',
    fontSize: FONT_SIZES.md,
  },
  infoCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.lg,
    marginBottom: SPACING.xl,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  infoTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.md,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  infoNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    color: COLORS.white,
    textAlign: 'center',
    lineHeight: 24,
    fontSize: FONT_SIZES.sm,
    fontWeight: 'bold',
    marginRight: SPACING.sm,
  },
  infoText: {
    flex: 1,
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
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
  buttonContainer: {
    marginBottom: SPACING.md,
  },
  cancelButton: {
    alignItems: 'center',
    padding: SPACING.md,
  },
  cancelButtonText: {
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
});
