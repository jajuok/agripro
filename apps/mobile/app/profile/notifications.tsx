import { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, Switch, ScrollView, ActivityIndicator } from 'react-native';
import { useAuthStore } from '@/store/auth';
import { notificationApi } from '@/services/api';

type Preferences = {
  push_enabled: boolean;
  sms_enabled: boolean;
  email_enabled: boolean;
  scheme_deadlines: boolean;
  weather_alerts: boolean;
  task_reminders: boolean;
  crop_alerts: boolean;
  market_prices: boolean;
};

const DEFAULT_PREFS: Preferences = {
  push_enabled: true,
  sms_enabled: true,
  email_enabled: false,
  scheme_deadlines: true,
  weather_alerts: true,
  task_reminders: true,
  crop_alerts: true,
  market_prices: true,
};

export default function NotificationsScreen() {
  const { user } = useAuthStore();
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const userId = user?.id;

  const fetchPreferences = useCallback(async () => {
    if (!userId) {
      setLoading(false);
      return;
    }
    try {
      const data = await notificationApi.getPreferences(userId);
      setPrefs({
        push_enabled: data.push_enabled ?? DEFAULT_PREFS.push_enabled,
        sms_enabled: data.sms_enabled ?? DEFAULT_PREFS.sms_enabled,
        email_enabled: data.email_enabled ?? DEFAULT_PREFS.email_enabled,
        scheme_deadlines: data.scheme_deadlines ?? DEFAULT_PREFS.scheme_deadlines,
        weather_alerts: data.weather_alerts ?? DEFAULT_PREFS.weather_alerts,
        task_reminders: data.task_reminders ?? DEFAULT_PREFS.task_reminders,
        crop_alerts: data.crop_alerts ?? DEFAULT_PREFS.crop_alerts,
        market_prices: data.market_prices ?? DEFAULT_PREFS.market_prices,
      });
    } catch {
      // Keep defaults on error
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchPreferences();
  }, [fetchPreferences]);

  const toggle = async (key: keyof Preferences) => {
    if (!userId || saving) return;

    const updated = { ...prefs, [key]: !prefs[key] };
    setPrefs(updated);
    setSaving(true);

    try {
      await notificationApi.updatePreferences(userId, { [key]: updated[key] });
    } catch {
      // Revert on error
      setPrefs(prefs);
    } finally {
      setSaving(false);
    }
  };

  const channelItems: { key: keyof Preferences; label: string; description: string }[] = [
    { key: 'push_enabled', label: 'Push Notifications', description: 'Receive push notifications on your device' },
    { key: 'sms_enabled', label: 'SMS Alerts', description: 'Get important alerts via text message' },
    { key: 'email_enabled', label: 'Email Updates', description: 'Receive updates and reports via email' },
  ];

  const categoryItems: { key: keyof Preferences; label: string; description: string }[] = [
    { key: 'scheme_deadlines', label: 'Scheme Deadlines', description: 'Reminders for upcoming scheme deadlines' },
    { key: 'weather_alerts', label: 'Weather Alerts', description: 'Severe weather warnings for your farm area' },
    { key: 'task_reminders', label: 'Task Reminders', description: 'Reminders for upcoming farm tasks' },
    { key: 'crop_alerts', label: 'Crop Alerts', description: 'Alerts about crop health and conditions' },
    { key: 'market_prices', label: 'Market Prices', description: 'Updates on market price changes' },
  ];

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1B5E20" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.sectionHeader}>Channels</Text>
      {channelItems.map((item) => (
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
            disabled={saving}
          />
        </View>
      ))}

      <Text style={styles.sectionHeader}>Categories</Text>
      {categoryItems.map((item) => (
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
            disabled={saving}
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
