import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useAuthStore } from '@/store/auth';
import { useKYCStore } from '@/store/kyc';
import { Button } from '@/components/Button';

export default function SubmitKYCScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { status, isLoading, submitForReview } = useKYCStore();

  const farmerId = user?.id;

  const handleSubmit = async () => {
    if (!farmerId) {
      Alert.alert('Error', 'Farmer ID not found');
      return;
    }

    // Final validation
    if (!status?.personal_info_complete) {
      Alert.alert('Error', 'Please complete your personal information first');
      return;
    }

    if (!status?.documents_complete) {
      Alert.alert('Error', 'Please upload all required documents first');
      return;
    }

    if (!status?.bank_info_complete) {
      Alert.alert('Error', 'Please provide your bank information first');
      return;
    }

    Alert.alert(
      'Submit for Review',
      'Are you sure you want to submit your KYC application for review? You will not be able to make changes after submission.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Submit',
          onPress: async () => {
            try {
              await submitForReview(farmerId);
              Alert.alert(
                'Success',
                'Your KYC application has been submitted for review. You will be notified once the review is complete.',
                [{ text: 'OK', onPress: () => router.replace('/kyc') }]
              );
            } catch (err: any) {
              Alert.alert('Error', err.message || 'Failed to submit application');
            }
          },
        },
      ]
    );
  };

  if (!status) {
    return null;
  }

  return (
    <View style={styles.container} testID="submit-screen">
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Review & Submit</Text>
          <Text style={styles.subtitle}>
            Review your information before submitting for verification
          </Text>
        </View>

        {/* Checklist */}
        <View style={styles.checklist}>
          <Text style={styles.checklistTitle}>Application Checklist</Text>

          <View style={[styles.checkItem, status.personal_info_complete && styles.checkItemComplete]}>
            <Text style={styles.checkIcon}>
              {status.personal_info_complete ? '✓' : '○'}
            </Text>
            <View style={styles.checkInfo}>
              <Text style={styles.checkLabel}>Personal Information</Text>
              <Text style={styles.checkDescription}>
                {status.personal_info_complete ? 'Complete' : 'Incomplete'}
              </Text>
            </View>
          </View>

          <View style={[styles.checkItem, status.documents_complete && styles.checkItemComplete]}>
            <Text style={styles.checkIcon}>
              {status.documents_complete ? '✓' : '○'}
            </Text>
            <View style={styles.checkInfo}>
              <Text style={styles.checkLabel}>Documents</Text>
              <Text style={styles.checkDescription}>
                {status.documents_complete
                  ? `${status.documents_submitted.length} documents uploaded`
                  : `${status.missing_documents.length} documents missing`}
              </Text>
            </View>
          </View>

          {status.required_biometrics.length > 0 && (
            <View style={[styles.checkItem, status.biometrics_complete && styles.checkItemComplete]}>
              <Text style={styles.checkIcon}>
                {status.biometrics_complete ? '✓' : '○'}
              </Text>
              <View style={styles.checkInfo}>
                <Text style={styles.checkLabel}>Biometrics</Text>
                <Text style={styles.checkDescription}>
                  {status.biometrics_complete ? 'Complete' : 'Incomplete'}
                </Text>
              </View>
            </View>
          )}

          <View style={[styles.checkItem, status.bank_info_complete && styles.checkItemComplete]}>
            <Text style={styles.checkIcon}>
              {status.bank_info_complete ? '✓' : '○'}
            </Text>
            <View style={styles.checkInfo}>
              <Text style={styles.checkLabel}>Bank Information</Text>
              <Text style={styles.checkDescription}>
                {status.bank_info_complete ? 'Complete' : 'Incomplete'}
              </Text>
            </View>
          </View>
        </View>

        {/* Info Box */}
        <View style={styles.infoBox}>
          <Text style={styles.infoIcon}>ℹ️</Text>
          <View style={styles.infoContent}>
            <Text style={styles.infoTitle}>What happens next?</Text>
            <Text style={styles.infoText}>
              • Your application will be reviewed by our verification team{'\n'}
              • Review typically takes 1-3 business days{'\n'}
              • You'll be notified via SMS and in-app notification{'\n'}
              • If approved, you'll gain access to all platform features
            </Text>
          </View>
        </View>

        {/* Submit Button */}
        {status.progress_percentage === 100 ? (
          <Button
            title="Submit for Review"
            onPress={handleSubmit}
            loading={isLoading}
            disabled={isLoading}
            testID="submit-for-review-button"
          />
        ) : (
          <View style={styles.warningBox}>
            <Text style={styles.warningText}>
              ⚠️ Please complete all required steps before submitting
            </Text>
          </View>
        )}

        <TouchableOpacity style={styles.cancelButton} onPress={() => router.back()}>
          <Text style={styles.cancelButtonText}>Back to Dashboard</Text>
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
  scrollView: {
    flex: 1,
  },
  content: {
    padding: SPACING.lg,
  },
  header: {
    marginBottom: SPACING.lg,
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
  checklist: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  checklistTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.md,
  },
  checkItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: 8,
    marginBottom: SPACING.sm,
    backgroundColor: COLORS.gray[50],
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  checkItemComplete: {
    backgroundColor: COLORS.success + '10',
    borderColor: COLORS.success,
  },
  checkIcon: {
    fontSize: 24,
    marginRight: SPACING.sm,
    width: 32,
    textAlign: 'center',
  },
  checkInfo: {
    flex: 1,
  },
  checkLabel: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.xs / 2,
  },
  checkDescription: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
  },
  infoBox: {
    flexDirection: 'row',
    backgroundColor: COLORS.primary + '10',
    borderRadius: 12,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  infoIcon: {
    fontSize: 24,
    marginRight: SPACING.sm,
  },
  infoContent: {
    flex: 1,
  },
  infoTitle: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.xs,
  },
  infoText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
    lineHeight: 20,
  },
  warningBox: {
    backgroundColor: COLORS.warning + '10',
    borderRadius: 8,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.warning,
  },
  warningText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
    textAlign: 'center',
  },
  cancelButton: {
    alignItems: 'center',
    padding: SPACING.md,
    marginTop: SPACING.sm,
  },
  cancelButtonText: {
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
});
