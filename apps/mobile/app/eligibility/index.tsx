import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
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
  application_deadline: string;
  max_beneficiaries: number;
  current_beneficiaries: number;
};

type Assessment = {
  id: string;
  scheme_id: string;
  status: string;
  eligibility_score: number;
  risk_level: string;
  final_decision: string;
  waitlist_position: number;
};

export default function EligibilityScreen() {
  const { user } = useAuthStore();
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [myAssessments, setMyAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const farmerId = user?.farmerId;

      const results = await Promise.allSettled([
        eligibilityApi.listSchemes(TENANT_ID, { status: 'active' }),
        farmerId ? eligibilityApi.listFarmerAssessments(farmerId) : Promise.resolve({ items: [] }),
      ]);

      const schemesResult = results[0];
      const assessmentsResult = results[1];

      if (schemesResult.status === 'fulfilled') {
        setSchemes(schemesResult.value.items || []);
      } else {
        console.error('Error loading schemes:', schemesResult.reason);
        setSchemes([]);
      }

      if (assessmentsResult.status === 'fulfilled') {
        setMyAssessments(assessmentsResult.value.items || []);
      } else {
        console.error('Error loading assessments:', assessmentsResult.reason);
        setMyAssessments([]);
      }

      if (schemesResult.status === 'rejected' && assessmentsResult.status === 'rejected') {
        setError('Failed to load eligibility data. Pull down to retry.');
      }
    } catch (err) {
      console.error('Error loading eligibility data:', err);
      setError('Something went wrong. Pull down to retry.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const getAssessmentForScheme = (schemeId: string) => {
    return myAssessments.find((a) => a.scheme_id === schemeId);
  };

  const getStatusBadge = (status: string, assessment?: Assessment, schemeId?: string) => {
    if (assessment) {
      const statusColors: Record<string, { bg: string; text: string }> = {
        approved: { bg: '#E8F5E9', text: '#2E7D32' },
        eligible: { bg: '#E3F2FD', text: '#1565C0' },
        pending: { bg: '#FFF3E0', text: '#EF6C00' },
        waitlisted: { bg: '#FFF8E1', text: '#F9A825' },
        rejected: { bg: '#FFEBEE', text: '#C62828' },
        not_eligible: { bg: '#FFEBEE', text: '#C62828' },
      };
      const style = statusColors[assessment.status] || statusColors.pending;
      return (
        <View style={[styles.badge, { backgroundColor: style.bg }]} testID={`eligibility-list-scheme-${schemeId}-status-badge`}>
          <Text style={[styles.badgeText, { color: style.text }]} testID={`eligibility-list-scheme-${schemeId}-status-text`}>
            {assessment.status.replace('_', ' ').toUpperCase()}
          </Text>
        </View>
      );
    }
    return null;
  };

  const renderSchemeCard = (scheme: Scheme) => {
    const assessment = getAssessmentForScheme(scheme.id);
    const maxBen = scheme.max_beneficiaries || 0;
    const curBen = scheme.current_beneficiaries || 0;
    const spotsLeft = maxBen - curBen;
    const fillPercentage = maxBen > 0 ? (curBen / maxBen) * 100 : 0;

    return (
      <TouchableOpacity
        key={scheme.id}
        style={styles.schemeCard}
        onPress={() => router.push(`/eligibility/${scheme.id}`)}
        testID={`eligibility-list-scheme-card-${scheme.id}`}
      >
        <View style={styles.schemeHeader} testID={`eligibility-list-scheme-${scheme.id}-header`}>
          <View style={styles.schemeTypeTag} testID={`eligibility-list-scheme-${scheme.id}-type-tag`}>
            <Text style={styles.schemeTypeText} testID={`eligibility-list-scheme-${scheme.id}-type-text`}>
              {scheme.scheme_type.toUpperCase()}
            </Text>
          </View>
          {getStatusBadge(scheme.status, assessment, scheme.id)}
        </View>

        <Text style={styles.schemeName} testID={`eligibility-list-scheme-${scheme.id}-name`}>
          {scheme.name}
        </Text>
        <Text style={styles.schemeCode} testID={`eligibility-list-scheme-${scheme.id}-code`}>
          {scheme.code}
        </Text>
        <Text style={styles.schemeDescription} numberOfLines={2} testID={`eligibility-list-scheme-${scheme.id}-description`}>
          {scheme.description}
        </Text>

        <View style={styles.benefitRow} testID={`eligibility-list-scheme-${scheme.id}-benefit`}>
          <Text style={styles.benefitLabel}>Benefit:</Text>
          <Text style={styles.benefitValue} testID={`eligibility-list-scheme-${scheme.id}-benefit-amount`}>
            KES {(scheme.benefit_amount ?? 0).toLocaleString()} ({scheme.benefit_type || 'N/A'})
          </Text>
        </View>

        <View style={styles.capacityContainer} testID={`eligibility-list-scheme-${scheme.id}-capacity`}>
          <View style={styles.capacityHeader}>
            <Text style={styles.capacityLabel}>Capacity</Text>
            <Text style={styles.capacityValue} testID={`eligibility-list-scheme-${scheme.id}-spots-left`}>
              {spotsLeft.toLocaleString()} spots left
            </Text>
          </View>
          <View style={styles.capacityBar} testID={`eligibility-list-scheme-${scheme.id}-capacity-bar`}>
            <View
              style={[
                styles.capacityFill,
                { width: `${fillPercentage}%` },
                fillPercentage > 90 && styles.capacityFillHigh,
              ]}
            />
          </View>
        </View>

        <View style={styles.deadlineRow} testID={`eligibility-list-scheme-${scheme.id}-deadline`}>
          <Text style={styles.deadlineIcon}>📅</Text>
          <Text style={styles.deadlineText} testID={`eligibility-list-scheme-${scheme.id}-deadline-text`}>
            Apply by: {scheme.application_deadline ? new Date(scheme.application_deadline).toLocaleDateString() : 'No deadline'}
          </Text>
        </View>

        {!assessment && (
          <TouchableOpacity
            style={styles.applyButton}
            onPress={() => router.push(`/eligibility/${scheme.id}`)}
            testID={`eligibility-list-scheme-${scheme.id}-check-button`}
          >
            <Text style={styles.applyButtonText}>Check Eligibility</Text>
          </TouchableOpacity>
        )}

        {assessment && assessment.status === 'waitlisted' && (
          <View style={styles.waitlistInfo} testID={`eligibility-list-scheme-${scheme.id}-waitlist-info`}>
            <Text style={styles.waitlistText} testID={`eligibility-list-scheme-${scheme.id}-waitlist-position`}>
              Waitlist Position: #{assessment.waitlist_position}
            </Text>
          </View>
        )}

        {assessment && assessment.status === 'approved' && (
          <View style={styles.approvedInfo} testID={`eligibility-list-scheme-${scheme.id}-enrolled-info`}>
            <Text style={styles.approvedText} testID={`eligibility-list-scheme-${scheme.id}-enrolled-text`}>
              You are enrolled in this scheme
            </Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer} testID="eligibility-list-loading">
        <ActivityIndicator size="large" color="#1B5E20" testID="eligibility-list-loading-indicator" />
        <Text style={styles.loadingText} testID="eligibility-list-loading-text">Loading schemes...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      testID="eligibility-list-screen"
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header} testID="eligibility-list-header">
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
          testID="eligibility-list-back-button"
        >
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title} testID="eligibility-list-title">Eligibility & Schemes</Text>
        <Text style={styles.subtitle} testID="eligibility-list-subtitle">
          Check your eligibility for government and private agricultural programs
        </Text>
      </View>

      {/* Summary Stats */}
      <View style={styles.statsRow} testID="eligibility-list-stats">
        <View style={styles.statCard} testID="eligibility-list-stat-available">
          <Text style={styles.statValue} testID="eligibility-list-stat-available-value">{schemes.length}</Text>
          <Text style={styles.statLabel} testID="eligibility-list-stat-available-label">Available Schemes</Text>
        </View>
        <View style={styles.statCard} testID="eligibility-list-stat-enrolled">
          <Text style={styles.statValue} testID="eligibility-list-stat-enrolled-value">
            {myAssessments.filter((a) => a.status === 'approved').length}
          </Text>
          <Text style={styles.statLabel} testID="eligibility-list-stat-enrolled-label">Enrolled</Text>
        </View>
        <View style={styles.statCard} testID="eligibility-list-stat-pending">
          <Text style={styles.statValue} testID="eligibility-list-stat-pending-value">
            {myAssessments.filter((a) => a.status === 'pending' || a.status === 'eligible').length}
          </Text>
          <Text style={styles.statLabel} testID="eligibility-list-stat-pending-label">Pending</Text>
        </View>
      </View>

      {/* Error State */}
      {error && (
        <View style={styles.emptyContainer} testID="eligibility-list-error">
          <Text style={styles.emptyText} testID="eligibility-list-error-text">{error}</Text>
        </View>
      )}

      {/* Scheme Cards */}
      <View style={styles.schemesSection} testID="eligibility-list-schemes-section">
        <Text style={styles.sectionTitle} testID="eligibility-list-section-title">Available Programs</Text>
        {schemes.length === 0 && !error && (
          <View style={styles.emptyContainer} testID="eligibility-list-empty">
            <Text style={styles.emptyText} testID="eligibility-list-empty-text">No schemes available at the moment.</Text>
          </View>
        )}
        {schemes.map(renderSchemeCard)}
      </View>
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
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 12,
    color: '#666',
  },
  header: {
    backgroundColor: '#1B5E20',
    padding: 20,
    paddingTop: 60,
  },
  backButton: {
    marginBottom: 12,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 14,
    color: '#E8F5E9',
    marginTop: 4,
  },
  statsRow: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1B5E20',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  schemesSection: {
    padding: 16,
    paddingTop: 0,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  schemeCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  schemeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  schemeTypeTag: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  schemeTypeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#1B5E20',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
  },
  schemeName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  schemeCode: {
    fontSize: 12,
    color: '#999',
    marginBottom: 8,
  },
  schemeDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  benefitRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  benefitLabel: {
    fontSize: 14,
    color: '#666',
  },
  benefitValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1B5E20',
    marginLeft: 4,
  },
  capacityContainer: {
    marginBottom: 12,
  },
  capacityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  capacityLabel: {
    fontSize: 12,
    color: '#666',
  },
  capacityValue: {
    fontSize: 12,
    color: '#666',
  },
  capacityBar: {
    height: 6,
    backgroundColor: '#E0E0E0',
    borderRadius: 3,
    overflow: 'hidden',
  },
  capacityFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 3,
  },
  capacityFillHigh: {
    backgroundColor: '#FF9800',
  },
  deadlineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  deadlineIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  deadlineText: {
    fontSize: 12,
    color: '#666',
  },
  applyButton: {
    backgroundColor: '#1B5E20',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  applyButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  waitlistInfo: {
    backgroundColor: '#FFF8E1',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  waitlistText: {
    color: '#F9A825',
    fontWeight: '600',
  },
  approvedInfo: {
    backgroundColor: '#E8F5E9',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  approvedText: {
    color: '#2E7D32',
    fontWeight: '600',
  },
  emptyContainer: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
});
