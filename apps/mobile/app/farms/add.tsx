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
    >
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Text style={styles.title}>Register Your Farm</Text>
          <Text style={styles.subtitle}>
            Start by giving your farm a name and capturing your current location.
          </Text>
        </View>

        {/* Farm Name */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Farm Name *</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="e.g., Kijani Shamba"
            placeholderTextColor={COLORS.gray[400]}
          />
        </View>

        {/* Location */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Location *</Text>

          {isGettingLocation ? (
            <View style={styles.locationLoading}>
              <ActivityIndicator color={COLORS.primary} />
              <Text style={styles.locationLoadingText}>Getting your location...</Text>
            </View>
          ) : locationError ? (
            <View style={styles.locationError}>
              <Text style={styles.locationErrorText}>{locationError}</Text>
              <TouchableOpacity onPress={getCurrentLocation}>
                <Text style={styles.retryText}>Tap to retry</Text>
              </TouchableOpacity>
            </View>
          ) : latitude && longitude ? (
            <View style={styles.locationSuccess}>
              <Text style={styles.coordinatesText}>
                📍 {latitude.toFixed(6)}, {longitude.toFixed(6)}
              </Text>

              {adminLocation && (
                <View style={styles.adminLocation}>
                  {adminLocation.county && (
                    <Text style={styles.adminLocationText}>
                      County: {adminLocation.county}
                    </Text>
                  )}
                  {adminLocation.subCounty && (
                    <Text style={styles.adminLocationText}>
                      Sub-County: {adminLocation.subCounty}
                    </Text>
                  )}
                  {adminLocation.ward && (
                    <Text style={styles.adminLocationText}>
                      Ward: {adminLocation.ward}
                    </Text>
                  )}
                </View>
              )}

              <TouchableOpacity style={styles.refreshButton} onPress={getCurrentLocation}>
                <Text style={styles.refreshButtonText}>Refresh Location</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <TouchableOpacity style={styles.captureButton} onPress={getCurrentLocation}>
              <Text style={styles.captureButtonText}>📍 Capture Location</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Info card */}
        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>What happens next?</Text>
          <View style={styles.infoItem}>
            <Text style={styles.infoNumber}>1</Text>
            <Text style={styles.infoText}>Mark your farm boundaries on a map</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoNumber}>2</Text>
            <Text style={styles.infoText}>Enter land details and ownership info</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoNumber}>3</Text>
            <Text style={styles.infoText}>Upload documents and photos</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoNumber}>4</Text>
            <Text style={styles.infoText}>Add soil, water, and crop information</Text>
          </View>
        </View>

        {/* Error message */}
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Submit button */}
        <View style={styles.buttonContainer}>
          <Button
            title="Continue"
            onPress={handleSubmit}
            loading={isLoading}
            disabled={!name.trim() || !latitude || !longitude || isLoading}
          />
        </View>

        {/* Cancel */}
        <TouchableOpacity style={styles.cancelButton} onPress={() => router.back()}>
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
