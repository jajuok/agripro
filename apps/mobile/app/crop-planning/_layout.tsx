import { Stack } from 'expo-router';
import { COLORS } from '@/utils/constants';

export default function CropPlanningLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: COLORS.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '600' },
      }}
    >
      <Stack.Screen name="index" options={{ title: 'Crop Planning' }} />
      <Stack.Screen name="create" options={{ title: 'Create Plan' }} />
      <Stack.Screen name="alerts" options={{ title: 'Alerts' }} />
      <Stack.Screen name="[id]/index" options={{ title: 'Plan Details' }} />
      <Stack.Screen name="[id]/activities" options={{ title: 'Activities' }} />
      <Stack.Screen name="[id]/activity-complete" options={{ title: 'Complete Activity', presentation: 'modal' }} />
      <Stack.Screen name="[id]/inputs" options={{ title: 'Inputs' }} />
      <Stack.Screen name="[id]/irrigation" options={{ title: 'Irrigation' }} />
    </Stack>
  );
}
