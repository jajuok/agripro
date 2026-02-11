import { useCallback } from 'react';
import { View, Text, StyleSheet, SectionList, TouchableOpacity, ActivityIndicator } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { useCropPlanningStore } from '@/store/crop-planning';
import { useAuthStore } from '@/store/auth';
import { ACTIVITY_TYPE_ICONS, COLORS } from '@/utils/constants';
import type { UpcomingActivity } from '@/types/crop-planning';

const priorityColors = {
  high: '#D32F2F',
  medium: '#FF9800',
  low: '#4CAF50',
};

function getPriorityLevel(priority: number): 'high' | 'medium' | 'low' {
  if (priority <= 3) return 'high';
  if (priority <= 6) return 'medium';
  return 'low';
}

function getDueLabel(daysUntil: number): string {
  if (daysUntil < 0) return `${Math.abs(daysUntil)}d overdue`;
  if (daysUntil === 0) return 'Today';
  if (daysUntil === 1) return 'Tomorrow';
  if (daysUntil <= 7) return `In ${daysUntil} days`;
  return `In ${Math.ceil(daysUntil / 7)} weeks`;
}

export default function TasksScreen() {
  const user = useAuthStore((s) => s.user);
  const { upcomingActivities, fetchUpcomingActivities, isLoading } = useCropPlanningStore();

  useFocusEffect(
    useCallback(() => {
      if (user?.farmerId) fetchUpcomingActivities(user.farmerId, 14);
    }, [user?.farmerId])
  );

  const todayItems = upcomingActivities.filter((a) => a.daysUntil <= 0);
  const upcomingItems = upcomingActivities.filter((a) => a.daysUntil > 0);

  const sections = [
    { title: 'Today', data: todayItems },
    { title: 'Upcoming', data: upcomingItems },
  ].filter((s) => s.data.length > 0);

  const renderTask = ({ item }: { item: UpcomingActivity }) => {
    const icon = ACTIVITY_TYPE_ICONS[item.activity.activityType] || '📋';
    const priority = getPriorityLevel(item.activity.priority);
    const isCompleted = item.activity.status === 'completed';

    return (
      <TouchableOpacity
        style={styles.taskCard}
        onPress={() =>
          router.push({
            pathname: `/crop-planning/${item.planId}/activity-complete`,
            params: { activityId: item.activity.id },
          } as any)
        }
        testID={`tasks-item-${item.activity.id}`}
      >
        <View style={styles.iconContainer}>
          <Text style={{ fontSize: 24 }}>{icon}</Text>
        </View>
        <View style={styles.taskContent}>
          <Text style={[styles.taskTitle, isCompleted && styles.completedTask]} numberOfLines={1}>
            {item.activity.title}
          </Text>
          <Text style={styles.taskFarm}>{item.cropName} - {item.farmName}</Text>
        </View>
        <View style={styles.taskMeta}>
          <View style={[styles.priorityDot, { backgroundColor: priorityColors[priority] }]} />
          <Text style={[styles.taskDue, item.isOverdue && styles.taskOverdue]}>
            {getDueLabel(item.daysUntil)}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View testID="tasks-screen" style={styles.container}>
      {isLoading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={styles.loader} />
      ) : (
        <SectionList
          sections={sections}
          renderItem={renderTask}
          renderSectionHeader={({ section }) => (
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>{section.title}</Text>
              <Text style={styles.sectionCount}>{section.data.length} tasks</Text>
            </View>
          )}
          keyExtractor={(item) => item.activity.id}
          contentContainerStyle={styles.list}
          stickySectionHeadersEnabled={false}
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>✅</Text>
              <Text style={styles.emptyText}>No tasks</Text>
              <Text style={styles.emptySubtext}>Create a crop plan to generate farming tasks</Text>
            </View>
          }
        />
      )}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => router.push('/crop-planning/create')}
        testID="tasks-fab-create"
      >
        <Text style={{ fontSize: 28, color: '#fff' }}>+</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loader: { marginTop: 48 },
  list: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  sectionCount: {
    fontSize: 14,
    color: '#999',
  },
  taskCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  iconContainer: {
    marginRight: 12,
  },
  taskContent: {
    flex: 1,
  },
  taskTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  completedTask: {
    textDecorationLine: 'line-through',
    color: '#999',
  },
  taskFarm: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  taskMeta: {
    alignItems: 'flex-end',
  },
  priorityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginBottom: 4,
  },
  taskDue: {
    fontSize: 12,
    color: '#999',
  },
  taskOverdue: {
    color: '#D32F2F',
    fontWeight: '600',
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#1B5E20',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 6,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#333' },
  emptySubtext: { fontSize: 13, color: '#666', marginTop: 4 },
});
