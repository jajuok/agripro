import { Stack } from 'expo-router';
import { COLORS } from '@/utils/constants';

export default function KYCLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: COLORS.primary,
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <Stack.Screen
        name="index"
        options={{
          title: 'KYC Verification',
        }}
      />
      <Stack.Screen
        name="personal-info"
        options={{
          title: 'Personal Information',
        }}
      />
      <Stack.Screen
        name="documents"
        options={{
          title: 'Documents',
        }}
      />
      <Stack.Screen
        name="biometrics"
        options={{
          title: 'Biometrics',
        }}
      />
      <Stack.Screen
        name="bank-info"
        options={{
          title: 'Bank Information',
        }}
      />
      <Stack.Screen
        name="submit"
        options={{
          title: 'Review & Submit',
        }}
      />
    </Stack>
  );
}
