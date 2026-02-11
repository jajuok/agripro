import { useState, useCallback } from 'react';
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
} from 'react-native';
import { router, useLocalSearchParams, useFocusEffect } from 'expo-router';
import * as Location from 'expo-location';
import { useCropPlanningStore } from '@/store/crop-planning';
import { COLORS, ACTIVITY_TYPE_ICONS } from '@/utils/constants';
import StatusBadge from '@/components/crop-planning/StatusBadge';

export default function ActivityCompleteScreen() {
  const { id, activityId } = useLocalSearchParams<{ id: string; activityId: string }>();
  const { activities, completeActivity, skipActivity, fetchActivities, isLoading } = useCropPlanningStore();

  const activity = activities.find((a) => a.id === activityId);

  const [notes, setNotes] = useState('');
  const [actualDate, setActualDate] = useState(new Date().toISOString().split('T')[0]);
  const [gpsLat, setGpsLat] = useState<number | null>(null);
  const [gpsLng, setGpsLng] = useState<number | null>(null);
  const [skipReason, setSkipReason] = useState('');
  const [showSkip, setShowSkip] = useState(false);

  useFocusEffect(
    useCallback(() => {
      if (id && activities.length === 0) fetchActivities(id);
    }, [id])
  );

  const captureGps = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'GPS permission required');
        return;
      }
      const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
      setGpsLat(loc.coords.latitude);
      setGpsLng(loc.coords.longitude);
    } catch {
      Alert.alert('Error', 'Failed to get GPS location');
    }
  };

  const handleComplete = async () => {
    try {
      await completeActivity(activityId!, {
        completion_notes: notes.trim() || undefined,
        gps_latitude: gpsLat,
        gps_longitude: gpsLng,
        actual_date: actualDate ? new Date(actualDate).toISOString() : undefined,
      });
      router.back();
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Failed to complete activity');
    }
  };

  const handleSkip = async () => {
    if (!skipReason.trim()) {
      Alert.alert('Required', 'Please provide a reason for skipping');
      return;
    }
    try {
      await skipActivity(activityId!, skipReason.trim());
      router.back();
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Failed to skip activity');
    }
  };

  if (!activity) {
    return (
      <View style={styles.loadingContainer}>
        {isLoading ? (
          <ActivityIndicator size="large" color={COLORS.primary} />
        ) : (
          <Text style={{ color: '#666', fontSize: 16 }}>Activity not found</Text>
        )}
      </View>
    );
  }

  const icon = ACTIVITY_TYPE_ICONS[activity.activityType] || '📋';
  const isAlreadyDone = activity.status === 'completed' || activity.status === 'skipped';

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      testID="cp-activity-complete-screen"
    >
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {/* Activity Summary */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryHeader}>
            <Text style={styles.summaryIcon}>{icon}</Text>
            <View style={styles.summaryInfo}>
              <Text style={styles.summaryTitle}>{activity.title}</Text>
              <Text style={styles.summaryDate}>
                Scheduled: {new Date(activity.scheduledDate).toLocaleDateString()}
              </Text>
            </View>
            <StatusBadge status={activity.status} type="activity" />
          </View>
          {activity.description && (
            <Text style={styles.summaryDesc}>{activity.description}</Text>
          )}
        </View>

        {isAlreadyDone ? (
          <View style={styles.doneCard}>
            <Text style={styles.doneText}>
              This activity has been {activity.status}
              {activity.completedAt
                ? ` on ${new Date(activity.completedAt).toLocaleDateString()}`
                : ''}
            </Text>
            {activity.completionNotes && (
              <Text style={styles.doneNotes}>Notes: {activity.completionNotes}</Text>
            )}
          </View>
        ) : (
          <>
            {/* Completion Form */}
            {!showSkip && (
              <>
                <Text style={styles.label}>Actual Date (YYYY-MM-DD)</Text>
                <TextInput
                  style={styles.input}
                  value={actualDate}
                  onChangeText={setActualDate}
                  testID="cp-activity-actual-date"
                />

                <Text style={styles.label}>Notes</Text>
                <TextInput
                  style={[styles.input, styles.textArea]}
                  value={notes}
                  onChangeText={setNotes}
                  placeholder="Completion notes..."
                  multiline
                  numberOfLines={3}
                  testID="cp-activity-notes"
                />

                {/* GPS */}
                <TouchableOpacity style={styles.gpsButton} onPress={captureGps} testID="cp-activity-gps">
                  <Text style={styles.gpsButtonText}>
                    {gpsLat ? `GPS: ${gpsLat.toFixed(5)}, ${gpsLng?.toFixed(5)}` : '📍 Capture GPS Location'}
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.completeButton, isLoading && { opacity: 0.6 }]}
                  onPress={handleComplete}
                  disabled={isLoading}
                  testID="cp-activity-mark-complete"
                >
                  {isLoading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text style={styles.completeButtonText}>Mark Complete</Text>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.skipToggle}
                  onPress={() => setShowSkip(true)}
                  testID="cp-activity-show-skip"
                >
                  <Text style={styles.skipToggleText}>Skip this activity instead</Text>
                </TouchableOpacity>
              </>
            )}

            {/* Skip Form */}
            {showSkip && (
              <>
                <Text style={styles.label}>Reason for Skipping *</Text>
                <TextInput
                  style={[styles.input, styles.textArea]}
                  value={skipReason}
                  onChangeText={setSkipReason}
                  placeholder="Why are you skipping this activity?"
                  multiline
                  numberOfLines={3}
                  testID="cp-activity-skip-reason"
                />

                <TouchableOpacity
                  style={[styles.skipButton, isLoading && { opacity: 0.6 }]}
                  onPress={handleSkip}
                  disabled={isLoading}
                  testID="cp-activity-skip-submit"
                >
                  {isLoading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text style={styles.completeButtonText}>Skip Activity</Text>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.skipToggle}
                  onPress={() => setShowSkip(false)}
                >
                  <Text style={styles.skipToggleText}>Go back to completion form</Text>
                </TouchableOpacity>
              </>
            )}
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f5f5f5' },
  content: { padding: 16, paddingBottom: 40 },
  summaryCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 16 },
  summaryHeader: { flexDirection: 'row', alignItems: 'center' },
  summaryIcon: { fontSize: 28, marginRight: 12 },
  summaryInfo: { flex: 1 },
  summaryTitle: { fontSize: 16, fontWeight: '600', color: '#333' },
  summaryDate: { fontSize: 12, color: '#666', marginTop: 2 },
  summaryDesc: { fontSize: 13, color: '#666', marginTop: 10, lineHeight: 19 },
  doneCard: { backgroundColor: '#E8F5E9', borderRadius: 12, padding: 16, marginBottom: 16 },
  doneText: { fontSize: 14, color: COLORS.primary, fontWeight: '500' },
  doneNotes: { fontSize: 13, color: '#666', marginTop: 8 },
  label: { fontSize: 14, fontWeight: '600', color: '#333', marginTop: 12, marginBottom: 6 },
  input: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  textArea: { minHeight: 80, textAlignVertical: 'top' },
  gpsButton: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    alignItems: 'center',
  },
  gpsButtonText: { fontSize: 14, color: COLORS.primary, fontWeight: '500' },
  completeButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 20,
  },
  completeButtonText: { fontSize: 16, fontWeight: '600', color: '#fff' },
  skipButton: {
    backgroundColor: '#FF9800',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 20,
  },
  skipToggle: { alignItems: 'center', marginTop: 16, padding: 8 },
  skipToggleText: { fontSize: 14, color: COLORS.primary, textDecorationLine: 'underline' },
});
