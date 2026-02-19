import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { useAuthStore } from '@/store/auth';
import { eligibilityApi } from '@/services/api';

const TENANT_ID = '00000000-0000-0000-0000-000000000001';

type Scheme = {
  id: string;
  name: string;
  code: string;
  description: string;
  scheme_type: string;
  status: string;
  benefit_type: string;
  benefit_amount: number;
  benefit_description: string;
  application_deadline: string;
  max_beneficiaries: number;
  current_beneficiaries: number;
  auto_approve_enabled: boolean;
};

type RuleResult = {
  rule_id: string;
  rule_name: string;
  passed: boolean;
  actual_value: string;
  expected_value: string;
  message: string;
  is_mandatory: boolean;
};

type Assessment = {
  id: string;
  status: string;
  eligibility_score: number;
  risk_score: number;
  risk_level: string;
  credit_score: number;
  rules_passed: number;
  rules_failed: number;
  rule_results: RuleResult[];
  workflow_decision: string;
  final_decision: string;
  decision_reason: string;
  waitlist_position: number;
};

export default function SchemeDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user } = useAuthStore();
  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [assessing, setAssessing] = useState(false);

  useEffect(() => {
    loadSchemeData();
  }, [id]);

  const loadSchemeData = async () => {
    try {
      if (!id) return;

      const farmerId = user?.farmerId;

      const results = await Promise.allSettled([
        eligibilityApi.getScheme(id),
        farmerId ? eligibilityApi.listFarmerAssessments(farmerId) : Promise.resolve({ items: [] }),
      ]);

      const schemeResult = results[0];
      const assessmentsResult = results[1];

      if (schemeResult.status === 'fulfilled') {
        setScheme(schemeResult.value);
      } else {
        console.error('Error loading scheme:', schemeResult.reason);
      }

      if (assessmentsResult.status === 'fulfilled') {
        const assessments = assessmentsResult.value.items || [];
        const existing = assessments.find((a: Assessment & { scheme_id: string }) => a.scheme_id === id);
        if (existing) setAssessment(existing);
      }
    } catch (error) {
      console.error('Error loading scheme:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkEligibility = async () => {
    if (!id || !user?.farmerId) {
      Alert.alert('Error', 'Please complete your profile before checking eligibility.');
      return;
    }
    setAssessing(true);
    try {
      const result = await eligibilityApi.assess(user.farmerId, id, TENANT_ID);
      setAssessment(result);
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to check eligibility. Please try again.';
      Alert.alert('Error', message);
    } finally {
      setAssessing(false);
    }
  };

  const submitApplication = async () => {
    Alert.alert(
      'Submit Application',
      'Are you sure you want to apply for this scheme?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Apply',
          onPress: async () => {
            // Submit application logic
            Alert.alert(
              'Application Submitted',
              'Your application has been submitted and is pending review.'
            );
          },
        },
      ]
    );
  };

  const getRiskLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      low: '#4CAF50',
      medium: '#FF9800',
      high: '#f44336',
      very_high: '#B71C1C',
    };
    return colors[level] || '#666';
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return '#4CAF50';
    if (score >= 50) return '#FF9800';
    return '#f44336';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer} testID="eligibility-detail-loading">
        <ActivityIndicator size="large" color="#1B5E20" testID="eligibility-detail-loading-indicator" />
      </View>
    );
  }

  if (!scheme) {
    return (
      <View style={styles.errorContainer} testID="eligibility-detail-error">
        <Text style={styles.errorText} testID="eligibility-detail-error-text">Scheme not found</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} testID="eligibility-detail-screen">
      {/* Header */}
      <View style={styles.header} testID="eligibility-detail-header">
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
          testID="eligibility-detail-back-button"
        >
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>
        <View style={styles.schemeTypeTag} testID="eligibility-detail-type-tag">
          <Text style={styles.schemeTypeText} testID="eligibility-detail-type-text">
            {scheme.scheme_type.toUpperCase()}
          </Text>
        </View>
      </View>

      {/* Scheme Info */}
      <View style={styles.schemeInfo} testID="eligibility-detail-info">
        <Text style={styles.schemeName} testID="eligibility-detail-name">{scheme.name}</Text>
        <Text style={styles.schemeCode} testID="eligibility-detail-code">{scheme.code}</Text>
        <Text style={styles.schemeDescription} testID="eligibility-detail-description">{scheme.description}</Text>

        <View style={styles.infoCard} testID="eligibility-detail-info-card">
          <View style={styles.infoRow} testID="eligibility-detail-benefit-type-row">
            <Text style={styles.infoLabel}>Benefit Type</Text>
            <Text style={styles.infoValue} testID="eligibility-detail-benefit-type">{scheme.benefit_type}</Text>
          </View>
          <View style={styles.infoRow} testID="eligibility-detail-benefit-amount-row">
            <Text style={styles.infoLabel}>Benefit Amount</Text>
            <Text style={styles.infoValueHighlight} testID="eligibility-detail-benefit-amount">
              KES {(scheme.benefit_amount ?? 0).toLocaleString()}
            </Text>
          </View>
          <View style={styles.infoRow} testID="eligibility-detail-deadline-row">
            <Text style={styles.infoLabel}>Application Deadline</Text>
            <Text style={styles.infoValue} testID="eligibility-detail-deadline">
              {scheme.application_deadline ? new Date(scheme.application_deadline).toLocaleDateString() : 'No deadline'}
            </Text>
          </View>
          <View style={styles.infoRow} testID="eligibility-detail-slots-row">
            <Text style={styles.infoLabel}>Remaining Slots</Text>
            <Text style={styles.infoValue} testID="eligibility-detail-slots">
              {scheme.max_beneficiaries ? ((scheme.max_beneficiaries - (scheme.current_beneficiaries || 0)).toLocaleString()) : 'Unlimited'}
            </Text>
          </View>
        </View>

        {scheme.benefit_description ? (
          <Text style={styles.benefitDescription} testID="eligibility-detail-benefit-description">{scheme.benefit_description}</Text>
        ) : null}
      </View>

      {/* Check Eligibility Button */}
      {!assessment && (
        <TouchableOpacity
          style={styles.checkButton}
          onPress={checkEligibility}
          disabled={assessing}
          testID="eligibility-detail-check-button"
        >
          {assessing ? (
            <ActivityIndicator color="#fff" testID="eligibility-detail-check-loading" />
          ) : (
            <Text style={styles.checkButtonText}>Check My Eligibility</Text>
          )}
        </TouchableOpacity>
      )}

      {/* Assessment Results */}
      {assessment && (
        <View style={styles.assessmentSection} testID="eligibility-detail-assessment">
          <Text style={styles.sectionTitle} testID="eligibility-detail-assessment-title">Eligibility Assessment</Text>

          {/* Score Cards */}
          <View style={styles.scoreRow} testID="eligibility-detail-scores">
            <View style={styles.scoreCard} testID="eligibility-detail-score-card">
              <Text style={styles.scoreLabel} testID="eligibility-detail-score-label">Eligibility Score</Text>
              <Text
                style={[
                  styles.scoreValue,
                  { color: getScoreColor(assessment.eligibility_score ?? 0) },
                ]}
                testID="eligibility-detail-score-value"
              >
                {assessment.eligibility_score ?? 0}%
              </Text>
            </View>
            <View style={styles.scoreCard} testID="eligibility-detail-risk-card">
              <Text style={styles.scoreLabel} testID="eligibility-detail-risk-label">Risk Level</Text>
              <Text
                style={[
                  styles.scoreValue,
                  { color: getRiskLevelColor(assessment.risk_level) },
                ]}
                testID="eligibility-detail-risk-value"
              >
                {(assessment.risk_level || 'N/A').toUpperCase()}
              </Text>
            </View>
          </View>

          {/* Status Badge */}
          <View
            style={[
              styles.statusBadge,
              assessment.status === 'eligible' && styles.statusEligible,
              assessment.status === 'not_eligible' && styles.statusNotEligible,
            ]}
            testID="eligibility-detail-status-badge"
          >
            <Text style={styles.statusText} testID="eligibility-detail-status-text">
              {assessment.status === 'eligible'
                ? 'You are eligible for this scheme'
                : 'You are not eligible for this scheme'}
            </Text>
          </View>

          {/* Rules Summary */}
          <View style={styles.rulesSummary} testID="eligibility-detail-rules-summary">
            <Text style={styles.rulesTitle} testID="eligibility-detail-rules-title">Eligibility Criteria</Text>
            <View style={styles.rulesCount} testID="eligibility-detail-rules-count">
              <Text style={styles.passedCount} testID="eligibility-detail-rules-passed">
                {assessment.rules_passed} Passed
              </Text>
              <Text style={styles.failedCount} testID="eligibility-detail-rules-failed">
                {assessment.rules_failed} Failed
              </Text>
            </View>
          </View>

          {/* Rule Results */}
          {(assessment.rule_results || []).map((rule) => (
            <View
              key={rule.rule_id}
              style={[
                styles.ruleItem,
                rule.passed ? styles.rulePassed : styles.ruleFailed,
              ]}
              testID={`eligibility-detail-rule-${rule.rule_id}`}
            >
              <View style={styles.ruleHeader} testID={`eligibility-detail-rule-${rule.rule_id}-header`}>
                <Text style={styles.ruleIcon} testID={`eligibility-detail-rule-${rule.rule_id}-icon`}>
                  {rule.passed ? '✓' : '✗'}
                </Text>
                <Text style={styles.ruleName} testID={`eligibility-detail-rule-${rule.rule_id}-name`}>
                  {rule.rule_name}
                </Text>
                {rule.is_mandatory && (
                  <Text style={styles.mandatoryTag} testID={`eligibility-detail-rule-${rule.rule_id}-mandatory`}>
                    Required
                  </Text>
                )}
              </View>
              <Text style={styles.ruleMessage} testID={`eligibility-detail-rule-${rule.rule_id}-message`}>
                {rule.message}
              </Text>
              {rule.actual_value && (
                <Text style={styles.ruleValues} testID={`eligibility-detail-rule-${rule.rule_id}-value`}>
                  Your value: {rule.actual_value}
                </Text>
              )}
            </View>
          ))}

          {/* Apply Button */}
          {assessment.status === 'eligible' && (
            <TouchableOpacity
              style={styles.applyButton}
              onPress={submitApplication}
              testID="eligibility-detail-submit-button"
            >
              <Text style={styles.applyButtonText}>Submit Application</Text>
            </TouchableOpacity>
          )}

          {/* Not Eligible Message */}
          {assessment.status === 'not_eligible' && (
            <View style={styles.notEligibleMessage} testID="eligibility-detail-not-eligible-message">
              <Text style={styles.notEligibleTitle} testID="eligibility-detail-not-eligible-title">What you can do:</Text>
              <Text style={styles.notEligibleText} testID="eligibility-detail-not-eligible-text">
                - Complete your KYC verification{'\n'}
                - Register your farm with accurate details{'\n'}
                - Ensure your credit record is up to date{'\n'}
                - Check other available schemes
              </Text>
            </View>
          )}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#666',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 60,
    backgroundColor: '#1B5E20',
  },
  backButton: {
    padding: 8,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
  },
  schemeTypeTag: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
  },
  schemeTypeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  schemeInfo: {
    backgroundColor: '#fff',
    padding: 20,
  },
  schemeName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  schemeCode: {
    fontSize: 14,
    color: '#999',
    marginBottom: 12,
  },
  schemeDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 22,
    marginBottom: 16,
  },
  infoCard: {
    backgroundColor: '#f9f9f9',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  infoLabel: {
    fontSize: 14,
    color: '#666',
  },
  infoValue: {
    fontSize: 14,
    color: '#333',
  },
  infoValueHighlight: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1B5E20',
  },
  benefitDescription: {
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
  },
  checkButton: {
    backgroundColor: '#1B5E20',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  checkButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  assessmentSection: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  scoreRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  scoreCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  scoreLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  scoreValue: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  statusBadge: {
    backgroundColor: '#FFF3E0',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    alignItems: 'center',
  },
  statusEligible: {
    backgroundColor: '#E8F5E9',
  },
  statusNotEligible: {
    backgroundColor: '#FFEBEE',
  },
  statusText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  rulesSummary: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  rulesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  rulesCount: {
    flexDirection: 'row',
    gap: 12,
  },
  passedCount: {
    fontSize: 14,
    color: '#4CAF50',
    fontWeight: '600',
  },
  failedCount: {
    fontSize: 14,
    color: '#f44336',
    fontWeight: '600',
  },
  ruleItem: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    borderLeftWidth: 4,
  },
  rulePassed: {
    borderLeftColor: '#4CAF50',
  },
  ruleFailed: {
    borderLeftColor: '#f44336',
  },
  ruleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  ruleIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  ruleName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  mandatoryTag: {
    fontSize: 10,
    color: '#f44336',
    backgroundColor: '#FFEBEE',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  ruleMessage: {
    fontSize: 13,
    color: '#666',
    marginBottom: 4,
  },
  ruleValues: {
    fontSize: 12,
    color: '#999',
  },
  applyButton: {
    backgroundColor: '#1B5E20',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
  },
  applyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  notEligibleMessage: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
  },
  notEligibleTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  notEligibleText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 24,
  },
});
