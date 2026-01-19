import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';

type Farm = {
  id: string;
  name: string;
  location: string;
  acreage: number;
  crops: string[];
};

const farms: Farm[] = [
  { id: '1', name: 'Main Farm', location: 'Nakuru County', acreage: 5.5, crops: ['Maize', 'Beans'] },
  { id: '2', name: 'Riverside Plot', location: 'Nakuru County', acreage: 3.2, crops: ['Wheat'] },
  { id: '3', name: 'Hill Farm', location: 'Nakuru County', acreage: 3.8, crops: ['Potatoes'] },
];

export default function FarmsScreen() {
  const renderFarm = ({ item }: { item: Farm }) => (
    <TouchableOpacity
      style={styles.farmCard}
      onPress={() => router.push(`/farms/${item.id}` as any)}
    >
      <View style={styles.farmHeader}>
        <View style={styles.farmIcon}>
          <Ionicons name="leaf" size={24} color="#1B5E20" />
        </View>
        <View style={styles.farmInfo}>
          <Text style={styles.farmName}>{item.name}</Text>
          <Text style={styles.farmLocation}>
            <Ionicons name="location-outline" size={12} /> {item.location}
          </Text>
        </View>
        <Ionicons name="chevron-forward" size={24} color="#ccc" />
      </View>
      <View style={styles.farmDetails}>
        <View style={styles.detailItem}>
          <Text style={styles.detailValue}>{item.acreage}</Text>
          <Text style={styles.detailLabel}>Hectares</Text>
        </View>
        <View style={styles.detailItem}>
          <Text style={styles.detailValue}>{item.crops.length}</Text>
          <Text style={styles.detailLabel}>Crops</Text>
        </View>
        <View style={styles.cropTags}>
          {item.crops.map((crop, index) => (
            <View key={index} style={styles.cropTag}>
              <Text style={styles.cropTagText}>{crop}</Text>
            </View>
          ))}
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={farms}
        renderItem={renderFarm}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={styles.totalFarms}>{farms.length} Farms</Text>
            <Text style={styles.totalAcreage}>
              Total: {farms.reduce((sum, f) => sum + f.acreage, 0).toFixed(1)} ha
            </Text>
          </View>
        }
      />
      <TouchableOpacity
        style={styles.fab}
        onPress={() => router.push('/farms/add' as any)}
      >
        <Ionicons name="add" size={28} color="#fff" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  list: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  totalFarms: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  totalAcreage: {
    fontSize: 14,
    color: '#666',
  },
  farmCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
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
    backgroundColor: '#E8F5E9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  farmInfo: {
    flex: 1,
    marginLeft: 12,
  },
  farmName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  farmLocation: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  farmDetails: {
    flexDirection: 'row',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  detailItem: {
    marginRight: 24,
  },
  detailValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1B5E20',
  },
  detailLabel: {
    fontSize: 12,
    color: '#999',
  },
  cropTags: {
    flex: 1,
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-end',
  },
  cropTag: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginLeft: 4,
    marginBottom: 4,
  },
  cropTagText: {
    fontSize: 12,
    color: '#1B5E20',
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
});
