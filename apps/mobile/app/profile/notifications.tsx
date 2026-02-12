import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Switch, ScrollView } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const PREFS_KEY = 'notification_preferences';

type Preferences = {
  pushNotifications: boolean;
  smsAlerts: boolean;
  emailUpdates: boolean;
  schemeDeadlines: boolean;
  weatherAlerts: boolean;
};

const DEFAULT_PREFS: Preferences = {
  pushNotifications: true,
  smsAlerts: true,
  emailUpdates: false,
  schemeDeadlines: true,
  weatherAlerts: true,
};

export default function NotificationsScreen() {
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFS);

  useEffect(() => {
    AsyncStorage.getItem(PREFS_KEY).then((data) => {
      if (data) {
        setPrefs({ ...DEFAULT_PREFS, ...JSON.parse(data) });
      }
    });
  }, []);

  const toggle = (key: keyof Preferences) => {
    const updated = { ...prefs, [key]: !prefs[key] };
    setPrefs(updated);
    AsyncStorage.setItem(PREFS_KEY, JSON.stringify(updated));
  };

  const items: { key: keyof Preferences; label: string; description: string }[] = [
    { key: 'pushNotifications', label: 'Push Notifications', description: 'Receive push notifications on your device' },
    { key: 'smsAlerts', label: 'SMS Alerts', description: 'Get important alerts via text message' },
    { key: 'emailUpdates', label: 'Email Updates', description: 'Receive updates and reports via email' },
    { key: 'schemeDeadlines', label: 'Scheme Deadlines', description: 'Reminders for upcoming scheme deadlines' },
    { key: 'weatherAlerts', label: 'Weather Alerts', description: 'Severe weather warnings for your farm area' },
  ];

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.sectionHeader}>Notification Preferences</Text>
      {items.map((item) => (
        <View key={item.key} style={styles.row}>
          <View style={styles.textContainer}>
            <Text style={styles.label}>{item.label}</Text>
            <Text style={styles.description}>{item.description}</Text>
          </View>
          <Switch
            value={prefs[item.key]}
            onValueChange={() => toggle(item.key)}
            trackColor={{ false: '#ddd', true: '#A5D6A7' }}
            thumbColor={prefs[item.key] ? '#1B5E20' : '#f4f3f4'}
          />
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  sectionHeader: {
    fontSize: 14,
    fontWeight: '600',
    color: '#999',
    textTransform: 'uppercase',
    paddingHorizontal: 16,
    paddingTop: 24,
    paddingBottom: 8,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  textContainer: {
    flex: 1,
    marginRight: 12,
  },
  label: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  description: {
    fontSize: 13,
    color: '#999',
    marginTop: 2,
  },
});
