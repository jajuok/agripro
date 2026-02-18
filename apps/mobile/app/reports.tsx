import { useState, useEffect, useCallback } from 'react';
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
import { farmApi, kycApi, cropPlanningApi, taskApi } from '@/services/api';

type FarmData = {
  farmCount: number;
  totalAcreage: number;
  activeCrops: number;
};

type CropData = {
  activePlans: number;
  completedPlans: number;
  draftPlans: number;
  totalPlans: number;
  overdueActivities: number;
  plannedAcreage: number;
  activitiesThisWeek: number;
};

type TaskData = {
  total: number;
  completed: number;
  overdue: number;
  inProgress: number;
  pending: number;
};

type KycData = {
  status: string;
  steps: { name: string; completed: boolean }[];
};

export default function ReportsScreen() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [farmData, setFarmData] = useState<FarmData>({ farmCount: 0, totalAcreage: 0, activeCrops: 0 });
  const [cropData, setCropData] = useState<CropData>({ activePlans: 0, completedPlans: 0, draftPlans: 0, totalPlans: 0, overdueActivities: 0, plannedAcreage: 0, activitiesThisWeek: 0 });
  const [taskData, setTaskData] = useState<TaskData>({ total: 0, completed: 0, overdue: 0, inProgress: 0, pending: 0 });
  const [kycData, setKycData] = useState<KycData>({ status: 'Not Started', steps: [] });

  const fetchData = useCallback(async () => {
    const farmerId = user?.farmerId;
    if (!farmerId) {
      setLoading(false);
      return;
    }

    try {
      const [farmsResult, cropResult, taskResult, kycResult] = await Promise.allSettled([
        farmApi.list(farmerId),
        cropPlanningApi.getDashboard(farmerId),
        taskApi.getStats(farmerId),
        kycApi.getStatus(farmerId),
      ]);

      // Farms
      if (farmsResult.status === 'fulfilled') {
        const farms = Array.isArray(farmsResult.value) ? farmsResult.value : [];
        const totalAcreage = farms.reduce((sum: number, f: any) => sum + (f.total_acreage || f.cultivable_acreage || 0), 0);
        const cropSet = new Set<string>();
        farms.forEach((f: any) => {
          if (f.primary_crop) cropSet.add(f.primary_crop);
          if (f.crops && Array.isArray(f.crops)) f.crops.forEach((c: string) => cropSet.add(c));
        });
        setFarmData({
          farmCount: farms.length,
          totalAcreage: Math.round(totalAcreage * 10) / 10,
          activeCrops: cropSet.size || farms.length,
        });
      }

      // Crop planning
      if (cropResult.status === 'fulfilled') {
        const d = cropResult.value || {};
        const active = d.active_plans || 0;
        const completed = d.completed_plans || 0;
        const draft = d.draft_plans || 0;
        setCropData({
          activePlans: active,
          completedPlans: completed,
          draftPlans: draft,
          totalPlans: active + completed + draft,
          overdueActivities: d.overdue_activities || d.activities_overdue || 0,
          plannedAcreage: d.total_planned_acreage || d.planned_acreage || 0,
          activitiesThisWeek: d.activities_this_week || d.upcoming_activities || 0,
        });
      }

      // Tasks
      if (taskResult.status === 'fulfilled') {
        const t = taskResult.value || {};
        setTaskData({
          total: t.total || t.total_tasks || 0,
          completed: t.completed || t.completed_tasks || 0,
          overdue: t.overdue || t.overdue_tasks || 0,
          inProgress: t.in_progress || t.in_progress_tasks || 0,
          pending: t.pending || t.pending_tasks || 0,
        });
      }

      // KYC
      if (kycResult.status === 'fulfilled') {
        const k = kycResult.value || {};
        const status = k.status || k.kyc_status || 'Not Started';
        const steps = (k.steps || k.completed_steps || []).map((s: any) => {
          if (typeof s === 'string') return { name: s, completed: true };
          return { name: s.name || s.step, completed: s.completed ?? s.status === 'completed' };
        });
        setKycData({ status, steps });
      }
    } catch {
      // Keep defaults on error
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.farmerId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchData();
  }, [fetchData]);

  const getKycStatusStyle = (status: string) => {
    const lower = status.toLowerCase();
    if (['verified', 'approved', 'completed'].includes(lower)) {
      return { bg: '#E8F5E9', text: '#2E7D32', label: 'Verified' };
    }
    if (['pending', 'in_progress', 'in progress', 'submitted'].includes(lower)) {
      return { bg: '#FFF3E0', text: '#EF6C00', label: 'In Progress' };
    }
    return { bg: '#F5F5F5', text: '#666', label: 'Not Started' };
  };

  const cropCompletionRate = cropData.totalPlans > 0
    ? Math.round((cropData.completedPlans / cropData.totalPlans) * 100)
    : 0;

  const taskCompletionRate = taskData.total > 0
    ? Math.round((taskData.completed / taskData.total) * 100)
    : 0;

  const kycStyle = getKycStatusStyle(kycData.status);

  if (loading) {
    return (
      <View style={styles.loadingContainer} testID="reports-loading">
        <ActivityIndicator size="large" color="#1B5E20" />
        <Text style={styles.loadingText}>Loading reports...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      testID="reports-screen"
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
          testID="reports-back-button"
        >
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Reports</Text>
        <Text style={styles.subtitle}>Farm management overview</Text>
      </View>

      {/* Section 1: Farm Summary */}
      <View style={styles.section} testID="reports-farm-section">
        <Text style={styles.sectionTitle}>Farm Summary</Text>
        <View style={styles.statsRow}>
          <View style={styles.statCard} testID="reports-farm-stat-count">
            <Text style={styles.statValue}>{farmData.farmCount}</Text>
            <Text style={styles.statLabel}>Total Farms</Text>
          </View>
          <View style={styles.statCard} testID="reports-farm-stat-acreage">
            <Text style={styles.statValue}>{farmData.totalAcreage}</Text>
            <Text style={styles.statLabel}>Acreage (ha)</Text>
          </View>
          <View style={styles.statCard} testID="reports-farm-stat-crops">
            <Text style={styles.statValue}>{farmData.activeCrops}</Text>
            <Text style={styles.statLabel}>Active Crops</Text>
          </View>
        </View>
      </View>

      {/* Section 2: Crop Planning */}
      <View style={styles.section} testID="reports-crop-section">
        <Text style={styles.sectionTitle}>Crop Planning</Text>
        <View style={styles.statsRow}>
          <View style={styles.statCard} testID="reports-crop-stat-active">
            <Text style={styles.statValue}>{cropData.activePlans}</Text>
            <Text style={styles.statLabel}>Active Plans</Text>
          </View>
          <View style={styles.statCard} testID="reports-crop-stat-completed">
            <Text style={styles.statValue}>{cropData.completedPlans}</Text>
            <Text style={styles.statLabel}>Completed</Text>
          </View>
          <View style={styles.statCard} testID="reports-crop-stat-overdue">
            <Text style={[styles.statValue, cropData.overdueActivities > 0 && { color: '#F44336' }]}>
              {cropData.overdueActivities}
            </Text>
            <Text style={styles.statLabel}>Overdue</Text>
          </View>
        </View>
        <View style={styles.progressContainer} testID="reports-crop-progress">
          <View style={styles.progressHeader}>
            <Text style={styles.progressLabel}>Plan Completion</Text>
            <Text style={styles.progressValue}>{cropCompletionRate}%</Text>
          </View>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${cropCompletionRate}%` }]} />
          </View>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailText}>Planned Acreage: {cropData.plannedAcreage} ha</Text>
          <Text style={styles.detailText}>Due This Week: {cropData.activitiesThisWeek}</Text>
        </View>
      </View>

      {/* Section 3: Task Overview */}
      <View style={styles.section} testID="reports-task-section">
        <Text style={styles.sectionTitle}>Task Overview</Text>
        <View style={styles.statsRow}>
          <View style={styles.statCard} testID="reports-task-stat-total">
            <Text style={styles.statValue}>{taskData.total}</Text>
            <Text style={styles.statLabel}>Total Tasks</Text>
          </View>
          <View style={styles.statCard} testID="reports-task-stat-completed">
            <Text style={styles.statValue}>{taskData.completed}</Text>
            <Text style={styles.statLabel}>Completed</Text>
          </View>
          <View style={styles.statCard} testID="reports-task-stat-overdue">
            <Text style={[styles.statValue, taskData.overdue > 0 && { color: '#F44336' }]}>
              {taskData.overdue}
            </Text>
            <Text style={styles.statLabel}>Overdue</Text>
          </View>
        </View>
        <View style={styles.progressContainer} testID="reports-task-progress">
          <View style={styles.progressHeader}>
            <Text style={styles.progressLabel}>Task Completion</Text>
            <Text style={styles.progressValue}>{taskCompletionRate}%</Text>
          </View>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${taskCompletionRate}%` }]} />
          </View>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailText}>In Progress: {taskData.inProgress}</Text>
          <Text style={styles.detailText}>Pending: {taskData.pending}</Text>
        </View>
      </View>

      {/* Section 4: KYC & Compliance */}
      <View style={[styles.section, { marginBottom: 32 }]} testID="reports-kyc-section">
        <Text style={styles.sectionTitle}>KYC & Compliance</Text>
        <View style={styles.kycCard}>
          <View style={styles.kycRow} testID="reports-kyc-status">
            <View style={[styles.kycBadge, { backgroundColor: kycStyle.bg }]}>
              <Text style={[styles.kycBadgeText, { color: kycStyle.text }]}>{kycStyle.label}</Text>
            </View>
          </View>
          {kycData.steps.length > 0 && (
            <View style={styles.stepsContainer}>
              {kycData.steps.map((step, i) => (
                <View key={i} style={styles.stepRow}>
                  <Text style={styles.stepIcon}>{step.completed ? '✅' : '⬜'}</Text>
                  <Text style={styles.stepName}>{step.name}</Text>
                </View>
              ))}
            </View>
          )}
          {kycData.steps.length === 0 && kycStyle.label === 'Not Started' && (
            <Text style={styles.kycHint}>Complete your KYC verification to unlock full access.</Text>
          )}
        </View>
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
  section: {
    padding: 16,
    paddingBottom: 0,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statValue: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1B5E20',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    textAlign: 'center',
  },
  progressContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressLabel: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
  },
  progressValue: {
    fontSize: 14,
    color: '#1B5E20',
    fontWeight: '600',
  },
  progressBar: {
    height: 6,
    backgroundColor: '#E0E0E0',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 3,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  detailText: {
    fontSize: 13,
    color: '#666',
  },
  kycCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  kycRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  kycBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  kycBadgeText: {
    fontSize: 14,
    fontWeight: '600',
  },
  stepsContainer: {
    marginTop: 12,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
  },
  stepIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  stepName: {
    fontSize: 14,
    color: '#333',
    textTransform: 'capitalize',
  },
  kycHint: {
    marginTop: 12,
    fontSize: 13,
    color: '#999',
  },
});
