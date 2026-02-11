import { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { useCropPlanningStore } from '@/store/crop-planning';
import { useAuthStore } from '@/store/auth';
import { COLORS, ALERT_SEVERITY_COLORS } from '@/utils/constants';
import type { CropPlanAlert } from '@/types/crop-planning';

const SEVERITY_ICONS: Record<string, string> = {
  info: 'i',
  warning: '!',
  critical: '!!',
};

const ALERT_TYPE_ICONS: Record<string, string> = {
  activity_reminder: '📋',
  activity_overdue: '⏰',
  weather_warning: '🌧️',
  planting_window: '🌱',
  irrigation_reminder: '💧',
  input_reminder: '📦',
  stage_transition: '📈',
  harvest_reminder: '🌽',
};

type FilterMode = 'all' | 'unread';

function getTimeAgo(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffWeeks = Math.floor(diffDays / 7);

  if (diffSeconds < 60) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffWeeks < 4) return `${diffWeeks}w ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function AlertsScreen() {
  const user = useAuthStore((s) => s.user);
  const {
    alerts,
    unreadAlertCount,
    fetchAlerts,
    markAlertRead,
    dismissAlert,
    isLoading,
  } = useCropPlanningStore();

  const [filter, setFilter] = useState<FilterMode>('all');

  useFocusEffect(
    useCallback(() => {
      if (user?.farmerId) {
        fetchAlerts(user.farmerId);
      }
    }, [user?.farmerId])
  );

  const filteredAlerts =
    filter === 'unread' ? alerts.filter((a) => !a.readAt) : alerts;

  const handleMarkAllRead = async () => {
    const unreadAlerts = alerts.filter((a) => !a.readAt);
    for (const alert of unreadAlerts) {
      await markAlertRead(alert.id);
    }
  };

  const handleAlertPress = async (alert: CropPlanAlert) => {
    if (!alert.readAt) {
      await markAlertRead(alert.id);
    }
    if (alert.cropPlanId) {
      router.push(`/crop-planning/${alert.cropPlanId}`);
    }
  };

  const handleDismiss = async (alertId: string) => {
    await dismissAlert(alertId);
  };

  const renderAlertCard = ({ item }: { item: CropPlanAlert }) => {
    const isUnread = !item.readAt;
    const severityColor = ALERT_SEVERITY_COLORS[item.severity] || COLORS.gray[400];
    const typeIcon = ALERT_TYPE_ICONS[item.alertType] || '📋';
    const timeAgo = item.sentAt ? getTimeAgo(item.sentAt) : getTimeAgo(item.createdAt);

    return (
      <TouchableOpacity
        style={[styles.alertCard, isUnread && styles.alertCardUnread]}
        onPress={() => handleAlertPress(item)}
        testID={`cp-alerts-card-${item.id}`}
      >
        <View style={[styles.severityBar, { backgroundColor: severityColor }]} />
        <View style={styles.alertContent}>
          <View style={styles.alertTopRow}>
            <View style={styles.alertIconContainer}>
              <Text style={styles.alertTypeIcon}>{typeIcon}</Text>
              <View style={[styles.severityDot, { backgroundColor: severityColor }]}>
                <Text style={styles.severityDotText}>
                  {SEVERITY_ICONS[item.severity] || ''}
                </Text>
              </View>
            </View>
            <View style={styles.alertTitleContainer}>
              <Text
                style={[styles.alertTitle, isUnread && styles.alertTitleUnread]}
                numberOfLines={1}
                testID={`cp-alerts-title-${item.id}`}
              >
                {item.title}
              </Text>
              <Text style={styles.alertTime} testID={`cp-alerts-time-${item.id}`}>
                {timeAgo}
              </Text>
            </View>
          </View>
          <Text
            style={styles.alertMessage}
            numberOfLines={2}
            testID={`cp-alerts-message-${item.id}`}
          >
            {item.message}
          </Text>
          <View style={styles.alertBottomRow}>
            <View style={[styles.severityBadge, { backgroundColor: `${severityColor}18` }]}>
              <Text style={[styles.severityBadgeText, { color: severityColor }]}>
                {item.severity.charAt(0).toUpperCase() + item.severity.slice(1)}
              </Text>
            </View>
            {isUnread && (
              <View style={styles.unreadIndicator} testID={`cp-alerts-unread-${item.id}`}>
                <View style={styles.unreadDot} />
              </View>
            )}
            <TouchableOpacity
              style={styles.dismissButton}
              onPress={() => handleDismiss(item.id)}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              testID={`cp-alerts-dismiss-${item.id}`}
            >
              <Text style={styles.dismissText}>Dismiss</Text>
            </TouchableOpacity>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyContainer} testID="cp-alerts-empty">
      <Text style={styles.emptyIcon}>🔔</Text>
      <Text style={styles.emptyTitle}>
        {filter === 'unread' ? 'No Unread Alerts' : 'No Alerts'}
      </Text>
      <Text style={styles.emptySubtitle}>
        {filter === 'unread'
          ? 'All your alerts have been read. Switch to "All" to see previous alerts.'
          : 'You have no alerts at the moment. Alerts will appear here when your crop plans need attention.'}
      </Text>
    </View>
  );

  if (isLoading && alerts.length === 0) {
    return (
      <View style={styles.loadingContainer} testID="cp-alerts-loading">
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Loading alerts...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container} testID="cp-alerts-screen">
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>Alerts</Text>
          {unreadAlertCount > 0 && (
            <View style={styles.unreadCountBadge} testID="cp-alerts-unread-count">
              <Text style={styles.unreadCountText}>{unreadAlertCount}</Text>
            </View>
          )}
        </View>
        {unreadAlertCount > 0 && (
          <TouchableOpacity
            onPress={handleMarkAllRead}
            testID="cp-alerts-mark-all-read"
          >
            <Text style={styles.markAllReadText}>Mark all read</Text>
          </TouchableOpacity>
        )}
      </View>
      <View style={styles.filterRow} testID="cp-alerts-filter">
        <TouchableOpacity
          style={[styles.filterButton, filter === 'all' && styles.filterButtonActive]}
          onPress={() => setFilter('all')}
          testID="cp-alerts-filter-all"
        >
          <Text
            style={[styles.filterButtonText, filter === 'all' && styles.filterButtonTextActive]}
          >
            All
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterButton, filter === 'unread' && styles.filterButtonActive]}
          onPress={() => setFilter('unread')}
          testID="cp-alerts-filter-unread"
        >
          <Text
            style={[
              styles.filterButtonText,
              filter === 'unread' && styles.filterButtonTextActive,
            ]}
          >
            Unread
            {unreadAlertCount > 0 ? ` (${unreadAlertCount})` : ''}
          </Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={filteredAlerts}
        renderItem={renderAlertCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={renderEmptyState}
        showsVerticalScrollIndicator={false}
        testID="cp-alerts-list"
      />
      {isLoading && alerts.length > 0 && (
        <View style={styles.refreshIndicator} testID="cp-alerts-refreshing">
          <ActivityIndicator size="small" color={COLORS.primary} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  loadingContainer: { flex: 1, backgroundColor: '#f5f5f5', justifyContent: 'center', alignItems: 'center' },
  loadingText: { marginTop: 12, fontSize: 16, color: COLORS.gray[600] },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[200],
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: COLORS.gray[900] },
  unreadCountBadge: {
    backgroundColor: COLORS.error,
    borderRadius: 12,
    minWidth: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  unreadCountText: { color: COLORS.white, fontSize: 12, fontWeight: 'bold' },
  markAllReadText: { fontSize: 14, color: COLORS.primary, fontWeight: '600' },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: COLORS.white,
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[100],
  },
  filterButton: { paddingHorizontal: 20, paddingVertical: 8, borderRadius: 20, backgroundColor: COLORS.gray[100] },
  filterButtonActive: { backgroundColor: COLORS.primary },
  filterButtonText: { fontSize: 14, fontWeight: '500', color: COLORS.gray[600] },
  filterButtonTextActive: { color: COLORS.white },
  listContent: { padding: 16, paddingBottom: 32 },
  alertCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.white,
    borderRadius: 12,
    marginBottom: 10,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  alertCardUnread: { backgroundColor: '#F1F8E9', shadowOpacity: 0.1 },
  severityBar: { width: 4 },
  alertContent: { flex: 1, padding: 14 },
  alertTopRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 6 },
  alertIconContainer: { position: 'relative', marginRight: 10 },
  alertTypeIcon: { fontSize: 22 },
  severityDot: {
    position: 'absolute',
    bottom: -2,
    right: -4,
    width: 14,
    height: 14,
    borderRadius: 7,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: COLORS.white,
  },
  severityDotText: { fontSize: 7, fontWeight: 'bold', color: COLORS.white },
  alertTitleContainer: { flex: 1, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  alertTitle: { fontSize: 15, fontWeight: '500', color: COLORS.gray[800], flex: 1, marginRight: 8 },
  alertTitleUnread: { fontWeight: '700', color: COLORS.gray[900] },
  alertTime: { fontSize: 12, color: COLORS.gray[500] },
  alertMessage: { fontSize: 13, color: COLORS.gray[600], lineHeight: 19, marginBottom: 10, marginLeft: 32 },
  alertBottomRow: { flexDirection: 'row', alignItems: 'center', marginLeft: 32 },
  severityBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  severityBadgeText: { fontSize: 11, fontWeight: '600' },
  unreadIndicator: { marginLeft: 8 },
  unreadDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: COLORS.primaryLight },
  dismissButton: {
    marginLeft: 'auto',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
  },
  dismissText: { fontSize: 12, color: COLORS.gray[600], fontWeight: '500' },
  emptyContainer: { alignItems: 'center', paddingTop: 80, paddingHorizontal: 32 },
  emptyIcon: { fontSize: 56, marginBottom: 16 },
  emptyTitle: { fontSize: 20, fontWeight: 'bold', color: COLORS.gray[800], marginBottom: 8 },
  emptySubtitle: { fontSize: 14, color: COLORS.gray[500], textAlign: 'center', lineHeight: 21 },
  refreshIndicator: {
    position: 'absolute',
    top: 120,
    alignSelf: 'center',
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
});
