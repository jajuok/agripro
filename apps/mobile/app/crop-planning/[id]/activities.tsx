import { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useLocalSearchParams, useFocusEffect } from 'expo-router';
import { useCropPlanningStore } from '@/store/crop-planning';
import { COLORS, ACTIVITY_STATUS_COLORS } from '@/utils/constants';
import ActivityCard from '@/components/crop-planning/ActivityCard';
import type { PlannedActivity } from '@/types/crop-planning';

const STATUS_FILTERS = ['all', 'scheduled', 'in_progress', 'completed', 'overdue', 'skipped'];

export default function ActivitiesScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { activities, fetchActivities, isLoading } = useCropPlanningStore();
  const [statusFilter, setStatusFilter] = useState('all');

  useFocusEffect(
    useCallback(() => {
      if (id) fetchActivities(id);
    }, [id])
  );

  const filtered = statusFilter === 'all'
    ? activities
    : activities.filter((a) => a.status === statusFilter);

  const scheduled = filtered.filter((a) => a.status === 'scheduled' || a.status === 'overdue').length;
  const completed = filtered.filter((a) => a.status === 'completed').length;

  return (
    <View style={styles.container} testID="cp-activities-screen">
      {/* Summary */}
      <View style={styles.summary}>
        <Text style={styles.summaryText}>
          {activities.length} total - {completed} done - {scheduled} pending
        </Text>
      </View>

      {/* Filter chips */}
      <View style={styles.filterRow}>
        {STATUS_FILTERS.map((s) => (
          <TouchableOpacity
            key={s}
            style={[styles.filterChip, statusFilter === s && styles.filterChipActive]}
            onPress={() => setStatusFilter(s)}
            testID={`cp-activities-filter-${s}`}
          >
            <Text style={[styles.filterChipText, statusFilter === s && styles.filterChipTextActive]}>
              {s === 'all' ? 'All' : s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {isLoading && activities.length === 0 ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={filtered}
          renderItem={({ item }) => (
            <ActivityCard activity={item} planId={id!} testID={`cp-activity-${item.id}`} />
          )}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={isLoading} onRefresh={() => fetchActivities(id!)} colors={[COLORS.primary]} />
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>📋</Text>
              <Text style={styles.emptyText}>No activities found</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  summary: { backgroundColor: '#fff', padding: 12, alignItems: 'center', borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  summaryText: { fontSize: 13, color: '#666' },
  filterRow: { flexDirection: 'row', flexWrap: 'wrap', padding: 12, gap: 6, backgroundColor: '#fff' },
  filterChip: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 16, backgroundColor: COLORS.gray[100] },
  filterChipActive: { backgroundColor: COLORS.primary },
  filterChipText: { fontSize: 12, color: COLORS.gray[600], fontWeight: '500' },
  filterChipTextActive: { color: '#fff' },
  list: { padding: 16, paddingBottom: 32 },
  emptyState: { alignItems: 'center', paddingVertical: 48 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#333' },
});
