import { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Stack } from 'expo-router';

const FAQ_ITEMS = [
  {
    question: 'How do I register my farm?',
    answer:
      'Go to the Farms tab and tap "Register New Farm". You\'ll need to provide your farm\'s location, boundary, land details, and supporting documents. The process is guided step-by-step.',
  },
  {
    question: 'What documents do I need for KYC verification?',
    answer:
      'You\'ll need a valid national ID or passport, proof of land ownership (title deed or lease agreement), and optionally a recent bank statement. Go to Profile > KYC Documents to start the process.',
  },
  {
    question: 'How do I apply for government schemes?',
    answer:
      'Navigate to the Schemes section from the home screen. Browse available schemes, check eligibility requirements, and submit your application. You\'ll be notified of any status changes.',
  },
  {
    question: 'How do I create a crop plan?',
    answer:
      'Go to the Crop Planning tab, tap "New Plan", select your farm and crop, then choose a planting template or create a custom plan. The system will generate recommended activities and timelines.',
  },
  {
    question: 'Can I manage my account details?',
    answer:
      'Yes! Go to Profile > Edit Profile to update your name and email. Your phone number is linked to your account and cannot be changed. Contact support if you need to update your phone number.',
  },
];

export default function SupportScreen() {
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <>
      <Stack.Screen options={{ title: 'Help & Support' }} />
      <ScrollView style={styles.container}>
        <Text style={styles.sectionTitle}>Frequently Asked Questions</Text>
        {FAQ_ITEMS.map((item, index) => (
          <View key={index} style={styles.faqItem}>
            <TouchableOpacity
              style={styles.faqQuestion}
              onPress={() => setExpanded(expanded === index ? null : index)}
            >
              <Text style={styles.faqQuestionText}>{item.question}</Text>
              <Text style={styles.faqChevron}>
                {expanded === index ? '−' : '+'}
              </Text>
            </TouchableOpacity>
            {expanded === index && (
              <Text style={styles.faqAnswer}>{item.answer}</Text>
            )}
          </View>
        ))}

        <Text style={styles.sectionTitle}>Contact Us</Text>
        <View style={styles.contactCard}>
          <View style={styles.contactRow}>
            <Text style={styles.contactIcon}>📧</Text>
            <View>
              <Text style={styles.contactLabel}>Email</Text>
              <Text style={styles.contactValue}>support@agripro.co.ke</Text>
            </View>
          </View>
          <View style={styles.divider} />
          <View style={styles.contactRow}>
            <Text style={styles.contactIcon}>📞</Text>
            <View>
              <Text style={styles.contactLabel}>Phone</Text>
              <Text style={styles.contactValue}>+254 700 000 000</Text>
            </View>
          </View>
          <View style={styles.divider} />
          <View style={styles.contactRow}>
            <Text style={styles.contactIcon}>🕐</Text>
            <View>
              <Text style={styles.contactLabel}>Hours</Text>
              <Text style={styles.contactValue}>Mon-Fri 8:00 AM - 6:00 PM EAT</Text>
            </View>
          </View>
        </View>

        <Text style={styles.versionText}>AgriPro v0.1.0</Text>
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#999',
    textTransform: 'uppercase',
    paddingHorizontal: 16,
    paddingTop: 24,
    paddingBottom: 8,
  },
  faqItem: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  faqQuestion: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  faqQuestionText: {
    fontSize: 15,
    color: '#333',
    fontWeight: '500',
    flex: 1,
    marginRight: 12,
  },
  faqChevron: {
    fontSize: 20,
    color: '#1B5E20',
    fontWeight: 'bold',
  },
  faqAnswer: {
    fontSize: 14,
    color: '#666',
    lineHeight: 22,
    paddingHorizontal: 16,
    paddingBottom: 14,
  },
  contactCard: {
    backgroundColor: '#fff',
    marginHorizontal: 0,
  },
  contactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  contactIcon: {
    fontSize: 24,
    marginRight: 16,
  },
  contactLabel: {
    fontSize: 13,
    color: '#999',
  },
  contactValue: {
    fontSize: 15,
    color: '#333',
    fontWeight: '500',
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: '#f0f0f0',
    marginLeft: 56,
  },
  versionText: {
    textAlign: 'center',
    color: '#999',
    fontSize: 12,
    paddingVertical: 24,
  },
});
