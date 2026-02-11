import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import DateTimePicker from '@react-native-community/datetimepicker';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useAuthStore } from '@/store/auth';
import { useKYCStore } from '@/store/kyc';
import { Button } from '@/components/Button';

export default function PersonalInfoScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { isLoading, completeStep } = useKYCStore();

  const [nationalId, setNationalId] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState(new Date(1990, 0, 1));
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [gender, setGender] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [physicalAddress, setPhysicalAddress] = useState('');
  const [postalAddress, setPostalAddress] = useState('');
  const [postalCode, setPostalCode] = useState('');

  const farmerId = user?.farmerId;

  const handleDateChange = (event: any, selectedDate?: Date) => {
    setShowDatePicker(Platform.OS === 'ios');
    if (selectedDate) {
      setDateOfBirth(selectedDate);
    }
  };

  const handleSubmit = async () => {
    // Validation
    if (!nationalId || !gender || !phoneNumber || !physicalAddress) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    if (nationalId.length < 6) {
      Alert.alert('Error', 'Please enter a valid National ID number');
      return;
    }

    if (phoneNumber.length < 10) {
      Alert.alert('Error', 'Please enter a valid phone number');
      return;
    }

    if (!farmerId) {
      Alert.alert('Error', 'Farmer ID not found');
      return;
    }

    try {
      const personalData = {
        national_id: nationalId,
        date_of_birth: dateOfBirth.toISOString().split('T')[0],
        gender,
        phone_number: phoneNumber,
        physical_address: physicalAddress,
        postal_address: postalAddress || undefined,
        postal_code: postalCode || undefined,
      };

      await completeStep(farmerId, 'personal_info', personalData);

      Alert.alert('Success', 'Personal information saved successfully', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to save personal information');
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Personal Information</Text>
          <Text style={styles.subtitle}>
            Provide your personal details for identity verification
          </Text>
        </View>

        {/* Form */}
        <View style={styles.form} testID="personal-info-form">
          {/* National ID */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>
              National ID Number <Text style={styles.required}>*</Text>
            </Text>
            <TextInput
              style={styles.input}
              value={nationalId}
              onChangeText={setNationalId}
              placeholder="Enter your National ID number"
              placeholderTextColor={COLORS.gray[400]}
              keyboardType="numeric"
              maxLength={10}
              testID="national-id-input"
            />
          </View>

          {/* Date of Birth */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>
              Date of Birth <Text style={styles.required}>*</Text>
            </Text>
            <TouchableOpacity
              style={styles.dateInput}
              onPress={() => setShowDatePicker(true)}
              testID="dob-input"
            >
              <Text style={styles.dateText}>{dateOfBirth.toLocaleDateString()}</Text>
              <Text style={styles.dateIcon}>📅</Text>
            </TouchableOpacity>

            {showDatePicker && (
              <DateTimePicker
                value={dateOfBirth}
                mode="date"
                display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                onChange={handleDateChange}
                maximumDate={new Date()}
                minimumDate={new Date(1920, 0, 1)}
              />
            )}
          </View>

          {/* Gender */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>
              Gender <Text style={styles.required}>*</Text>
            </Text>
            <View style={styles.radioGroup}>
              <TouchableOpacity
                style={[styles.radioButton, gender === 'male' && styles.radioButtonSelected]}
                onPress={() => setGender('male')}
                testID="gender-male-button"
              >
                <View style={styles.radioCircle}>
                  {gender === 'male' && <View style={styles.radioInner} />}
                </View>
                <Text style={styles.radioLabel}>Male</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.radioButton, gender === 'female' && styles.radioButtonSelected]}
                onPress={() => setGender('female')}
                testID="gender-female-button"
              >
                <View style={styles.radioCircle}>
                  {gender === 'female' && <View style={styles.radioInner} />}
                </View>
                <Text style={styles.radioLabel}>Female</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.radioButton, gender === 'other' && styles.radioButtonSelected]}
                onPress={() => setGender('other')}
                testID="gender-other-button"
              >
                <View style={styles.radioCircle}>
                  {gender === 'other' && <View style={styles.radioInner} />}
                </View>
                <Text style={styles.radioLabel}>Other</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Phone Number */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>
              Phone Number <Text style={styles.required}>*</Text>
            </Text>
            <TextInput
              style={styles.input}
              value={phoneNumber}
              onChangeText={setPhoneNumber}
              placeholder="0712345678"
              placeholderTextColor={COLORS.gray[400]}
              keyboardType="phone-pad"
              maxLength={15}
              testID="phone-input"
            />
          </View>

          {/* Physical Address */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>
              Physical Address <Text style={styles.required}>*</Text>
            </Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={physicalAddress}
              onChangeText={setPhysicalAddress}
              placeholder="Enter your residential address"
              placeholderTextColor={COLORS.gray[400]}
              multiline
              numberOfLines={3}
              textAlignVertical="top"
              testID="address-input"
            />
          </View>

          {/* Postal Address */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Postal Address (Optional)</Text>
            <TextInput
              style={styles.input}
              value={postalAddress}
              onChangeText={setPostalAddress}
              placeholder="P.O. Box"
              placeholderTextColor={COLORS.gray[400]}
            />
          </View>

          {/* Postal Code */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Postal Code (Optional)</Text>
            <TextInput
              style={styles.input}
              value={postalCode}
              onChangeText={setPostalCode}
              placeholder="e.g., 00100"
              placeholderTextColor={COLORS.gray[400]}
              keyboardType="numeric"
              maxLength={10}
            />
          </View>

          {/* Submit Button */}
          <Button
            title="Save Personal Information"
            onPress={handleSubmit}
            loading={isLoading}
            disabled={isLoading}
            testID="personal-info-submit-button"
          />

          <TouchableOpacity style={styles.cancelButton} onPress={() => router.back()}>
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.gray[50],
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: SPACING.lg,
  },
  header: {
    marginBottom: SPACING.lg,
  },
  title: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: SPACING.xs,
  },
  subtitle: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[600],
    lineHeight: 22,
  },
  form: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.lg,
  },
  inputGroup: {
    marginBottom: SPACING.lg,
  },
  label: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '500',
    color: COLORS.gray[700],
    marginBottom: SPACING.xs,
  },
  required: {
    color: COLORS.error,
  },
  input: {
    backgroundColor: COLORS.gray[50],
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 8,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[900],
  },
  textArea: {
    minHeight: 80,
  },
  dateInput: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.gray[50],
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 8,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
  },
  dateText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[900],
  },
  dateIcon: {
    fontSize: 20,
  },
  radioGroup: {
    flexDirection: 'row',
    gap: SPACING.md,
  },
  radioButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    backgroundColor: COLORS.gray[50],
  },
  radioButtonSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  radioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: COLORS.gray[400],
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.xs,
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: COLORS.primary,
  },
  radioLabel: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
  },
  cancelButton: {
    alignItems: 'center',
    padding: SPACING.md,
    marginTop: SPACING.sm,
  },
  cancelButtonText: {
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
});
