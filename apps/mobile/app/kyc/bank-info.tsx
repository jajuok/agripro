import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useAuthStore } from '@/store/auth';
import { useKYCStore } from '@/store/kyc';
import { Button } from '@/components/Button';

const KENYAN_BANKS = [
  'KCB Bank',
  'Equity Bank',
  'Co-operative Bank',
  'NCBA Bank',
  'Stanbic Bank',
  'Standard Chartered',
  'Absa Bank',
  'Family Bank',
  'DTB Bank',
  'I&M Bank',
  'Sidian Bank',
  'Credit Bank',
  'Prime Bank',
  'Gulf African Bank',
  'Other',
];

export default function BankInfoScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { isLoading, completeStep } = useKYCStore();

  const [bankName, setBankName] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [accountName, setAccountName] = useState('');
  const [branchName, setBranchName] = useState('');
  const [showBankList, setShowBankList] = useState(false);

  const farmerId = user?.farmerId;

  const handleSelectBank = (bank: string) => {
    setBankName(bank);
    setShowBankList(false);
  };

  const handleSubmit = async () => {
    // Validation
    if (!bankName || !accountNumber || !accountName) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    if (accountNumber.length < 10) {
      Alert.alert('Error', 'Please enter a valid account number');
      return;
    }

    if (!farmerId) {
      Alert.alert('Error', 'Farmer ID not found');
      return;
    }

    try {
      const bankData = {
        bank_name: bankName,
        account_number: accountNumber,
        account_name: accountName,
        branch_name: branchName || undefined,
      };

      await completeStep(farmerId, 'bank_info', bankData);

      Alert.alert('Success', 'Bank information saved successfully', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to save bank information');
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Bank Information</Text>
          <Text style={styles.subtitle}>
            Provide your bank account details for payments and disbursements
          </Text>
        </View>

        {/* Info Box */}
        <View style={styles.infoBox}>
          <Text style={styles.infoIcon}>ℹ️</Text>
          <Text style={styles.infoText}>
            Your bank information will be used for receiving subsidies, loan disbursements, and
            payments. Ensure the account name matches your registered name.
          </Text>
        </View>

        {/* Form */}
        <View style={styles.form} testID="bank-info-form">
          {/* Bank Name */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>
              Bank Name <Text style={styles.required}>*</Text>
            </Text>
            <TouchableOpacity
              style={styles.selectInput}
              onPress={() => setShowBankList(!showBankList)}
              testID="bank-name-select"
            >
              <Text style={[styles.selectText, !bankName && styles.selectPlaceholder]}>
                {bankName || 'Select your bank'}
              </Text>
              <Text style={styles.selectArrow}>{showBankList ? '▲' : '▼'}</Text>
            </TouchableOpacity>

            {showBankList && (
              <View style={styles.dropdown}>
                <ScrollView style={styles.dropdownScroll}>
                  {KENYAN_BANKS.map((bank) => (
                    <TouchableOpacity
                      key={bank}
                      style={styles.dropdownItem}
                      onPress={() => handleSelectBank(bank)}
                    >
                      <Text style={styles.dropdownItemText}>{bank}</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            )}
          </View>

          {/* Account Number */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>
              Account Number <Text style={styles.required}>*</Text>
            </Text>
            <TextInput
              style={styles.input}
              value={accountNumber}
              onChangeText={setAccountNumber}
              placeholder="Enter your account number"
              placeholderTextColor={COLORS.gray[400]}
              keyboardType="numeric"
              maxLength={20}
              testID="account-number-input"
            />
          </View>

          {/* Account Name */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>
              Account Name <Text style={styles.required}>*</Text>
            </Text>
            <TextInput
              style={styles.input}
              value={accountName}
              onChangeText={setAccountName}
              placeholder="Enter account holder name"
              placeholderTextColor={COLORS.gray[400]}
              autoCapitalize="words"
              testID="account-name-input"
            />
            <Text style={styles.hint}>Must match the name on your National ID</Text>
          </View>

          {/* Branch Name */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Branch Name (Optional)</Text>
            <TextInput
              style={styles.input}
              value={branchName}
              onChangeText={setBranchName}
              placeholder="Enter branch name"
              placeholderTextColor={COLORS.gray[400]}
              autoCapitalize="words"
              testID="branch-name-input"
            />
          </View>

          {/* Security Note */}
          <View style={styles.securityNote}>
            <Text style={styles.securityIcon}>🔒</Text>
            <Text style={styles.securityText}>
              Your banking information is encrypted and securely stored
            </Text>
          </View>

          {/* Submit Button */}
          <Button
            title="Save Bank Information"
            onPress={handleSubmit}
            loading={isLoading}
            disabled={isLoading}
            testID="bank-info-submit-button"
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
  infoBox: {
    flexDirection: 'row',
    backgroundColor: COLORS.primary + '10',
    borderRadius: 8,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  infoIcon: {
    fontSize: 20,
    marginRight: SPACING.sm,
  },
  infoText: {
    flex: 1,
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
    lineHeight: 20,
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
  selectInput: {
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
  selectText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[900],
  },
  selectPlaceholder: {
    color: COLORS.gray[400],
  },
  selectArrow: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[500],
  },
  dropdown: {
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 8,
    marginTop: SPACING.xs,
    maxHeight: 200,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  dropdownScroll: {
    maxHeight: 200,
  },
  dropdownItem: {
    padding: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray[100],
  },
  dropdownItemText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[900],
  },
  hint: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[500],
    marginTop: SPACING.xs / 2,
  },
  securityNote: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.success + '10',
    borderRadius: 8,
    padding: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  securityIcon: {
    fontSize: 16,
    marginRight: SPACING.xs,
  },
  securityText: {
    flex: 1,
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[600],
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
