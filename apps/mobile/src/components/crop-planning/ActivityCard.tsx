import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { COLORS, ACTIVITY_TYPE_ICONS, ACTIVITY_STATUS_COLORS } from '@/utils/constants';
import StatusBadge from './StatusBadge';
import type { PlannedActivity } from '@/types/crop-planning';

type Props = {
  activity: PlannedActivity;
  planId: string;
  testID?: string;
};

const priorityColors: Record<string, string> = {
  high: '#D32F2F',
  medium: '#FF9800',
  low: '#4CAF50',
};

function getPriorityLevel(priority: number): string {
  if (priority <= 3) return 'high';
  if (priority <= 6) return 'medium';
  return 'low';
}

export default function ActivityCard({ activity, planId, testID }: Props) {
  const icon = ACTIVITY_TYPE_ICONS[activity.activityType] || '\u{1F4CB}';
  const priorityLevel = getPriorityLevel(activity.priority);
  const dateStr = new Date(activity.scheduledDate).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={() =>
        router.push({
          pathname: `/crop-planning/${planId}/activity-complete`,
          params: { activityId: activity.id },
        } as any)
      }
      testID={testID}
    >
      <View style={styles.iconContainer}>
        <Text style={styles.icon}>{icon}</Text>
      </View>
      <View style={styles.content}>
        <Text style={styles.title} numberOfLines={1}>{activity.title}</Text>
        <View style={styles.metaRow}>
          <Text style={styles.date}>{dateStr}</Text>
          {activity.growthStage && (
            <Text style={styles.stage}>{activity.growthStage.replace(/_/g, ' ')}</Text>
          )}
        </View>
      </View>
      <View style={styles.rightColumn}>
        <StatusBadge status={activity.status} type="activity" />
        <View style={[styles.priorityDot, { backgroundColor: priorityColors[priorityLevel] }]} />
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 2,
    elevation: 1,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  icon: { fontSize: 20 },
  content: { flex: 1 },
  title: { fontSize: 14, fontWeight: '600', color: '#333' },
  metaRow: { flexDirection: 'row', alignItems: 'center', marginTop: 4 },
  date: { fontSize: 12, color: '#666' },
  stage: { fontSize: 12, color: COLORS.gray[500], marginLeft: 8, textTransform: 'capitalize' },
  rightColumn: { alignItems: 'flex-end', gap: 6 },
  priorityDot: { width: 8, height: 8, borderRadius: 4 },
});
