import React, { useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
// Using Text-based icons instead of Ionicons to avoid font loading issues
import { router, useFocusEffect } from 'expo-router';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useFarmStore, Farm } from '@/store/farm';
import { useAuthStore } from '@/store/auth';

export default function FarmsScreen() {
  const { user } = useAuthStore();
  const { farms, isLoading, error, fetchFarms } = useFarmStore();
  const [refreshing, setRefreshing] = React.useState(false);

  // Fetch farms on mount and when screen is focused
  useFocusEffect(
    useCallback(() => {
      if (user?.id) {
        fetchFarms(user.id);
      }
    }, [user?.id, fetchFarms])
  );

  const onRefresh = useCallback(async () => {
    if (!user?.id) return;
    setRefreshing(true);
    await fetchFarms(user.id);
    setRefreshing(false);
  }, [fetchFarms, user?.id]);

  const getLocation = (farm: Farm): string => {
    if (farm.county) {
      if (farm.subCounty) {
        return `${farm.subCounty}, ${farm.county}`;
      }
      return farm.county;
    }
    if (farm.latitude && farm.longitude) {
      return `${farm.latitude.toFixed(4)}, ${farm.longitude.toFixed(4)}`;
    }
    return 'Location pending';
  };

  const getCropsList = (farm: Farm): string[] => {
    if (farm.crops && farm.crops.length > 0) {
      return farm.crops.slice(0, 3).map((c: any) => c.cropName || c.cropType);
    }
    return [];
  };

  const getStatusBadge = (farm: Farm) => {
    if (farm.registrationComplete) {
      return { label: 'Verified', color: COLORS.success };
    }
    if (farm.registrationStep) {
      return { label: 'In Progress', color: COLORS.warning };
    }
    return null;
  };

  const renderFarm = ({ item }: { item: Farm }) => {
    const status = getStatusBadge(item);
    const crops = getCropsList(item);
    const location = getLocation(item);

    return (
      <TouchableOpacity
        style={styles.farmCard}
        onPress={() => router.push(`/farms/${item.id}`)}
        testID={`farms-card-${item.id}`}
      >
        <View style={styles.farmHeader} testID={`farms-card-${item.id}-header`}>
          <View style={styles.farmIcon} testID={`farms-card-${item.id}-icon`}>
            <Text style={{ fontSize: 24 }}>🌿</Text>
          </View>
          <View style={styles.farmInfo} testID={`farms-card-${item.id}-info`}>
            <View style={styles.farmNameRow}>
              <Text style={styles.farmName} testID={`farms-card-${item.id}-name`}>{item.name}</Text>
              {status && (
                <View style={[styles.statusBadge, { backgroundColor: status.color + '20' }]} testID={`farms-card-${item.id}-status-badge`}>
                  <Text style={[styles.statusText, { color: status.color }]} testID={`farms-card-${item.id}-status-text`}>
                    {status.label}
                  </Text>
                </View>
              )}
            </View>
            <Text style={styles.farmLocation} testID={`farms-card-${item.id}-location`}>
              📍{' '}
              {location}
            </Text>
          </View>
          <Text style={{ fontSize: 20, color: COLORS.gray[300] }}>›</Text>
        </View>
        <View style={styles.farmDetails} testID={`farms-card-${item.id}-details`}>
          <View style={styles.detailItem} testID={`farms-card-${item.id}-acreage`}>
            <Text style={styles.detailValue} testID={`farms-card-${item.id}-acreage-value`}>
              {item.totalAcreage?.toFixed(1) || '-'}
            </Text>
            <Text style={styles.detailLabel}>Acres</Text>
          </View>
          <View style={styles.detailItem} testID={`farms-card-${item.id}-crops`}>
            <Text style={styles.detailValue} testID={`farms-card-${item.id}-crops-count`}>{crops.length || '-'}</Text>
            <Text style={styles.detailLabel}>Crops</Text>
          </View>
          <View style={styles.cropTags} testID={`farms-card-${item.id}-crop-tags`}>
            {crops.length > 0 ? (
              crops.map((crop, index) => (
                <View key={index} style={styles.cropTag} testID={`farms-card-${item.id}-crop-tag-${index}`}>
                  <Text style={styles.cropTagText}>{crop}</Text>
                </View>
              ))
            ) : (
              <Text style={styles.noCropsText} testID={`farms-card-${item.id}-no-crops`}>No crops yet</Text>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState} testID="farms-empty-state">
      <View style={styles.emptyIcon} testID="farms-empty-icon">
        <Text style={{ fontSize: 64 }}>🌿</Text>
      </View>
      <Text style={styles.emptyTitle} testID="farms-empty-title">No Farms Yet</Text>
      <Text style={styles.emptyText} testID="farms-empty-text">
        Register your first farm to get started with AgriPro.
      </Text>
      <TouchableOpacity
        style={styles.emptyButton}
        onPress={() => router.push('/farms/add')}
        testID="farms-empty-add-button"
      >
        <Text style={{ fontSize: 20, color: COLORS.white }}>+</Text>
        <Text style={styles.emptyButtonText}>Add Your First Farm</Text>
      </TouchableOpacity>
    </View>
  );

  const renderHeader = () => {
    if (farms.length === 0) return null;

    const totalAcreage = farms.reduce((sum, f) => sum + (f.totalAcreage || 0), 0);

    return (
      <View style={styles.header} testID="farms-header">
        <Text style={styles.totalFarms} testID="farms-header-count">
          {farms.length} {farms.length === 1 ? 'Farm' : 'Farms'}
        </Text>
        <Text style={styles.totalAcreage} testID="farms-header-total-acreage">
          Total: {totalAcreage.toFixed(1)} acres
        </Text>
      </View>
    );
  };

  if (isLoading && farms.length === 0) {
    return (
      <View style={styles.loadingContainer} testID="farms-loading">
        <ActivityIndicator size="large" color={COLORS.primary} testID="farms-loading-indicator" />
        <Text style={styles.loadingText} testID="farms-loading-text">Loading farms...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container} testID="farms-screen">
      {error && (
        <View style={styles.errorBanner} testID="farms-error-banner">
          <Text style={{ fontSize: 16 }}>⚠️</Text>
          <Text style={styles.errorText} testID="farms-error-text">{error}</Text>
          <TouchableOpacity onPress={onRefresh} testID="farms-error-retry">
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      <FlatList
        data={farms}
        renderItem={renderFarm}
        keyExtractor={(item) => item.id}
        testID="farms-list"
        contentContainerStyle={[
          styles.list,
          farms.length === 0 && styles.listEmpty,
        ]}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={renderEmptyState}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[COLORS.primary]}
            tintColor={COLORS.primary}
          />
        }
      />

      {farms.length > 0 && (
        <TouchableOpacity
          style={styles.fab}
          onPress={() => router.push('/farms/add')}
          testID="farms-add-fab"
        >
          <Text style={{ fontSize: 28, color: COLORS.white }}>+</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.gray[50],
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.gray[50],
  },
  loadingText: {
    marginTop: SPACING.md,
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.error + '10',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    gap: SPACING.sm,
  },
  errorText: {
    flex: 1,
    color: COLORS.error,
    fontSize: FONT_SIZES.sm,
  },
  retryText: {
    color: COLORS.primary,
    fontWeight: '600',
    fontSize: FONT_SIZES.sm,
  },
  list: {
    padding: SPACING.md,
  },
  listEmpty: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  totalFarms: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  totalAcreage: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
  },
  farmCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  farmHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  farmIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.primary + '10',
    justifyContent: 'center',
    alignItems: 'center',
  },
  farmInfo: {
    flex: 1,
    marginLeft: SPACING.sm,
  },
  farmNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: SPACING.xs,
  },
  farmName: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.gray[900],
  },
  statusBadge: {
    paddingHorizontal: SPACING.xs,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusText: {
    fontSize: FONT_SIZES.xs,
    fontWeight: '500',
  },
  farmLocation: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
    marginTop: 2,
  },
  farmDetails: {
    flexDirection: 'row',
    marginTop: SPACING.md,
    paddingTop: SPACING.md,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray[100],
  },
  detailItem: {
    marginRight: SPACING.lg,
  },
  detailValue: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.primary,
  },
  detailLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[500],
  },
  cropTags: {
    flex: 1,
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-end',
  },
  cropTag: {
    backgroundColor: COLORS.primary + '10',
    paddingHorizontal: SPACING.sm,
    paddingVertical: 4,
    borderRadius: 4,
    marginLeft: 4,
    marginBottom: 4,
  },
  cropTagText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.primary,
    textTransform: 'capitalize',
  },
  noCropsText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[400],
    fontStyle: 'italic',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.xl,
  },
  emptyIcon: {
    marginBottom: SPACING.lg,
  },
  emptyTitle: {
    fontSize: FONT_SIZES.xl,
    fontWeight: '600',
    color: COLORS.gray[800],
    marginBottom: SPACING.sm,
  },
  emptyText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[600],
    textAlign: 'center',
    marginBottom: SPACING.xl,
    lineHeight: 22,
  },
  emptyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.lg,
    borderRadius: 8,
    gap: SPACING.xs,
  },
  emptyButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
  },
  fab: {
    position: 'absolute',
    right: SPACING.md,
    bottom: SPACING.md,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 6,
  },
});
