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
import { api } from '@/services/api';

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

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // In a real app, these would be actual API calls
      // For now, use mock data
      setSchemes([
        {
          id: '1',
          name: 'Agricultural Input Subsidy',
          code: 'AIS-2024',
          description: 'Government subsidy program for certified seeds and fertilizers',
          scheme_type: 'subsidy',
          status: 'active',
          benefit_type: 'voucher',
          benefit_amount: 15000,
          application_deadline: '2024-03-31',
          max_beneficiaries: 10000,
          current_beneficiaries: 7500,
        },
        {
          id: '2',
          name: 'Crop Insurance Program',
          code: 'CIP-2024',
          description: 'Weather-indexed crop insurance for smallholder farmers',
          scheme_type: 'insurance',
          status: 'active',
          benefit_type: 'service',
          benefit_amount: 50000,
          application_deadline: '2024-02-28',
          max_beneficiaries: 5000,
          current_beneficiaries: 2100,
        },
        {
          id: '3',
          name: 'Farm Mechanization Loan',
          code: 'FML-2024',
          description: 'Low-interest loans for farm equipment purchase',
          scheme_type: 'loan',
          status: 'active',
          benefit_type: 'cash',
          benefit_amount: 500000,
          application_deadline: '2024-06-30',
          max_beneficiaries: 1000,
          current_beneficiaries: 450,
        },
      ]);

      setMyAssessments([
        {
          id: 'a1',
          scheme_id: '1',
          status: 'approved',
          eligibility_score: 85,
          risk_level: 'low',
          final_decision: 'approved',
          waitlist_position: 0,
        },
      ]);
    } catch (error) {
      console.error('Error loading eligibility data:', error);
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

  const getStatusBadge = (status: string, assessment?: Assessment) => {
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
        <View style={[styles.badge, { backgroundColor: style.bg }]}>
          <Text style={[styles.badgeText, { color: style.text }]}>
            {assessment.status.replace('_', ' ').toUpperCase()}
          </Text>
        </View>
      );
    }
    return null;
  };

  const renderSchemeCard = (scheme: Scheme) => {
    const assessment = getAssessmentForScheme(scheme.id);
    const spotsLeft = scheme.max_beneficiaries - scheme.current_beneficiaries;
    const fillPercentage = (scheme.current_beneficiaries / scheme.max_beneficiaries) * 100;

    return (
      <TouchableOpacity
        key={scheme.id}
        style={styles.schemeCard}
        onPress={() => router.push(`/eligibility/${scheme.id}`)}
        testID={`scheme-card-${scheme.id}`}
      >
        <View style={styles.schemeHeader}>
          <View style={styles.schemeTypeTag}>
            <Text style={styles.schemeTypeText}>{scheme.scheme_type.toUpperCase()}</Text>
          </View>
          {getStatusBadge(scheme.status, assessment)}
        </View>

        <Text style={styles.schemeName}>{scheme.name}</Text>
        <Text style={styles.schemeCode}>{scheme.code}</Text>
        <Text style={styles.schemeDescription} numberOfLines={2}>
          {scheme.description}
        </Text>

        <View style={styles.benefitRow}>
          <Text style={styles.benefitLabel}>Benefit:</Text>
          <Text style={styles.benefitValue}>
            KES {scheme.benefit_amount.toLocaleString()} ({scheme.benefit_type})
          </Text>
        </View>

        <View style={styles.capacityContainer}>
          <View style={styles.capacityHeader}>
            <Text style={styles.capacityLabel}>Capacity</Text>
            <Text style={styles.capacityValue}>
              {spotsLeft.toLocaleString()} spots left
            </Text>
          </View>
          <View style={styles.capacityBar}>
            <View
              style={[
                styles.capacityFill,
                { width: `${fillPercentage}%` },
                fillPercentage > 90 && styles.capacityFillHigh,
              ]}
            />
          </View>
        </View>

        <View style={styles.deadlineRow}>
          <Text style={styles.deadlineIcon}>📅</Text>
          <Text style={styles.deadlineText}>
            Apply by: {new Date(scheme.application_deadline).toLocaleDateString()}
          </Text>
        </View>

        {!assessment && (
          <TouchableOpacity
            style={styles.applyButton}
            onPress={() => router.push(`/eligibility/${scheme.id}`)}
            testID={`apply-button-${scheme.id}`}
          >
            <Text style={styles.applyButtonText}>Check Eligibility</Text>
          </TouchableOpacity>
        )}

        {assessment && assessment.status === 'waitlisted' && (
          <View style={styles.waitlistInfo}>
            <Text style={styles.waitlistText}>
              Waitlist Position: #{assessment.waitlist_position}
            </Text>
          </View>
        )}

        {assessment && assessment.status === 'approved' && (
          <View style={styles.approvedInfo}>
            <Text style={styles.approvedText}>You are enrolled in this scheme</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1B5E20" />
        <Text style={styles.loadingText}>Loading schemes...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.title}>Eligibility & Schemes</Text>
        <Text style={styles.subtitle}>
          Check your eligibility for government and private agricultural programs
        </Text>
      </View>

      {/* Summary Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{schemes.length}</Text>
          <Text style={styles.statLabel}>Available Schemes</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>
            {myAssessments.filter((a) => a.status === 'approved').length}
          </Text>
          <Text style={styles.statLabel}>Enrolled</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>
            {myAssessments.filter((a) => a.status === 'pending' || a.status === 'eligible').length}
          </Text>
          <Text style={styles.statLabel}>Pending</Text>
        </View>
      </View>

      {/* Scheme Cards */}
      <View style={styles.schemesSection}>
        <Text style={styles.sectionTitle}>Available Programs</Text>
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
});
