import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { COLORS, CROP_PLAN_STATUS_COLORS, SEASON_LABELS } from '@/utils/constants';
import StatusBadge from './StatusBadge';
import type { CropPlanSummary } from '@/types/crop-planning';

type Props = {
  plan: CropPlanSummary;
  testID?: string;
};

export default function PlanCard({ plan, testID }: Props) {
  const progress = plan.activitiesTotal > 0
    ? (plan.activitiesCompleted / plan.activitiesTotal) * 100
    : 0;

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={() => router.push(`/crop-planning/${plan.id}`)}
      testID={testID}
    >
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.cropName} numberOfLines={1}>{plan.cropName}</Text>
          {plan.variety && <Text style={styles.variety}>{plan.variety}</Text>}
        </View>
        <StatusBadge status={plan.status} type="plan" />
      </View>

      <Text style={styles.planName} numberOfLines={1}>{plan.name}</Text>
      <Text style={styles.farmName}>{plan.farmName} - {SEASON_LABELS[plan.season] || plan.season} {plan.year}</Text>

      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${progress}%` }]} />
        </View>
        <Text style={styles.progressText}>{plan.activitiesCompleted}/{plan.activitiesTotal}</Text>
      </View>

      {plan.activitiesOverdue > 0 && (
        <View style={styles.overdueRow}>
          <Text style={styles.overdueText}>{plan.activitiesOverdue} overdue</Text>
        </View>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 8,
  },
  cropName: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.primary,
  },
  variety: {
    fontSize: 12,
    color: COLORS.gray[500],
    marginLeft: 8,
  },
  planName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
    marginBottom: 2,
  },
  farmName: {
    fontSize: 12,
    color: '#666',
    marginBottom: 10,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressBar: {
    flex: 1,
    height: 6,
    backgroundColor: '#E0E0E0',
    borderRadius: 3,
    overflow: 'hidden',
    marginRight: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.primaryLight,
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  overdueRow: {
    marginTop: 6,
  },
  overdueText: {
    fontSize: 12,
    color: COLORS.error,
    fontWeight: '600',
  },
});
