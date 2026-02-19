import { useState, useEffect, useCallback, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, RefreshControl } from 'react-native';
import { router } from 'expo-router';
import { useAuthStore } from '@/store/auth';
import { farmApi, kycApi, cropPlanningApi, notificationApi } from '@/services/api';

type QuickAction = {
  icon: string;
  label: string;
  route: string;
  color: string;
  testID: string;
};

const quickActions: QuickAction[] = [
  { icon: '🌱', label: 'Crop Plans', route: '/crop-planning', color: '#4CAF50', testID: 'home-action-crop-planning' },
  { icon: '➕', label: 'Add Farm', route: '/farms/add', color: '#2196F3', testID: 'home-action-add-farm' },
  { icon: '📋', label: 'Eligibility', route: '/eligibility', color: '#FF9800', testID: 'home-action-check-eligibility' },
  { icon: '📊', label: 'Reports', route: '/reports', color: '#9C27B0', testID: 'home-action-view-reports' },
];

type DashboardData = {
  farmCount: number;
  totalHectares: number;
  activeCrops: number;
  kycStatus: string;
  kycVerified: boolean;
  upcomingActivities: { name: string; due: string; icon: string }[];
};

export default function HomeScreen() {
  const { user } = useAuthStore();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDashboard = useCallback(async () => {
    const farmerId = user?.farmerId;
    if (!farmerId) {
      setData({
        farmCount: 0,
        totalHectares: 0,
        activeCrops: 0,
        kycStatus: 'Not Started',
        kycVerified: false,
        upcomingActivities: [],
      });
      setLoading(false);
      return;
    }

    try {
      const [farmsResult, kycResult, dashboardResult, activitiesResult] = await Promise.allSettled([
        farmApi.list(farmerId),
        kycApi.getStatus(farmerId),
        cropPlanningApi.getDashboard(farmerId),
        cropPlanningApi.getUpcomingActivities(farmerId, 7),
      ]);

      // Farms
      const farms = farmsResult.status === 'fulfilled' ? (Array.isArray(farmsResult.value) ? farmsResult.value : []) : [];
      const totalHectares = farms.reduce((sum: number, f: any) => sum + (f.total_acreage || f.cultivable_acreage || 0), 0);

      // KYC
      const kyc = kycResult.status === 'fulfilled' ? kycResult.value : null;
      const kycStatus = kyc?.status || kyc?.kyc_status || 'Not Started';
      const kycVerified = ['verified', 'approved', 'completed'].includes(kycStatus.toLowerCase());

      // Crop dashboard
      const dashboard = dashboardResult.status === 'fulfilled' ? dashboardResult.value : null;
      const activeCrops = dashboard?.active_plans || dashboard?.active_crops || 0;

      // Upcoming activities
      const rawActivities = activitiesResult.status === 'fulfilled'
        ? (Array.isArray(activitiesResult.value) ? activitiesResult.value : activitiesResult.value?.items || [])
        : [];
      const upcomingActivities = rawActivities.slice(0, 5).map((a: any) => {
        const dueDate = a.scheduled_date || a.due_date || a.planned_date || '';
        const today = new Date().toISOString().split('T')[0];
        const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
        let due = dueDate;
        if (dueDate === today) due = 'Due today';
        else if (dueDate === tomorrow) due = 'Due tomorrow';
        else if (dueDate) due = `Due ${dueDate}`;

        const type = (a.activity_type || a.name || a.title || '').toLowerCase();
        let icon = '📋';
        if (type.includes('irrig') || type.includes('water')) icon = '💧';
        else if (type.includes('fertil') || type.includes('nutrient')) icon = '🧪';
        else if (type.includes('harvest')) icon = '🌾';
        else if (type.includes('plant') || type.includes('sow')) icon = '🌱';
        else if (type.includes('spray') || type.includes('pest')) icon = '🔬';
        else if (type.includes('weed')) icon = '🌿';

        return {
          name: a.name || a.title || a.activity_type || 'Task',
          due,
          icon,
        };
      });

      setData({
        farmCount: farms.length,
        totalHectares: Math.round(totalHectares * 10) / 10,
        activeCrops,
        kycStatus,
        kycVerified,
        upcomingActivities,
      });
    } catch {
      setData({
        farmCount: 0,
        totalHectares: 0,
        activeCrops: 0,
        kycStatus: 'Unknown',
        kycVerified: false,
        upcomingActivities: [],
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.farmerId]);

  const fetchUnreadCount = useCallback(async () => {
    const userId = user?.id;
    if (!userId) return;
    try {
      const result = await notificationApi.getUnreadCount(userId);
      setUnreadCount(result.unread_count || 0);
    } catch {}
  }, [user?.id]);

  useEffect(() => {
    fetchDashboard();
    fetchUnreadCount();

    // Refresh unread count every 60 seconds
    intervalRef.current = setInterval(fetchUnreadCount, 60000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchDashboard, fetchUnreadCount]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchDashboard();
    fetchUnreadCount();
  }, [fetchDashboard, fetchUnreadCount]);

  const firstName = user?.firstName || 'Farmer';

  return (
    <ScrollView
      style={styles.container}
      testID="home-screen"
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#fff" />}
    >
      <View style={styles.header} testID="home-header">
        <View style={styles.headerRow}>
          <View style={styles.headerTextContainer}>
            <Text style={styles.greeting} testID="home-greeting">Welcome back, {firstName}!</Text>
            <Text style={styles.subGreeting} testID="home-sub-greeting">Here's your farm overview</Text>
          </View>
          <TouchableOpacity
            style={styles.bellButton}
            onPress={() => router.push('/notifications')}
            testID="home-bell-button"
          >
            <Text style={styles.bellIcon}>🔔</Text>
            {unreadCount > 0 && (
              <View style={styles.badge} testID="home-bell-badge">
                <Text style={styles.badgeText}>
                  {unreadCount > 99 ? '99+' : unreadCount}
                </Text>
              </View>
            )}
          </TouchableOpacity>
        </View>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1B5E20" />
        </View>
      ) : (
        <>
          <View style={styles.statsContainer} testID="home-stats-container">
            <View style={styles.statCard} testID="home-stat-farms">
              <Text style={styles.statValue} testID="home-stat-farms-value">{data?.farmCount ?? 0}</Text>
              <Text style={styles.statLabel} testID="home-stat-farms-label">Farms</Text>
            </View>
            <View style={styles.statCard} testID="home-stat-hectares">
              <Text style={styles.statValue} testID="home-stat-hectares-value">{data?.totalHectares ?? 0}</Text>
              <Text style={styles.statLabel} testID="home-stat-hectares-label">Hectares</Text>
            </View>
            <View style={styles.statCard} testID="home-stat-crops">
              <Text style={styles.statValue} testID="home-stat-crops-value">{data?.activeCrops ?? 0}</Text>
              <Text style={styles.statLabel} testID="home-stat-crops-label">Active Crops</Text>
            </View>
          </View>

          <Text style={styles.sectionTitle} testID="home-section-quick-actions">Quick Actions</Text>
          <View style={styles.actionsGrid} testID="home-actions-grid">
            {quickActions.map((action, index) => (
              <TouchableOpacity
                key={index}
                style={styles.actionCard}
                onPress={() => router.push(action.route as any)}
                testID={action.testID}
              >
                <View style={[styles.actionIcon, { backgroundColor: action.color }]}>
                  <Text style={{ fontSize: 24 }}>{action.icon}</Text>
                </View>
                <Text style={styles.actionLabel}>{action.label}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.sectionTitle} testID="home-section-kyc">KYC Status</Text>
          <View style={styles.kycCard} testID="home-kyc-card">
            <View style={styles.kycHeader}>
              <Text style={{ fontSize: 24 }}>{data?.kycVerified ? '✅' : '⚠️'}</Text>
              <Text style={[styles.kycStatus, !data?.kycVerified && { color: '#FF9800' }]} testID="home-kyc-status">
                {data?.kycVerified ? 'Verified' : data?.kycStatus || 'Not Started'}
              </Text>
            </View>
            <Text style={styles.kycText} testID="home-kyc-text">
              {data?.kycVerified
                ? 'Your KYC verification is complete. You have full access to all features.'
                : 'Complete your KYC verification to access all features.'}
            </Text>
            {!data?.kycVerified && (
              <TouchableOpacity style={styles.kycButton} onPress={() => router.push('/kyc')}>
                <Text style={styles.kycButtonText}>Complete KYC</Text>
              </TouchableOpacity>
            )}
          </View>

          <Text style={styles.sectionTitle} testID="home-section-eligibility">Scheme Eligibility Criteria</Text>
          <TouchableOpacity
            style={styles.eligibilityCard}
            onPress={() => router.push('/eligibility')}
            testID="home-eligibility-card"
          >
            <View style={styles.eligibilityHeader}>
              <Text style={{ fontSize: 24 }}>📋</Text>
              <View style={styles.eligibilityInfo}>
                <Text style={styles.eligibilityTitle} testID="home-eligibility-title">Check Eligibility</Text>
                <Text style={styles.eligibilitySubtitle} testID="home-eligibility-subtitle">Browse available government programs</Text>
              </View>
            </View>
          </TouchableOpacity>

          <Text style={styles.sectionTitle} testID="home-section-tasks">Upcoming Activities</Text>
          <View style={styles.taskCard} testID="home-tasks-card">
            {data?.upcomingActivities && data.upcomingActivities.length > 0 ? (
              data.upcomingActivities.map((activity, index) => (
                <View key={index} style={styles.taskItem}>
                  <Text style={{ fontSize: 20 }}>{activity.icon}</Text>
                  <View style={styles.taskContent}>
                    <Text style={styles.taskTitle}>{activity.name}</Text>
                    <Text style={styles.taskDue}>{activity.due}</Text>
                  </View>
                </View>
              ))
            ) : (
              <Text style={styles.emptyText}>No upcoming activities</Text>
            )}
          </View>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#1B5E20',
    padding: 24,
    paddingTop: 16,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  headerTextContainer: {
    flex: 1,
  },
  bellButton: {
    padding: 4,
    position: 'relative',
  },
  bellIcon: {
    fontSize: 24,
    color: '#fff',
  },
  badge: {
    position: 'absolute',
    top: -2,
    right: -4,
    backgroundColor: '#F44336',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: 'bold',
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  subGreeting: {
    fontSize: 14,
    color: '#C8E6C9',
    marginTop: 4,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 16,
    marginTop: -20,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 4,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
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
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    paddingHorizontal: 16,
    paddingTop: 24,
    paddingBottom: 12,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 12,
  },
  actionCard: {
    width: '25%',
    alignItems: 'center',
    padding: 8,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionLabel: {
    fontSize: 12,
    color: '#333',
    marginTop: 8,
    textAlign: 'center',
  },
  kycCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
  },
  kycHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  kycStatus: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4CAF50',
    marginLeft: 8,
  },
  kycText: {
    fontSize: 14,
    color: '#666',
  },
  kycButton: {
    backgroundColor: '#1B5E20',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignSelf: 'flex-start',
    marginTop: 12,
  },
  kycButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  taskCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  taskItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  taskContent: {
    marginLeft: 12,
    flex: 1,
  },
  taskTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
  },
  taskDue: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  emptyText: {
    color: '#999',
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 12,
  },
  eligibilityCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#2196F3',
  },
  eligibilityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  eligibilityInfo: {
    marginLeft: 12,
    flex: 1,
  },
  eligibilityTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  eligibilitySubtitle: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
});
