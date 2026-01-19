import { View, Text, StyleSheet, SectionList, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

type Task = {
  id: string;
  title: string;
  farm: string;
  dueDate: string;
  priority: 'high' | 'medium' | 'low';
  completed: boolean;
};

const tasks = {
  today: [
    { id: '1', title: 'Irrigation - Plot A', farm: 'Main Farm', dueDate: 'Today', priority: 'high', completed: false },
    { id: '2', title: 'Check pest traps', farm: 'Main Farm', dueDate: 'Today', priority: 'medium', completed: true },
  ] as Task[],
  upcoming: [
    { id: '3', title: 'Fertilizer Application', farm: 'Hill Farm', dueDate: 'Tomorrow', priority: 'high', completed: false },
    { id: '4', title: 'Soil testing', farm: 'Riverside Plot', dueDate: 'In 3 days', priority: 'low', completed: false },
    { id: '5', title: 'Harvest preparation', farm: 'Main Farm', dueDate: 'Next week', priority: 'medium', completed: false },
  ] as Task[],
};

const priorityColors = {
  high: '#D32F2F',
  medium: '#FF9800',
  low: '#4CAF50',
};

export default function TasksScreen() {
  const sections = [
    { title: 'Today', data: tasks.today },
    { title: 'Upcoming', data: tasks.upcoming },
  ];

  const renderTask = ({ item }: { item: Task }) => (
    <TouchableOpacity style={styles.taskCard}>
      <TouchableOpacity style={styles.checkbox}>
        {item.completed ? (
          <Ionicons name="checkbox" size={24} color="#4CAF50" />
        ) : (
          <Ionicons name="square-outline" size={24} color="#ccc" />
        )}
      </TouchableOpacity>
      <View style={styles.taskContent}>
        <Text style={[styles.taskTitle, item.completed && styles.completedTask]}>
          {item.title}
        </Text>
        <Text style={styles.taskFarm}>{item.farm}</Text>
      </View>
      <View style={styles.taskMeta}>
        <View style={[styles.priorityDot, { backgroundColor: priorityColors[item.priority] }]} />
        <Text style={styles.taskDue}>{item.dueDate}</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <SectionList
        sections={sections}
        renderItem={renderTask}
        renderSectionHeader={({ section }) => (
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>{section.title}</Text>
            <Text style={styles.sectionCount}>{section.data.length} tasks</Text>
          </View>
        )}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        stickySectionHeadersEnabled={false}
      />
      <TouchableOpacity style={styles.fab}>
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
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  sectionCount: {
    fontSize: 14,
    color: '#999',
  },
  taskCard: {
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
    elevation: 2,
  },
  checkbox: {
    marginRight: 12,
  },
  taskContent: {
    flex: 1,
  },
  taskTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  completedTask: {
    textDecorationLine: 'line-through',
    color: '#999',
  },
  taskFarm: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  taskMeta: {
    alignItems: 'flex-end',
  },
  priorityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginBottom: 4,
  },
  taskDue: {
    fontSize: 12,
    color: '#999',
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
