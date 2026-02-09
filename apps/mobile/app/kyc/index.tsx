import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useAuthStore } from '@/store/auth';
import { useKYCStore } from '@/store/kyc';

export default function KYCDashboard() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { status, isLoading, error, getStatus, startKYC } = useKYCStore();

  // Get farmer_id from user (this would come from farmer profile)
  // For now, we'll use a placeholder
  const farmerId = user?.id; // In production, get actual farmer_id from farmer profile

  useEffect(() => {
    if (farmerId) {
      loadKYCStatus();
    }
  }, [farmerId]);

  const loadKYCStatus = async () => {
    try {
      await getStatus(farmerId!);
    } catch (err: any) {
      // If no KYC exists, we might want to start one
      if (err.response?.status === 404) {
        console.log('No KYC application found');
      }
    }
  };

  const handleStartKYC = async () => {
    if (!farmerId) {
      Alert.alert('Error', 'Farmer profile not found. Please complete your profile first.');
      return;
    }

    try {
      await startKYC(farmerId);
      Alert.alert('Success', 'KYC application started successfully');
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to start KYC application');
    }
  };

  const handleContinueStep = (step: string) => {
    switch (step) {
      case 'personal_info':
        router.push('/kyc/personal-info');
        break;
      case 'documents':
        router.push('/kyc/documents');
        break;
      case 'biometrics':
        router.push('/kyc/biometrics');
        break;
      case 'bank_info':
        router.push('/kyc/bank-info');
        break;
      default:
        Alert.alert('Info', 'This step is not yet available');
    }
  };

  const getStatusColor = (statusValue: string) => {
    switch (statusValue.toLowerCase()) {
      case 'pending':
      case 'in_progress':
        return COLORS.warning;
      case 'approved':
      case 'verified':
      case 'complete':
        return COLORS.success;
      case 'rejected':
      case 'failed':
        return COLORS.error;
      default:
        return COLORS.gray[500];
    }
  };

  const getStatusIcon = (complete: boolean) => {
    return complete ? '✓' : '○';
  };

  if (isLoading && !status) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Loading KYC status...</Text>
      </View>
    );
  }

  // No KYC application yet
  if (!status) {
    return (
      <View style={styles.container}>
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateIcon}>🔐</Text>
            <Text style={styles.emptyStateTitle}>KYC Verification</Text>
            <Text style={styles.emptyStateText}>
              Complete your Know Your Customer (KYC) verification to access all features and services.
            </Text>

            <View style={styles.benefitsContainer}>
              <Text style={styles.benefitsTitle}>Why KYC?</Text>
              <View style={styles.benefit}>
                <Text style={styles.benefitIcon}>✓</Text>
                <Text style={styles.benefitText}>Access financial services</Text>
              </View>
              <View style={styles.benefit}>
                <Text style={styles.benefitIcon}>✓</Text>
                <Text style={styles.benefitText}>Receive subsidies and grants</Text>
              </View>
              <View style={styles.benefit}>
                <Text style={styles.benefitIcon}>✓</Text>
                <Text style={styles.benefitText}>Get certified products</Text>
              </View>
              <View style={styles.benefit}>
                <Text style={styles.benefitIcon}>✓</Text>
                <Text style={styles.benefitText}>Secure your account</Text>
              </View>
            </View>

            <TouchableOpacity style={styles.startButton} onPress={handleStartKYC}>
              <Text style={styles.startButtonText}>Start KYC Verification</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    );
  }

  // KYC application exists
  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>KYC Verification</Text>
          <View
            style={[styles.statusBadge, { backgroundColor: getStatusColor(status.overall_status) }]}
          >
            <Text style={styles.statusBadgeText}>{status.overall_status.toUpperCase()}</Text>
          </View>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <Text style={styles.progressLabel}>Progress: {status.progress_percentage}%</Text>
          <View style={styles.progressBar}>
            <View
              style={[styles.progressFill, { width: `${status.progress_percentage}%` }]}
            />
          </View>
        </View>

        {/* Steps */}
        <View style={styles.stepsContainer}>
          <Text style={styles.sectionTitle}>Verification Steps</Text>

          {/* Personal Info */}
          <TouchableOpacity
            style={[
              styles.stepCard,
              status.personal_info_complete && styles.stepCardComplete,
            ]}
            onPress={() => !status.personal_info_complete && handleContinueStep('personal_info')}
            disabled={status.personal_info_complete}
          >
            <View style={styles.stepHeader}>
              <Text
                style={[
                  styles.stepIcon,
                  status.personal_info_complete && styles.stepIconComplete,
                ]}
              >
                {getStatusIcon(status.personal_info_complete)}
              </Text>
              <View style={styles.stepInfo}>
                <Text style={styles.stepTitle}>Personal Information</Text>
                <Text style={styles.stepDescription}>
                  {status.personal_info_complete ? 'Complete' : 'Provide your personal details'}
                </Text>
              </View>
            </View>
          </TouchableOpacity>

          {/* Documents */}
          <TouchableOpacity
            style={[styles.stepCard, status.documents_complete && styles.stepCardComplete]}
            onPress={() => !status.documents_complete && handleContinueStep('documents')}
            disabled={status.documents_complete}
          >
            <View style={styles.stepHeader}>
              <Text
                style={[styles.stepIcon, status.documents_complete && styles.stepIconComplete]}
              >
                {getStatusIcon(status.documents_complete)}
              </Text>
              <View style={styles.stepInfo}>
                <Text style={styles.stepTitle}>Document Upload</Text>
                <Text style={styles.stepDescription}>
                  {status.documents_complete
                    ? `All ${status.documents_submitted.length} documents uploaded`
                    : `${status.missing_documents.length} documents required`}
                </Text>
              </View>
            </View>
            {!status.documents_complete && status.missing_documents.length > 0 && (
              <View style={styles.stepDetails}>
                <Text style={styles.stepDetailsLabel}>Required:</Text>
                {status.missing_documents.map((doc, index) => (
                  <Text key={index} style={styles.stepDetailsItem}>
                    • {doc.replace(/_/g, ' ')}
                  </Text>
                ))}
              </View>
            )}
          </TouchableOpacity>

          {/* Biometrics (Optional) */}
          {status.required_biometrics.length > 0 && (
            <TouchableOpacity
              style={[styles.stepCard, status.biometrics_complete && styles.stepCardComplete]}
              onPress={() => !status.biometrics_complete && handleContinueStep('biometrics')}
              disabled={status.biometrics_complete}
            >
              <View style={styles.stepHeader}>
                <Text
                  style={[styles.stepIcon, status.biometrics_complete && styles.stepIconComplete]}
                >
                  {getStatusIcon(status.biometrics_complete)}
                </Text>
                <View style={styles.stepInfo}>
                  <Text style={styles.stepTitle}>Biometric Capture</Text>
                  <Text style={styles.stepDescription}>
                    {status.biometrics_complete
                      ? 'Biometrics captured'
                      : `${status.missing_biometrics.length} biometrics required`}
                  </Text>
                </View>
              </View>
            </TouchableOpacity>
          )}

          {/* Bank Info */}
          <TouchableOpacity
            style={[styles.stepCard, status.bank_info_complete && styles.stepCardComplete]}
            onPress={() => !status.bank_info_complete && handleContinueStep('bank_info')}
            disabled={status.bank_info_complete}
          >
            <View style={styles.stepHeader}>
              <Text
                style={[styles.stepIcon, status.bank_info_complete && styles.stepIconComplete]}
              >
                {getStatusIcon(status.bank_info_complete)}
              </Text>
              <View style={styles.stepInfo}>
                <Text style={styles.stepTitle}>Bank Information</Text>
                <Text style={styles.stepDescription}>
                  {status.bank_info_complete
                    ? 'Complete'
                    : 'Provide your bank account details'}
                </Text>
              </View>
            </View>
          </TouchableOpacity>

          {/* External Verification */}
          {status.external_verifications.length > 0 && (
            <View style={[styles.stepCard, styles.stepCardInfo]}>
              <View style={styles.stepHeader}>
                <Text style={styles.stepIcon}>ℹ</Text>
                <View style={styles.stepInfo}>
                  <Text style={styles.stepTitle}>External Verification</Text>
                  <Text style={styles.stepDescription}>Automatic verification in progress</Text>
                </View>
              </View>
              <View style={styles.stepDetails}>
                {status.external_verifications.map((verification, index) => (
                  <View key={index} style={styles.verificationItem}>
                    <Text style={styles.verificationLabel}>
                      {verification.verification_type.replace(/_/g, ' ')}:
                    </Text>
                    <Text
                      style={[
                        styles.verificationStatus,
                        { color: getStatusColor(verification.status) },
                      ]}
                    >
                      {verification.status}
                    </Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Review Status */}
          {status.in_review_queue && (
            <View style={[styles.stepCard, styles.stepCardWarning]}>
              <View style={styles.stepHeader}>
                <Text style={styles.stepIcon}>⏳</Text>
                <View style={styles.stepInfo}>
                  <Text style={styles.stepTitle}>Under Review</Text>
                  <Text style={styles.stepDescription}>
                    Your application is being reviewed by our team
                  </Text>
                </View>
              </View>
            </View>
          )}

          {/* Rejection Notice */}
          {status.rejection_reason && (
            <View style={[styles.stepCard, styles.stepCardError]}>
              <View style={styles.stepHeader}>
                <Text style={styles.stepIcon}>✗</Text>
                <View style={styles.stepInfo}>
                  <Text style={styles.stepTitle}>Verification Declined</Text>
                  <Text style={styles.stepDescription}>{status.rejection_reason}</Text>
                </View>
              </View>
            </View>
          )}
        </View>

        {/* Submit Button */}
        {!status.in_review_queue &&
          status.overall_status !== 'complete' &&
          status.overall_status !== 'approved' &&
          status.progress_percentage === 100 && (
            <TouchableOpacity
              style={styles.submitButton}
              onPress={() => router.push('/kyc/submit')}
            >
              <Text style={styles.submitButtonText}>Submit for Review</Text>
            </TouchableOpacity>
          )}
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
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.gray[50],
  },
  loadingText: {
    marginTop: SPACING.md,
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[600],
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: SPACING.lg,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  title: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.gray[900],
  },
  statusBadge: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.xs,
    borderRadius: 12,
  },
  statusBadgeText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.xs,
    fontWeight: '600',
  },
  progressContainer: {
    marginBottom: SPACING.xl,
  },
  progressLabel: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
    marginBottom: SPACING.xs,
    fontWeight: '500',
  },
  progressBar: {
    height: 8,
    backgroundColor: COLORS.gray[200],
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
    borderRadius: 4,
  },
  stepsContainer: {
    marginBottom: SPACING.xl,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.md,
  },
  stepCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  stepCardComplete: {
    borderColor: COLORS.success,
    backgroundColor: COLORS.success + '10',
  },
  stepCardInfo: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  stepCardWarning: {
    borderColor: COLORS.warning,
    backgroundColor: COLORS.warning + '10',
  },
  stepCardError: {
    borderColor: COLORS.error,
    backgroundColor: COLORS.error + '10',
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stepIcon: {
    fontSize: 24,
    marginRight: SPACING.sm,
    width: 32,
    textAlign: 'center',
  },
  stepIconComplete: {
    color: COLORS.success,
  },
  stepInfo: {
    flex: 1,
  },
  stepTitle: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.xs / 2,
  },
  stepDescription: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
  },
  stepDetails: {
    marginTop: SPACING.sm,
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray[200],
  },
  stepDetailsLabel: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '500',
    color: COLORS.gray[700],
    marginBottom: SPACING.xs,
  },
  stepDetailsItem: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
    marginLeft: SPACING.sm,
  },
  verificationItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SPACING.xs / 2,
  },
  verificationLabel: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
    textTransform: 'capitalize',
  },
  verificationStatus: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '500',
  },
  submitButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.md,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: SPACING.lg,
  },
  submitButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    paddingTop: SPACING.xl * 2,
  },
  emptyStateIcon: {
    fontSize: 64,
    marginBottom: SPACING.lg,
  },
  emptyStateTitle: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: SPACING.sm,
  },
  emptyStateText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[600],
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: SPACING.xl,
    paddingHorizontal: SPACING.lg,
  },
  benefitsContainer: {
    width: '100%',
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.lg,
    marginBottom: SPACING.xl,
  },
  benefitsTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.md,
  },
  benefit: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  benefitIcon: {
    fontSize: 16,
    color: COLORS.success,
    marginRight: SPACING.sm,
    width: 20,
  },
  benefitText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[700],
  },
  startButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.xl * 2,
    paddingVertical: SPACING.md,
    borderRadius: 8,
  },
  startButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
  },
});
