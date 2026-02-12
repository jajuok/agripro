import { Stack } from 'expo-router';
import { COLORS } from '@/utils/constants';

export default function TasksLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: COLORS.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '600' },
      }}
    >
      <Stack.Screen name="[taskId]" options={{ title: 'Task Details' }} />
      <Stack.Screen name="create" options={{ title: 'Create Task' }} />
    </Stack>
  );
}
