import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useFarmStore, Farm } from '@/store/farm';

const OWNERSHIP_LABELS: Record<string, string> = {
  freehold: 'Freehold',
  leasehold: 'Leasehold',
  communal: 'Communal',
  trust: 'Trust Land',
  family: 'Family Land',
  rented: 'Rented',
};

export default function FarmDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { farms, fetchFarms, isLoading } = useFarmStore();

  const [refreshing, setRefreshing] = useState(false);
  const [farm, setFarm] = useState<Farm | null>(null);

  useEffect(() => {
    if (id) {
      const foundFarm = farms.find((f) => f.id === id);
      setFarm(foundFarm || null);
    }
  }, [id, farms]);

  useEffect(() => {
    if (!farm && id) {
      fetchFarms();
    }
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchFarms();
    setRefreshing(false);
  };

  if (isLoading && !farm) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Loading farm details...</Text>
      </View>
    );
  }

  if (!farm) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorIcon}>🚫</Text>
        <Text style={styles.errorTitle}>Farm Not Found</Text>
        <Text style={styles.errorText}>
          This farm could not be found. It may have been removed.
        </Text>
        <TouchableOpacity
          style={styles.backToListButton}
          onPress={() => router.replace('/(tabs)/farms')}
        >
          <Text style={styles.backToListButtonText}>Back to Farms</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const getStatusBadge = () => {
    if (farm.registrationComplete) {
      return { label: 'Verified', color: COLORS.success };
    }
    return { label: 'In Progress', color: COLORS.warning };
  };

  const status = getStatusBadge();

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Hero Section */}
      <View style={styles.hero}>
        <View style={styles.heroContent}>
          <View style={[styles.statusBadge, { backgroundColor: status.color + '20' }]}>
            <View style={[styles.statusDot, { backgroundColor: status.color }]} />
            <Text style={[styles.statusText, { color: status.color }]}>
              {status.label}
            </Text>
          </View>
          <Text style={styles.farmName}>{farm.name}</Text>
          {farm.plotId && (
            <Text style={styles.plotId}>Plot ID: {farm.plotId}</Text>
          )}
        </View>
      </View>

      {/* Quick Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>
            {farm.totalAcreage?.toFixed(1) || '-'}
          </Text>
          <Text style={styles.statLabel}>Acres</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>
            {farm.crops?.length || 0}
          </Text>
          <Text style={styles.statLabel}>Crops</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>
            {farm.documents?.length || 0}
          </Text>
          <Text style={styles.statLabel}>Documents</Text>
        </View>
      </View>

      {/* Location Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Location</Text>
        <View style={styles.card}>
          {farm.county && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>County</Text>
              <Text style={styles.infoValue}>{farm.county}</Text>
            </View>
          )}
          {farm.subCounty && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Sub-County</Text>
              <Text style={styles.infoValue}>{farm.subCounty}</Text>
            </View>
          )}
          {farm.ward && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Ward</Text>
              <Text style={styles.infoValue}>{farm.ward}</Text>
            </View>
          )}
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Coordinates</Text>
            <Text style={styles.infoValue}>
              {farm.latitude?.toFixed(6)}, {farm.longitude?.toFixed(6)}
            </Text>
          </View>
          {farm.addressDescription && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Directions</Text>
              <Text style={styles.infoValueFull}>{farm.addressDescription}</Text>
            </View>
          )}
        </View>

        {/* View on Map Button */}
        <TouchableOpacity
          style={styles.mapButton}
          onPress={() => router.push(`/farms/${id}/boundary`)}
        >
          <Text style={styles.mapButtonIcon}>🗺️</Text>
          <Text style={styles.mapButtonText}>View Boundary on Map</Text>
        </TouchableOpacity>
      </View>

      {/* Land Details Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Land Details</Text>
        <View style={styles.card}>
          {farm.ownershipType && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Ownership</Text>
              <Text style={styles.infoValue}>
                {OWNERSHIP_LABELS[farm.ownershipType] || farm.ownershipType}
              </Text>
            </View>
          )}
          {farm.landUseType && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Land Use</Text>
              <Text style={styles.infoValue}>{farm.landUseType}</Text>
            </View>
          )}
          {farm.totalAcreage && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Total Acreage</Text>
              <Text style={styles.infoValue}>{farm.totalAcreage} acres</Text>
            </View>
          )}
          {farm.cultivatedAcreage && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Cultivated</Text>
              <Text style={styles.infoValue}>{farm.cultivatedAcreage} acres</Text>
            </View>
          )}
          {farm.landReferenceNumber && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>LR Number</Text>
              <Text style={styles.infoValue}>{farm.landReferenceNumber}</Text>
            </View>
          )}
        </View>
      </View>

      {/* Soil & Water Section */}
      {(farm.soilType || farm.waterSources) && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Soil & Water</Text>
          <View style={styles.card}>
            {farm.soilType && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Soil Type</Text>
                <Text style={styles.infoValue}>{farm.soilType}</Text>
              </View>
            )}
            {farm.soilPh && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Soil pH</Text>
                <Text style={styles.infoValue}>{farm.soilPh}</Text>
              </View>
            )}
            {farm.waterSources && farm.waterSources.length > 0 && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Water Sources</Text>
                <Text style={styles.infoValue}>
                  {farm.waterSources.join(', ')}
                </Text>
              </View>
            )}
            {farm.irrigationMethod && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Irrigation</Text>
                <Text style={styles.infoValue}>{farm.irrigationMethod}</Text>
              </View>
            )}
          </View>
        </View>
      )}

      {/* Current Crops Section */}
      {farm.crops && farm.crops.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Crops</Text>
          <View style={styles.cropsContainer}>
            {farm.crops.map((crop: any, index: number) => (
              <View key={index} style={styles.cropCard}>
                <Text style={styles.cropName}>{crop.cropName || crop.cropType}</Text>
                <Text style={styles.cropDetails}>
                  {crop.acreage} acres • {crop.season} {crop.year}
                </Text>
              </View>
            ))}
          </View>
          <TouchableOpacity
            style={styles.viewAllButton}
            onPress={() => router.push(`/farms/${id}/crops`)}
          >
            <Text style={styles.viewAllButtonText}>Manage Crops</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Documents Section */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Documents</Text>
          <TouchableOpacity onPress={() => router.push(`/farms/${id}/documents`)}>
            <Text style={styles.sectionAction}>Manage</Text>
          </TouchableOpacity>
        </View>
        {farm.documents && farm.documents.length > 0 ? (
          <View style={styles.documentsGrid}>
            {farm.documents.slice(0, 4).map((doc: any, index: number) => (
              <View key={index} style={styles.documentItem}>
                <Text style={styles.documentIcon}>📄</Text>
                <Text style={styles.documentName} numberOfLines={1}>
                  {doc.name}
                </Text>
              </View>
            ))}
          </View>
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateText}>No documents uploaded</Text>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => router.push(`/farms/${id}/documents`)}
            >
              <Text style={styles.addButtonText}>Add Documents</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => router.push(`/farms/${id}/land-details`)}
        >
          <Text style={styles.actionButtonIcon}>✏️</Text>
          <Text style={styles.actionButtonText}>Edit Details</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.actionButtonDanger]}
          onPress={() => {
            Alert.alert(
              'Delete Farm',
              'Are you sure you want to delete this farm? This action cannot be undone.',
              [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Delete',
                  style: 'destructive',
                  onPress: () => {
                    // TODO: Implement delete
                    Alert.alert('Coming Soon', 'Delete functionality will be available soon.');
                  },
                },
              ]
            );
          }}
        >
          <Text style={styles.actionButtonIcon}>🗑️</Text>
          <Text style={[styles.actionButtonText, styles.actionButtonTextDanger]}>
            Delete Farm
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.gray[50],
  },
  content: {
    paddingBottom: SPACING.xxl,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.gray[50],
  },
  loadingText: {
    marginTop: SPACING.md,
    color: COLORS.gray[600],
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.gray[50],
    padding: SPACING.xl,
  },
  errorIcon: {
    fontSize: 48,
    marginBottom: SPACING.md,
  },
  errorTitle: {
    fontSize: FONT_SIZES.xl,
    fontWeight: 'bold',
    color: COLORS.gray[800],
    marginBottom: SPACING.sm,
  },
  errorText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[600],
    textAlign: 'center',
    marginBottom: SPACING.lg,
  },
  backToListButton: {
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.lg,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
  },
  backToListButtonText: {
    color: COLORS.white,
    fontWeight: '600',
  },
  hero: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.xl,
    paddingTop: SPACING.md,
  },
  heroContent: {},
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingVertical: 4,
    paddingHorizontal: SPACING.sm,
    borderRadius: 12,
    marginBottom: SPACING.sm,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: SPACING.xs,
  },
  statusText: {
    fontSize: FONT_SIZES.xs,
    fontWeight: '600',
  },
  farmName: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.white,
    marginBottom: SPACING.xs,
  },
  plotId: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.white + 'CC',
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: SPACING.lg,
    marginTop: -SPACING.lg,
  },
  statCard: {
    flex: 1,
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.md,
    alignItems: 'center',
    marginHorizontal: 4,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statValue: {
    fontSize: FONT_SIZES.xl,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  statLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[600],
    marginTop: 2,
  },
  section: {
    paddingHorizontal: SPACING.lg,
    marginTop: SPACING.xl,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.sm,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  sectionAction: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.primary,
    fontWeight: '500',
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: SPACING.xs,
  },
  infoLabel: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
  },
  infoValue: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[900],
    fontWeight: '500',
    maxWidth: '60%',
    textAlign: 'right',
    textTransform: 'capitalize',
  },
  infoValueFull: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
    flex: 1,
    marginLeft: SPACING.md,
  },
  mapButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.gray[100],
    borderRadius: 8,
    padding: SPACING.sm,
    marginTop: SPACING.sm,
  },
  mapButtonIcon: {
    fontSize: 18,
    marginRight: SPACING.xs,
  },
  mapButtonText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
    fontWeight: '500',
  },
  cropsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  cropCard: {
    backgroundColor: COLORS.white,
    borderRadius: 8,
    padding: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
    minWidth: 120,
  },
  cropName: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '600',
    color: COLORS.gray[900],
    textTransform: 'capitalize',
  },
  cropDetails: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[500],
    marginTop: 2,
  },
  viewAllButton: {
    alignItems: 'center',
    padding: SPACING.sm,
    marginTop: SPACING.sm,
  },
  viewAllButtonText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.primary,
    fontWeight: '500',
  },
  documentsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  documentItem: {
    backgroundColor: COLORS.white,
    borderRadius: 8,
    padding: SPACING.sm,
    alignItems: 'center',
    width: 80,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  documentIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  documentName: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[700],
    textAlign: 'center',
  },
  emptyState: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.lg,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  emptyStateText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[500],
    marginBottom: SPACING.sm,
  },
  addButton: {
    paddingVertical: SPACING.xs,
    paddingHorizontal: SPACING.md,
    backgroundColor: COLORS.primary + '10',
    borderRadius: 6,
  },
  addButtonText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.primary,
    fontWeight: '500',
  },
  actions: {
    paddingHorizontal: SPACING.lg,
    marginTop: SPACING.xl,
    gap: SPACING.sm,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.md,
    backgroundColor: COLORS.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  actionButtonDanger: {
    borderColor: COLORS.error + '30',
    backgroundColor: COLORS.error + '05',
  },
  actionButtonIcon: {
    fontSize: 18,
    marginRight: SPACING.sm,
  },
  actionButtonText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[700],
    fontWeight: '500',
  },
  actionButtonTextDanger: {
    color: COLORS.error,
  },
});
