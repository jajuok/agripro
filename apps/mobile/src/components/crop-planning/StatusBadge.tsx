import { View, Text, StyleSheet } from 'react-native';
import {
  CROP_PLAN_STATUS_COLORS,
  ACTIVITY_STATUS_COLORS,
  PROCUREMENT_STATUS_COLORS,
  ALERT_SEVERITY_COLORS,
} from '@/utils/constants';

type Props = {
  status: string;
  type?: 'plan' | 'activity' | 'procurement' | 'alert';
  testID?: string;
};

const COLOR_MAPS: Record<string, Record<string, string>> = {
  plan: CROP_PLAN_STATUS_COLORS,
  activity: ACTIVITY_STATUS_COLORS,
  procurement: PROCUREMENT_STATUS_COLORS,
  alert: ALERT_SEVERITY_COLORS,
};

export default function StatusBadge({ status, type = 'plan', testID }: Props) {
  const colorMap = COLOR_MAPS[type] || CROP_PLAN_STATUS_COLORS;
  const color = colorMap[status] || '#9E9E9E';
  const label = status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <View style={[styles.badge, { backgroundColor: `${color}18` }]} testID={testID}>
      <View style={[styles.dot, { backgroundColor: color }]} />
      <Text style={[styles.text, { color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  text: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
});
