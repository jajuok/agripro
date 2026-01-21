import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';

type Step = {
  key: string;
  label: string;
  icon?: string;
};

type StepIndicatorProps = {
  steps: Step[];
  currentStep: string;
  completedSteps?: string[];
};

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  steps,
  currentStep,
  completedSteps = [],
}) => {
  const currentIndex = steps.findIndex((s) => s.key === currentStep);

  return (
    <View style={styles.container}>
      {steps.map((step, index) => {
        const isCompleted = completedSteps.includes(step.key);
        const isCurrent = step.key === currentStep;
        const isPast = index < currentIndex;

        return (
          <View key={step.key} style={styles.stepContainer}>
            {/* Connector line (before) */}
            {index > 0 && (
              <View
                style={[
                  styles.connector,
                  styles.connectorLeft,
                  (isCompleted || isCurrent || isPast) && styles.connectorActive,
                ]}
              />
            )}

            {/* Step circle */}
            <View
              style={[
                styles.circle,
                isCompleted && styles.circleCompleted,
                isCurrent && styles.circleCurrent,
                isPast && !isCompleted && styles.circlePast,
              ]}
            >
              {isCompleted ? (
                <Text style={styles.checkmark}>✓</Text>
              ) : (
                <Text
                  style={[
                    styles.stepNumber,
                    (isCurrent || isPast) && styles.stepNumberActive,
                  ]}
                >
                  {index + 1}
                </Text>
              )}
            </View>

            {/* Connector line (after) */}
            {index < steps.length - 1 && (
              <View
                style={[
                  styles.connector,
                  styles.connectorRight,
                  (isCompleted || isPast) && styles.connectorActive,
                ]}
              />
            )}

            {/* Step label */}
            <Text
              style={[
                styles.label,
                (isCurrent || isCompleted) && styles.labelActive,
              ]}
              numberOfLines={1}
            >
              {step.label}
            </Text>
          </View>
        );
      })}
    </View>
  );
};

// Compact version for smaller screens
export const StepIndicatorCompact: React.FC<StepIndicatorProps> = ({
  steps,
  currentStep,
  completedSteps = [],
}) => {
  const currentIndex = steps.findIndex((s) => s.key === currentStep);
  const currentStepData = steps[currentIndex];

  return (
    <View style={styles.compactContainer}>
      <View style={styles.compactProgress}>
        <View
          style={[
            styles.compactProgressBar,
            { width: `${((currentIndex + 1) / steps.length) * 100}%` },
          ]}
        />
      </View>
      <View style={styles.compactInfo}>
        <Text style={styles.compactStep}>
          Step {currentIndex + 1} of {steps.length}
        </Text>
        <Text style={styles.compactLabel}>{currentStepData?.label}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.md,
  },
  stepContainer: {
    flex: 1,
    alignItems: 'center',
    position: 'relative',
  },
  circle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.gray[200],
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: COLORS.gray[300],
    zIndex: 1,
  },
  circleCompleted: {
    backgroundColor: COLORS.success,
    borderColor: COLORS.success,
  },
  circleCurrent: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  circlePast: {
    backgroundColor: COLORS.primaryLight,
    borderColor: COLORS.primaryLight,
  },
  stepNumber: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '600',
    color: COLORS.gray[600],
  },
  stepNumberActive: {
    color: COLORS.white,
  },
  checkmark: {
    fontSize: FONT_SIZES.md,
    fontWeight: 'bold',
    color: COLORS.white,
  },
  connector: {
    position: 'absolute',
    top: 15,
    height: 2,
    backgroundColor: COLORS.gray[300],
    zIndex: 0,
  },
  connectorLeft: {
    left: 0,
    right: '50%',
    marginRight: 16,
  },
  connectorRight: {
    left: '50%',
    right: 0,
    marginLeft: 16,
  },
  connectorActive: {
    backgroundColor: COLORS.primaryLight,
  },
  label: {
    marginTop: SPACING.xs,
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[500],
    textAlign: 'center',
    maxWidth: 60,
  },
  labelActive: {
    color: COLORS.primary,
    fontWeight: '500',
  },
  // Compact styles
  compactContainer: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
  },
  compactProgress: {
    height: 4,
    backgroundColor: COLORS.gray[200],
    borderRadius: 2,
    overflow: 'hidden',
  },
  compactProgressBar: {
    height: '100%',
    backgroundColor: COLORS.primary,
    borderRadius: 2,
  },
  compactInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: SPACING.xs,
  },
  compactStep: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
  },
  compactLabel: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.primary,
    fontWeight: '500',
  },
});

export default StepIndicator;
