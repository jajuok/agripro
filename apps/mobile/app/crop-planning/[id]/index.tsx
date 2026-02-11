import { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { router, useLocalSearchParams, useFocusEffect } from 'expo-router';
import { useCropPlanningStore } from '@/store/crop-planning';
import { COLORS, SEASON_LABELS } from '@/utils/constants';
import StatusBadge from '@/components/crop-planning/StatusBadge';
import GrowthStageTimeline from '@/components/crop-planning/GrowthStageTimeline';

export default function PlanDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const {
    selectedPlan: plan,
    statistics: stats,
    fetchPlan,
    fetchStatistics,
    activatePlan,
    advanceStage,
    completePlan,
    isLoading,
  } = useCropPlanningStore();

  useFocusEffect(
    useCallback(() => {
      if (id) {
        fetchPlan(id);
        fetchStatistics(id);
      }
    }, [id])
  );

  const growthStages = plan?.growthStageHistory
    ? plan.growthStageHistory.map((s: any) => s.stage || s.name).filter(Boolean)
    : [];

  const handleActivate = () => {
    Alert.alert('Activate Plan', 'This will activate the plan and start tracking activities.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Activate',
        onPress: async () => {
          try {
            await activatePlan(id!);
            fetchPlan(id!);
          } catch (e: any) {
            Alert.alert('Error', e.message);
          }
        },
      },
    ]);
  };

  const handleComplete = () => {
    Alert.prompt
      ? Alert.alert('Complete Plan', 'Mark this plan as completed?', [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Complete',
            onPress: async () => {
              try {
                await completePlan(id!, {
                  actual_harvest_date: new Date().toISOString(),
                  actual_yield_kg: 0,
                });
                fetchPlan(id!);
              } catch (e: any) {
                Alert.alert('Error', e.message);
              }
            },
          },
        ])
      : null;
  };

  if (isLoading && !plan) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (!plan) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={{ fontSize: 16, color: '#666' }}>Plan not found</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={isLoading}
          onRefresh={() => { fetchPlan(id!); fetchStatistics(id!); }}
          colors={[COLORS.primary]}
        />
      }
      testID="cp-plan-detail-screen"
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerRow}>
          <View style={styles.headerLeft}>
            <Text style={styles.cropName}>{plan.cropName}</Text>
            {plan.variety && <Text style={styles.variety}>{plan.variety}</Text>}
          </View>
          <StatusBadge status={plan.status} type="plan" />
        </View>
        <Text style={styles.planName}>{plan.name}</Text>
        <Text style={styles.seasonInfo}>
          {SEASON_LABELS[plan.season] || plan.season} {plan.year} - {plan.plannedAcreage} acres
        </Text>
      </View>

      {/* Growth Stage Timeline */}
      {growthStages.length > 0 && (
        <View style={styles.section}>
          <GrowthStageTimeline
            stages={growthStages}
            currentStage={plan.currentGrowthStage}
            testID="cp-plan-timeline"
          />
        </View>
      )}

      {/* Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats?.daysSincePlanting ?? '-'}</Text>
          <Text style={styles.statLabel}>Days Planted</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats?.daysToHarvest ?? '-'}</Text>
          <Text style={styles.statLabel}>To Harvest</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats?.completionPercentage?.toFixed(0) ?? 0}%</Text>
          <Text style={styles.statLabel}>Complete</Text>
        </View>
      </View>

      {/* Navigation Cards */}
      <View style={styles.section}>
        <TouchableOpacity
          style={styles.navCard}
          onPress={() => router.push(`/crop-planning/${id}/activities`)}
          testID="cp-plan-nav-activities"
        >
          <Text style={styles.navIcon}>📋</Text>
          <View style={styles.navContent}>
            <Text style={styles.navTitle}>Activities</Text>
            <Text style={styles.navSubtitle}>
              {stats?.activitiesCompleted ?? 0}/{stats?.activitiesTotal ?? 0} completed
              {(stats?.activitiesOverdue ?? 0) > 0 && ` - ${stats!.activitiesOverdue} overdue`}
            </Text>
          </View>
          <Text style={styles.navArrow}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navCard}
          onPress={() => router.push(`/crop-planning/${id}/inputs`)}
          testID="cp-plan-nav-inputs"
        >
          <Text style={styles.navIcon}>📦</Text>
          <View style={styles.navContent}>
            <Text style={styles.navTitle}>Inputs</Text>
            <Text style={styles.navSubtitle}>
              {stats?.inputsProcuredPercentage?.toFixed(0) ?? 0}% procured
            </Text>
          </View>
          <Text style={styles.navArrow}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navCard}
          onPress={() => router.push(`/crop-planning/${id}/irrigation`)}
          testID="cp-plan-nav-irrigation"
        >
          <Text style={styles.navIcon}>💧</Text>
          <View style={styles.navContent}>
            <Text style={styles.navTitle}>Irrigation</Text>
            <Text style={styles.navSubtitle}>Schedule & water tracking</Text>
          </View>
          <Text style={styles.navArrow}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Action Buttons */}
      <View style={styles.section}>
        {plan.status === 'draft' && (
          <TouchableOpacity style={styles.primaryButton} onPress={handleActivate} testID="cp-plan-activate">
            <Text style={styles.primaryButtonText}>Activate Plan</Text>
          </TouchableOpacity>
        )}
        {plan.status === 'active' && (
          <TouchableOpacity style={[styles.primaryButton, { backgroundColor: '#2196F3' }]} onPress={handleComplete} testID="cp-plan-complete">
            <Text style={styles.primaryButtonText}>Complete Plan</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Notes */}
      {plan.notes && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notes</Text>
          <View style={styles.notesCard}>
            <Text style={styles.notesText}>{plan.notes}</Text>
          </View>
        </View>
      )}

      <View style={{ height: 32 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f5f5f5' },
  header: { backgroundColor: '#fff', padding: 16, marginBottom: 8 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  headerLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  cropName: { fontSize: 22, fontWeight: '700', color: COLORS.primary },
  variety: { fontSize: 14, color: COLORS.gray[500], marginLeft: 8 },
  planName: { fontSize: 15, fontWeight: '500', color: '#333', marginTop: 2 },
  seasonInfo: { fontSize: 13, color: '#666', marginTop: 4 },
  section: { paddingHorizontal: 16, marginBottom: 12 },
  statsRow: { flexDirection: 'row', paddingHorizontal: 16, marginBottom: 12 },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    marginHorizontal: 3,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  statValue: { fontSize: 20, fontWeight: 'bold', color: COLORS.primary },
  statLabel: { fontSize: 11, color: '#666', marginTop: 4 },
  navCard: {
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
    elevation: 1,
  },
  navIcon: { fontSize: 24, marginRight: 14 },
  navContent: { flex: 1 },
  navTitle: { fontSize: 16, fontWeight: '600', color: '#333' },
  navSubtitle: { fontSize: 12, color: '#666', marginTop: 2 },
  navArrow: { fontSize: 24, color: '#ccc' },
  primaryButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 4,
  },
  primaryButtonText: { fontSize: 16, fontWeight: '600', color: '#fff' },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 8 },
  notesCard: { backgroundColor: '#fff', borderRadius: 10, padding: 14 },
  notesText: { fontSize: 14, color: '#333', lineHeight: 20 },
});
