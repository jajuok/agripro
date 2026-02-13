import { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { router } from 'expo-router';
import { useAuthStore } from '@/store/auth';
import { farmApi, kycApi, cropPlanningApi } from '@/services/api';

type MenuItem = {
  icon: string;
  label: string;
  testID: string;
  route?: string;
  action?: () => void;
};

type ProfileStats = {
  farmCount: number;
  totalHectares: number;
  activePlans: number;
  kycStatus: string;
  kycVerified: boolean;
};

export default function ProfileScreen() {
  const { user, logout } = useAuthStore();
  const [stats, setStats] = useState<ProfileStats>({
    farmCount: 0,
    totalHectares: 0,
    activePlans: 0,
    kycStatus: 'Not Started',
    kycVerified: false,
  });
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = useCallback(async () => {
    const farmerId = user?.farmerId;
    if (!farmerId) return;

    try {
      const [farmsResult, kycResult, dashboardResult] = await Promise.allSettled([
        farmApi.list(farmerId),
        kycApi.getStatus(farmerId),
        cropPlanningApi.getDashboard(farmerId),
      ]);

      const farms = farmsResult.status === 'fulfilled' ? (Array.isArray(farmsResult.value) ? farmsResult.value : []) : [];
      const totalHectares = farms.reduce((sum: number, f: any) => sum + (f.total_acreage || f.cultivable_acreage || 0), 0);

      const kyc = kycResult.status === 'fulfilled' ? kycResult.value : null;
      const kycStatus = kyc?.status || kyc?.kyc_status || 'Not Started';
      const kycVerified = ['verified', 'approved', 'completed'].includes(kycStatus.toLowerCase());

      const dashboard = dashboardResult.status === 'fulfilled' ? dashboardResult.value : null;
      const activePlans = dashboard?.active_plans || dashboard?.total_plans || 0;

      setStats({
        farmCount: farms.length,
        totalHectares: Math.round(totalHectares * 10) / 10,
        activePlans,
        kycStatus,
        kycVerified,
      });
    } catch {
      // Keep defaults on error
    } finally {
      setRefreshing(false);
    }
  }, [user?.farmerId]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchStats();
  }, [fetchStats]);

  const initials = user
    ? `${user.firstName?.charAt(0) || ''}${user.lastName?.charAt(0) || ''}`.toUpperCase() || '?'
    : '?';

  const menuItems: MenuItem[] = [
    { icon: '👤', label: 'Edit Profile', testID: 'profile-menu-edit', route: '/profile/edit' },
    { icon: '🛡️', label: 'KYC Documents', testID: 'profile-menu-kyc', route: '/kyc' },
    { icon: '💳', label: 'Payment Methods', testID: 'profile-menu-payments', route: '/profile/payments' },
    { icon: '🔔', label: 'Notifications', testID: 'profile-menu-notifications', route: '/profile/notifications' },
    { icon: '❓', label: 'Help & Support', testID: 'profile-menu-help', route: '/support' },
    { icon: '📄', label: 'Terms & Privacy', testID: 'profile-menu-terms', route: '/legal' },
    { icon: '🚪', label: 'Logout', testID: 'profile-logout-button', action: () => {
      logout();
      router.replace('/(auth)/login');
    }},
  ];

  return (
    <ScrollView
      style={styles.container}
      testID="profile-screen"
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header} testID="profile-header">
        <View style={styles.avatarContainer} testID="profile-avatar-container">
          <View style={styles.avatar} testID="profile-avatar">
            <Text style={styles.initialsText}>{initials}</Text>
          </View>
          <TouchableOpacity style={styles.editAvatar} testID="profile-edit-avatar-button">
            <Text style={{ fontSize: 16 }}>📷</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.name} testID="profile-name">
          {user ? `${user.firstName} ${user.lastName}`.trim() || 'User' : 'User'}
        </Text>
        <Text style={styles.email} testID="profile-email">
          {user?.email || user?.phoneNumber || ''}
        </Text>
        <View style={[styles.verifiedBadge, !stats.kycVerified && styles.unverifiedBadge]} testID="profile-verified-badge">
          <Text style={{ fontSize: 16 }}>{stats.kycVerified ? '✅' : '⚠️'}</Text>
          <Text style={[styles.verifiedText, !stats.kycVerified && styles.unverifiedText]} testID="profile-verified-text">
            {stats.kycVerified ? 'KYC Verified' : stats.kycStatus}
          </Text>
        </View>
      </View>

      <View style={styles.statsRow} testID="profile-stats">
        <View style={styles.statItem} testID="profile-stat-farms">
          <Text style={styles.statValue} testID="profile-stat-farms-value">{stats.farmCount}</Text>
          <Text style={styles.statLabel} testID="profile-stat-farms-label">Farms</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem} testID="profile-stat-hectares">
          <Text style={styles.statValue} testID="profile-stat-hectares-value">{stats.totalHectares}</Text>
          <Text style={styles.statLabel} testID="profile-stat-hectares-label">Hectares</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem} testID="profile-stat-schemes">
          <Text style={styles.statValue} testID="profile-stat-schemes-value">{stats.activePlans}</Text>
          <Text style={styles.statLabel} testID="profile-stat-schemes-label">Crop Plans</Text>
        </View>
      </View>

      <View style={styles.menu} testID="profile-menu">
        {menuItems.map((item, index) => (
          <TouchableOpacity
            key={index}
            style={styles.menuItem}
            testID={item.testID}
            onPress={() => {
              if (item.action) {
                item.action();
              } else if (item.route) {
                router.push(item.route as any);
              }
            }}
          >
            <View style={styles.menuItemLeft}>
              <Text style={{ fontSize: 24 }}>{item.icon}</Text>
              <Text style={styles.menuItemLabel}>{item.label}</Text>
            </View>
            <Text style={{ fontSize: 20, color: '#ccc' }}>›</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.version} testID="profile-version">Version 0.1.0</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    alignItems: 'center',
    paddingVertical: 32,
  },
  avatarContainer: {
    position: 'relative',
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#E8F5E9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  initialsText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#1B5E20',
  },
  editAvatar: {
    position: 'absolute',
    right: 0,
    bottom: 0,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#1B5E20',
    justifyContent: 'center',
    alignItems: 'center',
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
  },
  email: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginTop: 12,
  },
  unverifiedBadge: {
    backgroundColor: '#FFF3E0',
  },
  verifiedText: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: '600',
    marginLeft: 4,
  },
  unverifiedText: {
    color: '#FF9800',
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginTop: 16,
    paddingVertical: 16,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    backgroundColor: '#f0f0f0',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1B5E20',
  },
  statLabel: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  menu: {
    backgroundColor: '#fff',
    marginTop: 16,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  menuItemLabel: {
    fontSize: 16,
    color: '#333',
    marginLeft: 16,
  },
  version: {
    textAlign: 'center',
    color: '#999',
    fontSize: 12,
    paddingVertical: 24,
  },
});
