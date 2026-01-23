import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';

type QuickAction = {
  icon: string;
  label: string;
  route: string;
  color: string;
};

const quickActions: QuickAction[] = [
  { icon: '➕', label: 'Add Farm', route: '/farms/add', color: '#4CAF50' },
  { icon: '📋', label: 'Check Eligibility', route: '/eligibility', color: '#2196F3' },
  { icon: '📍', label: 'Record Location', route: '/farms/location', color: '#FF9800' },
  { icon: '📊', label: 'View Reports', route: '/reports', color: '#9C27B0' },
];

export default function HomeScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.greeting}>Welcome back!</Text>
        <Text style={styles.subGreeting}>Here's your farm overview</Text>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>3</Text>
          <Text style={styles.statLabel}>Farms</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>12.5</Text>
          <Text style={styles.statLabel}>Hectares</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>5</Text>
          <Text style={styles.statLabel}>Active Crops</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <View style={styles.actionsGrid}>
        {quickActions.map((action, index) => (
          <TouchableOpacity
            key={index}
            style={styles.actionCard}
            onPress={() => router.push(action.route as any)}
          >
            <View style={[styles.actionIcon, { backgroundColor: action.color }]}>
              <Text style={{ fontSize: 24 }}>{action.icon}</Text>
            </View>
            <Text style={styles.actionLabel}>{action.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.sectionTitle}>KYC Status</Text>
      <View style={styles.kycCard}>
        <View style={styles.kycHeader}>
          <Text style={{ fontSize: 24 }}>✅</Text>
          <Text style={styles.kycStatus}>Verified</Text>
        </View>
        <Text style={styles.kycText}>
          Your KYC verification is complete. You have full access to all features.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Scheme Eligibility</Text>
      <TouchableOpacity
        style={styles.eligibilityCard}
        onPress={() => router.push('/eligibility')}
        testID="eligibility-card"
      >
        <View style={styles.eligibilityHeader}>
          <Text style={{ fontSize: 24 }}>📋</Text>
          <View style={styles.eligibilityInfo}>
            <Text style={styles.eligibilityTitle}>3 Schemes Available</Text>
            <Text style={styles.eligibilitySubtitle}>Check your eligibility for government programs</Text>
          </View>
        </View>
        <View style={styles.eligibilityStats}>
          <View style={styles.eligibilityStat}>
            <Text style={styles.eligibilityStatValue}>1</Text>
            <Text style={styles.eligibilityStatLabel}>Enrolled</Text>
          </View>
          <View style={styles.eligibilityStat}>
            <Text style={styles.eligibilityStatValue}>2</Text>
            <Text style={styles.eligibilityStatLabel}>Available</Text>
          </View>
        </View>
      </TouchableOpacity>

      <Text style={styles.sectionTitle}>Upcoming Tasks</Text>
      <View style={styles.taskCard}>
        <View style={styles.taskItem}>
          <Text style={{ fontSize: 20 }}>💧</Text>
          <View style={styles.taskContent}>
            <Text style={styles.taskTitle}>Irrigation - Plot A</Text>
            <Text style={styles.taskDue}>Due today</Text>
          </View>
        </View>
        <View style={styles.taskItem}>
          <Text style={{ fontSize: 20 }}>🧪</Text>
          <View style={styles.taskContent}>
            <Text style={styles.taskTitle}>Fertilizer Application</Text>
            <Text style={styles.taskDue}>Due tomorrow</Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#1B5E20',
    padding: 24,
    paddingTop: 16,
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  subGreeting: {
    fontSize: 14,
    color: '#C8E6C9',
    marginTop: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 16,
    marginTop: -20,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 4,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1B5E20',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    paddingHorizontal: 16,
    paddingTop: 24,
    paddingBottom: 12,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 12,
  },
  actionCard: {
    width: '25%',
    alignItems: 'center',
    padding: 8,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionLabel: {
    fontSize: 12,
    color: '#333',
    marginTop: 8,
    textAlign: 'center',
  },
  kycCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
  },
  kycHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  kycStatus: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4CAF50',
    marginLeft: 8,
  },
  kycText: {
    fontSize: 14,
    color: '#666',
  },
  taskCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  taskItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  taskContent: {
    marginLeft: 12,
    flex: 1,
  },
  taskTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
  },
  taskDue: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  eligibilityCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#2196F3',
  },
  eligibilityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  eligibilityInfo: {
    marginLeft: 12,
    flex: 1,
  },
  eligibilityTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  eligibilitySubtitle: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  eligibilityStats: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 12,
    gap: 24,
  },
  eligibilityStat: {
    alignItems: 'center',
  },
  eligibilityStatValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1B5E20',
  },
  eligibilityStatLabel: {
    fontSize: 12,
    color: '#666',
  },
});
