import { useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { useCropPlanningStore } from '@/store/crop-planning';
import { useAuthStore } from '@/store/auth';
import { COLORS } from '@/utils/constants';
import PlanCard from '@/components/crop-planning/PlanCard';
import type { CropPlanSummary, UpcomingActivity } from '@/types/crop-planning';
import { ACTIVITY_TYPE_ICONS } from '@/utils/constants';

export default function CropPlanningDashboard() {
  const user = useAuthStore((s) => s.user);
  const {
    dashboard,
    plans,
    fetchDashboard,
    fetchPlans,
    isLoading,
  } = useCropPlanningStore();

  useFocusEffect(
    useCallback(() => {
      if (user?.farmerId) {
        fetchDashboard(user.farmerId);
        fetchPlans({ farmerId: user.farmerId });
      }
    }, [user?.farmerId])
  );

  const activePlans = plans.filter((p) => p.status === 'active' || p.status === 'draft');

  const renderHeader = () => (
    <View>
      {/* Stats Row */}
      <View style={styles.statsRow} testID="cp-stats-row">
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{dashboard?.activePlansCount ?? 0}</Text>
          <Text style={styles.statLabel}>Active</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{dashboard?.draftPlansCount ?? 0}</Text>
          <Text style={styles.statLabel}>Drafts</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{dashboard?.completedPlansCount ?? 0}</Text>
          <Text style={styles.statLabel}>Done</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, (dashboard?.activitiesOverdue ?? 0) > 0 && { color: COLORS.error }]}>
            {dashboard?.activitiesOverdue ?? 0}
          </Text>
          <Text style={styles.statLabel}>Overdue</Text>
        </View>
      </View>

      {/* Alerts Banner */}
      {(dashboard?.alertsUnread ?? 0) > 0 && (
        <TouchableOpacity
          style={styles.alertBanner}
          onPress={() => router.push('/crop-planning/alerts')}
          testID="cp-alerts-banner"
        >
          <Text style={styles.alertBannerIcon}>🔔</Text>
          <Text style={styles.alertBannerText}>
            {dashboard!.alertsUnread} unread alert{dashboard!.alertsUnread > 1 ? 's' : ''}
          </Text>
          <Text style={styles.alertBannerArrow}>→</Text>
        </TouchableOpacity>
      )}

      {/* Upcoming Activities */}
      {(dashboard?.upcomingActivities?.length ?? 0) > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Upcoming Tasks</Text>
          {dashboard!.upcomingActivities.slice(0, 5).map((item: UpcomingActivity) => (
            <TouchableOpacity
              key={item.activity.id}
              style={styles.upcomingItem}
              onPress={() =>
                router.push({
                  pathname: `/crop-planning/${item.planId}/activity-complete`,
                  params: { activityId: item.activity.id },
                } as any)
              }
              testID={`cp-upcoming-${item.activity.id}`}
            >
              <Text style={styles.upcomingIcon}>
                {ACTIVITY_TYPE_ICONS[item.activity.activityType] || '📋'}
              </Text>
              <View style={styles.upcomingContent}>
                <Text style={styles.upcomingTitle} numberOfLines={1}>{item.activity.title}</Text>
                <Text style={styles.upcomingMeta}>{item.cropName} - {item.farmName}</Text>
              </View>
              <Text style={[styles.upcomingDue, item.isOverdue && { color: COLORS.error, fontWeight: '600' }]}>
                {item.daysUntil === 0 ? 'Today' : item.daysUntil < 0 ? `${Math.abs(item.daysUntil)}d late` : `${item.daysUntil}d`}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Plans Section Header */}
      <View style={styles.sectionRow}>
        <Text style={styles.sectionTitle}>Plans</Text>
        <Text style={styles.planCount}>{activePlans.length}</Text>
      </View>
    </View>
  );

  return (
    <View testID="cp-dashboard-screen" style={styles.container}>
      {isLoading && plans.length === 0 ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={styles.loader} />
      ) : (
        <FlatList
          data={activePlans}
          renderItem={({ item }) => (
            <PlanCard plan={item} testID={`cp-plan-${item.id}`} />
          )}
          keyExtractor={(item) => item.id}
          ListHeaderComponent={renderHeader}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={isLoading}
              onRefresh={() => {
                if (user?.farmerId) {
                  fetchDashboard(user.farmerId);
                  fetchPlans({ farmerId: user.farmerId });
                }
              }}
              colors={[COLORS.primary]}
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>🌱</Text>
              <Text style={styles.emptyText}>No crop plans yet</Text>
              <Text style={styles.emptySubtext}>Create your first crop plan to get started</Text>
            </View>
          }
        />
      )}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => router.push('/crop-planning/create')}
        testID="cp-fab-create"
      >
        <Text style={{ fontSize: 28, color: '#fff' }}>+</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  loader: { marginTop: 48 },
  list: { padding: 16 },
  statsRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 12,
    marginHorizontal: 3,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  statValue: { fontSize: 22, fontWeight: 'bold', color: COLORS.primary },
  statLabel: { fontSize: 11, color: '#666', marginTop: 2 },
  alertBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3E0',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
    borderLeftWidth: 3,
    borderLeftColor: '#FF9800',
  },
  alertBannerIcon: { fontSize: 18, marginRight: 8 },
  alertBannerText: { flex: 1, fontSize: 14, color: '#333', fontWeight: '500' },
  alertBannerArrow: { fontSize: 16, color: '#FF9800' },
  section: { marginBottom: 16 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 10 },
  sectionRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  planCount: { fontSize: 14, color: '#999' },
  upcomingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 12,
    marginBottom: 6,
  },
  upcomingIcon: { fontSize: 20, marginRight: 10 },
  upcomingContent: { flex: 1 },
  upcomingTitle: { fontSize: 14, fontWeight: '500', color: '#333' },
  upcomingMeta: { fontSize: 12, color: '#666', marginTop: 2 },
  upcomingDue: { fontSize: 12, color: '#999' },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 6,
  },
  emptyState: { alignItems: 'center', paddingVertical: 48 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#333' },
  emptySubtext: { fontSize: 13, color: '#666', marginTop: 4 },
});
