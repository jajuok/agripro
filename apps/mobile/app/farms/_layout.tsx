import { Stack } from 'expo-router';
import { COLORS } from '@/utils/constants';

export default function FarmsLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: COLORS.primary,
        },
        headerTintColor: COLORS.white,
        headerTitleStyle: {
          fontWeight: '600',
        },
      }}
    >
      <Stack.Screen
        name="add"
        options={{
          title: 'Add New Farm',
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="[id]/index"
        options={{
          title: 'Farm Details',
        }}
      />
      <Stack.Screen
        name="[id]/boundary"
        options={{
          title: 'Farm Boundary',
          headerShown: false,
        }}
      />
      <Stack.Screen
        name="[id]/land-details"
        options={{
          title: 'Land Details',
        }}
      />
      <Stack.Screen
        name="[id]/documents"
        options={{
          title: 'Documents',
        }}
      />
      <Stack.Screen
        name="[id]/soil-water"
        options={{
          title: 'Soil & Water',
        }}
      />
      <Stack.Screen
        name="[id]/crops"
        options={{
          title: 'Crop History',
        }}
      />
      <Stack.Screen
        name="[id]/review"
        options={{
          title: 'Review & Submit',
        }}
      />
    </Stack>
  );
}
