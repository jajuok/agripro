import { useCallback, useMemo } from 'react';
import { View, Text, StyleSheet, SectionList, TouchableOpacity, ActivityIndicator } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { useCropPlanningStore } from '@/store/crop-planning';
import { useTaskStore } from '@/store/task';
import { useAuthStore } from '@/store/auth';
import { ACTIVITY_TYPE_ICONS, TASK_CATEGORY_ICONS, TASK_STATUS_COLORS, COLORS } from '@/utils/constants';
import type { UpcomingActivity } from '@/types/crop-planning';
import type { Task } from '@/types/task';

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

type UnifiedItem =
  | { kind: 'activity'; data: UpcomingActivity }
  | { kind: 'task'; data: Task };

function getDueLabel(item: UnifiedItem): string {
  if (item.kind === 'activity') {
    const d = item.data.daysUntil;
    if (d < 0) return `${Math.abs(d)}d overdue`;
    if (d === 0) return 'Today';
    if (d === 1) return 'Tomorrow';
    if (d <= 7) return `In ${d} days`;
    return `In ${Math.ceil(d / 7)} weeks`;
  }
  const task = item.data;
  if (!task.dueDate) return '';
  const diff = Math.floor((new Date(task.dueDate).getTime() - Date.now()) / 86400000);
  if (diff < 0) return `${Math.abs(diff)}d overdue`;
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  if (diff <= 7) return `In ${diff} days`;
  return `In ${Math.ceil(diff / 7)} weeks`;
}

function isOverdue(item: UnifiedItem): boolean {
  if (item.kind === 'activity') return item.data.isOverdue;
  const t = item.data;
  if (!t.dueDate || t.status === 'completed' || t.status === 'cancelled') return false;
  return new Date(t.dueDate) < new Date();
}

function daysUntil(item: UnifiedItem): number {
  if (item.kind === 'activity') return item.data.daysUntil;
  const t = item.data;
  if (!t.dueDate) return 999;
  return Math.floor((new Date(t.dueDate).getTime() - Date.now()) / 86400000);
}

export default function TasksScreen() {
  const user = useAuthStore((s) => s.user);
  const { upcomingActivities, fetchUpcomingActivities, isLoading: actLoading } = useCropPlanningStore();
  const { tasks, fetchTasks, isLoading: taskLoading } = useTaskStore();

  useFocusEffect(
    useCallback(() => {
      if (user?.farmerId) {
        fetchUpcomingActivities(user.farmerId, 14);
        fetchTasks(user.farmerId, { limit: 100 });
      }
    }, [user?.farmerId])
  );

  const isLoading = actLoading || taskLoading;

  // Merge activities and standalone tasks into unified sections
  const sections = useMemo(() => {
    const actItems: UnifiedItem[] = upcomingActivities.map((a) => ({ kind: 'activity', data: a }));
    const activeTasks = tasks.filter((t) => t.status !== 'completed' && t.status !== 'cancelled');
    const taskItems: UnifiedItem[] = activeTasks.map((t) => ({ kind: 'task', data: t }));
    const all = [...actItems, ...taskItems];

    const overdueItems = all.filter((i) => isOverdue(i)).sort((a, b) => daysUntil(a) - daysUntil(b));
    const todayItems = all.filter((i) => !isOverdue(i) && daysUntil(i) === 0);
    const upcomingItems = all.filter((i) => !isOverdue(i) && daysUntil(i) > 0).sort((a, b) => daysUntil(a) - daysUntil(b));
    const noDueItems = all.filter((i) => i.kind === 'task' && !(i.data as Task).dueDate);

    return [
      { title: 'Overdue', data: overdueItems },
      { title: 'Today', data: todayItems },
      { title: 'Upcoming', data: upcomingItems },
      { title: 'No Due Date', data: noDueItems },
    ].filter((s) => s.data.length > 0);
  }, [upcomingActivities, tasks]);

  const renderItem = ({ item }: { item: UnifiedItem }) => {
    if (item.kind === 'activity') {
      const act = item.data;
      const icon = ACTIVITY_TYPE_ICONS[act.activity.activityType] || '📋';
      const priority = getPriorityLevel(act.activity.priority);
      return (
        <TouchableOpacity
          style={styles.taskCard}
          onPress={() =>
            router.push({
              pathname: `/crop-planning/${act.planId}/activity-complete`,
              params: { activityId: act.activity.id },
            } as any)
          }
        >
          <View style={styles.iconContainer}>
            <Text style={{ fontSize: 24 }}>{icon}</Text>
          </View>
          <View style={styles.taskContent}>
            <Text style={styles.taskTitle} numberOfLines={1}>{act.activity.title}</Text>
            <Text style={styles.taskSubtitle}>{act.cropName} - {act.farmName}</Text>
          </View>
          <View style={styles.taskMeta}>
            <View style={[styles.priorityDot, { backgroundColor: priorityColors[priority] }]} />
            <Text style={[styles.taskDue, isOverdue(item) && styles.taskOverdue]}>
              {getDueLabel(item)}
            </Text>
          </View>
        </TouchableOpacity>
      );
    }

    const task = item.data;
    const icon = TASK_CATEGORY_ICONS[task.category] || '📌';
    const priority = getPriorityLevel(task.priority);
    const statusColor = TASK_STATUS_COLORS[task.status] || '#999';

    return (
      <TouchableOpacity
        style={styles.taskCard}
        onPress={() => router.push(`/tasks/${task.id}` as any)}
      >
        <View style={styles.iconContainer}>
          <Text style={{ fontSize: 24 }}>{icon}</Text>
        </View>
        <View style={styles.taskContent}>
          <Text style={styles.taskTitle} numberOfLines={1}>{task.title}</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 2 }}>
            <View style={[styles.statusBadge, { backgroundColor: statusColor + '20' }]}>
              <Text style={[styles.statusText, { color: statusColor }]}>{task.status.replace('_', ' ')}</Text>
            </View>
          </View>
        </View>
        <View style={styles.taskMeta}>
          <View style={[styles.priorityDot, { backgroundColor: priorityColors[priority] }]} />
          <Text style={[styles.taskDue, isOverdue(item) && styles.taskOverdue]}>
            {getDueLabel(item)}
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
          renderItem={renderItem}
          renderSectionHeader={({ section }) => (
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>{section.title}</Text>
              <Text style={styles.sectionCount}>{section.data.length}</Text>
            </View>
          )}
          keyExtractor={(item, index) =>
            item.kind === 'activity' ? `act-${item.data.activity.id}` : `task-${item.data.id}`
          }
          contentContainerStyle={styles.list}
          stickySectionHeadersEnabled={false}
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>✅</Text>
              <Text style={styles.emptyText}>No tasks</Text>
              <Text style={styles.emptySubtext}>Create a task or crop plan to get started</Text>
            </View>
          }
        />
      )}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => router.push('/tasks/create' as any)}
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
  taskSubtitle: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'capitalize',
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
