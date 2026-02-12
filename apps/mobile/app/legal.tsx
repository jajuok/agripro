import { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Stack } from 'expo-router';

type Tab = 'terms' | 'privacy';

export default function LegalScreen() {
  const [activeTab, setActiveTab] = useState<Tab>('terms');

  return (
    <>
      <Stack.Screen options={{ title: 'Terms & Privacy' }} />
      <View style={styles.container}>
        <View style={styles.tabBar}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'terms' && styles.activeTab]}
            onPress={() => setActiveTab('terms')}
          >
            <Text style={[styles.tabText, activeTab === 'terms' && styles.activeTabText]}>
              Terms of Service
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'privacy' && styles.activeTab]}
            onPress={() => setActiveTab('privacy')}
          >
            <Text style={[styles.tabText, activeTab === 'privacy' && styles.activeTabText]}>
              Privacy Policy
            </Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content}>
          {activeTab === 'terms' ? <TermsContent /> : <PrivacyContent />}
        </ScrollView>
      </View>
    </>
  );
}

function TermsContent() {
  return (
    <View style={styles.textContainer}>
      <Text style={styles.heading}>Terms of Service</Text>
      <Text style={styles.updated}>Last updated: February 2026</Text>

      <Text style={styles.subheading}>1. Acceptance of Terms</Text>
      <Text style={styles.body}>
        By accessing or using the AgriPro mobile application, you agree to be bound by these Terms
        of Service. If you do not agree to these terms, please do not use the application.
      </Text>

      <Text style={styles.subheading}>2. Use of Service</Text>
      <Text style={styles.body}>
        AgriPro provides farm management, crop planning, and agricultural support tools. You agree
        to use the service only for lawful purposes related to agricultural management and planning.
      </Text>

      <Text style={styles.subheading}>3. Account Registration</Text>
      <Text style={styles.body}>
        You must provide accurate and complete information when creating an account. You are
        responsible for maintaining the confidentiality of your account credentials and for all
        activities that occur under your account.
      </Text>

      <Text style={styles.subheading}>4. Data Accuracy</Text>
      <Text style={styles.body}>
        You are responsible for the accuracy of farm data, crop records, and documents you submit
        through the application. AgriPro is not liable for decisions made based on inaccurate data
        you provide.
      </Text>

      <Text style={styles.subheading}>5. Service Availability</Text>
      <Text style={styles.body}>
        We strive to maintain continuous service availability but do not guarantee uninterrupted
        access. The service may be temporarily unavailable for maintenance or updates.
      </Text>

      <Text style={styles.subheading}>6. Limitation of Liability</Text>
      <Text style={styles.body}>
        AgriPro shall not be liable for any indirect, incidental, or consequential damages arising
        from your use of the service, including but not limited to crop losses, financial losses, or
        missed scheme deadlines.
      </Text>
    </View>
  );
}

function PrivacyContent() {
  return (
    <View style={styles.textContainer}>
      <Text style={styles.heading}>Privacy Policy</Text>
      <Text style={styles.updated}>Last updated: February 2026</Text>

      <Text style={styles.subheading}>1. Information We Collect</Text>
      <Text style={styles.body}>
        We collect personal information you provide during registration (name, phone number, email),
        farm data (location, boundaries, crop records), KYC documents, and device information for
        service functionality.
      </Text>

      <Text style={styles.subheading}>2. How We Use Your Information</Text>
      <Text style={styles.body}>
        Your information is used to provide farm management services, process scheme applications,
        generate crop planning recommendations, and send relevant notifications. We may use
        anonymized data to improve our services.
      </Text>

      <Text style={styles.subheading}>3. Data Storage and Security</Text>
      <Text style={styles.body}>
        Your data is stored securely using industry-standard encryption. Sensitive information like
        authentication tokens are stored using device secure storage. We implement appropriate
        technical and organizational measures to protect your data.
      </Text>

      <Text style={styles.subheading}>4. Data Sharing</Text>
      <Text style={styles.body}>
        We do not sell your personal data. We may share data with government agricultural bodies
        only when required for scheme applications you initiate, or when required by law. Third-party
        service providers are bound by confidentiality agreements.
      </Text>

      <Text style={styles.subheading}>5. Your Rights</Text>
      <Text style={styles.body}>
        You have the right to access, correct, or delete your personal data. You can update your
        profile information through the app. To request data deletion, contact our support team.
      </Text>

      <Text style={styles.subheading}>6. Contact</Text>
      <Text style={styles.body}>
        For privacy-related inquiries, please contact us at support@agripro.co.ke or through the
        Help & Support section in the app.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#1B5E20',
  },
  tabText: {
    fontSize: 15,
    color: '#999',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#1B5E20',
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  textContainer: {
    padding: 16,
  },
  heading: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  updated: {
    fontSize: 13,
    color: '#999',
    marginBottom: 20,
  },
  subheading: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginTop: 20,
    marginBottom: 8,
  },
  body: {
    fontSize: 14,
    color: '#666',
    lineHeight: 22,
  },
});
