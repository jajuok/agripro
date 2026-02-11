import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { COLORS } from '@/utils/constants';

type Props = {
  stages: string[];
  currentStage: string | null;
  testID?: string;
};

export default function GrowthStageTimeline({ stages, currentStage, testID }: Props) {
  if (stages.length === 0) return null;

  const currentIndex = currentStage ? stages.indexOf(currentStage) : -1;

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      style={styles.container}
      testID={testID}
    >
      {stages.map((stage, index) => {
        const isCompleted = currentIndex >= 0 && index < currentIndex;
        const isCurrent = index === currentIndex;
        const isPending = index > currentIndex || currentIndex < 0;

        return (
          <View key={stage} style={styles.stageItem}>
            <View style={styles.lineContainer}>
              {index > 0 && (
                <View
                  style={[
                    styles.line,
                    (isCompleted || isCurrent) ? styles.lineActive : styles.lineInactive,
                  ]}
                />
              )}
              <View
                style={[
                  styles.dot,
                  isCompleted && styles.dotCompleted,
                  isCurrent && styles.dotCurrent,
                  isPending && styles.dotPending,
                ]}
              >
                {isCompleted && <Text style={styles.checkmark}>{'\u2713'}</Text>}
                {isCurrent && <View style={styles.currentInner} />}
              </View>
              {index < stages.length - 1 && (
                <View
                  style={[
                    styles.line,
                    isCompleted ? styles.lineActive : styles.lineInactive,
                  ]}
                />
              )}
            </View>
            <Text
              style={[
                styles.label,
                isCurrent && styles.labelCurrent,
                isCompleted && styles.labelCompleted,
              ]}
              numberOfLines={2}
            >
              {stage.replace(/_/g, ' ')}
            </Text>
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { paddingVertical: 8 },
  stageItem: { alignItems: 'center', width: 80 },
  lineContainer: { flexDirection: 'row', alignItems: 'center', height: 24 },
  line: { height: 2, width: 20 },
  lineActive: { backgroundColor: COLORS.primary },
  lineInactive: { backgroundColor: '#E0E0E0' },
  dot: {
    width: 20, height: 20, borderRadius: 10,
    justifyContent: 'center', alignItems: 'center',
  },
  dotCompleted: { backgroundColor: COLORS.primary },
  dotCurrent: { backgroundColor: '#fff', borderWidth: 3, borderColor: COLORS.primary },
  dotPending: { backgroundColor: '#E0E0E0' },
  currentInner: { width: 8, height: 8, borderRadius: 4, backgroundColor: COLORS.primary },
  checkmark: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  label: { fontSize: 10, color: '#999', textAlign: 'center', marginTop: 4, textTransform: 'capitalize' },
  labelCurrent: { color: COLORS.primary, fontWeight: '600' },
  labelCompleted: { color: '#666' },
});
