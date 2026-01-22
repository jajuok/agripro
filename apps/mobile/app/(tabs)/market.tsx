import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
// Using Text-based icons instead of Ionicons to avoid font loading issues

type PriceItem = {
  commodity: string;
  price: number;
  unit: string;
  change: number;
};

const marketPrices: PriceItem[] = [
  { commodity: 'Maize', price: 45.50, unit: 'kg', change: 2.5 },
  { commodity: 'Wheat', price: 52.00, unit: 'kg', change: -1.2 },
  { commodity: 'Beans', price: 120.00, unit: 'kg', change: 5.0 },
  { commodity: 'Potatoes', price: 35.00, unit: 'kg', change: 0 },
];

export default function MarketScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Market Prices</Text>
        <Text style={styles.headerSubtitle}>Updated 2 hours ago</Text>
      </View>

      <View style={styles.priceList}>
        {marketPrices.map((item, index) => (
          <View key={index} style={styles.priceCard}>
            <View style={styles.commodityInfo}>
              <Text style={styles.commodityName}>{item.commodity}</Text>
              <Text style={styles.unit}>per {item.unit}</Text>
            </View>
            <View style={styles.priceInfo}>
              <Text style={styles.price}>KES {item.price.toFixed(2)}</Text>
              <View style={[styles.changeContainer, item.change >= 0 ? styles.positive : styles.negative]}>
                <Text style={{ fontSize: 12, color: item.change >= 0 ? '#4CAF50' : '#D32F2F' }}>
                  {item.change >= 0 ? '↑' : '↓'}
                </Text>
                <Text style={[styles.change, item.change >= 0 ? styles.positiveText : styles.negativeText]}>
                  {Math.abs(item.change)}%
                </Text>
              </View>
            </View>
          </View>
        ))}
      </View>

      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <View style={styles.actionsContainer}>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={{ fontSize: 24 }}>🏷️</Text>
          <Text style={styles.actionText}>List Produce</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={{ fontSize: 24 }}>👥</Text>
          <Text style={styles.actionText}>Find Buyers</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={{ fontSize: 24 }}>📄</Text>
          <Text style={styles.actionText}>Contracts</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.sectionTitle}>My Listings</Text>
      <View style={styles.emptyState}>
        <Text style={{ fontSize: 48 }}>🧺</Text>
        <Text style={styles.emptyText}>No active listings</Text>
        <TouchableOpacity style={styles.listButton}>
          <Text style={styles.listButtonText}>List Your Produce</Text>
        </TouchableOpacity>
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
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#C8E6C9',
    marginTop: 4,
  },
  priceList: {
    padding: 16,
    marginTop: -16,
  },
  priceCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  commodityInfo: {
    flex: 1,
  },
  commodityName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  unit: {
    fontSize: 12,
    color: '#999',
  },
  priceInfo: {
    alignItems: 'flex-end',
  },
  price: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1B5E20',
  },
  changeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  positive: {},
  negative: {},
  change: {
    fontSize: 12,
    marginLeft: 2,
  },
  positiveText: {
    color: '#4CAF50',
  },
  negativeText: {
    color: '#D32F2F',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
  },
  actionsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  actionText: {
    fontSize: 12,
    color: '#333',
    marginTop: 8,
  },
  emptyState: {
    backgroundColor: '#fff',
    margin: 16,
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    marginTop: 12,
  },
  listButton: {
    backgroundColor: '#1B5E20',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    marginTop: 16,
  },
  listButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
});
