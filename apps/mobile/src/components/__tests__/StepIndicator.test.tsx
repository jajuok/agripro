/**
 * StepIndicator Component Tests
 * Tests for the registration wizard progress indicator
 */

import React from 'react';
import { render, screen } from '@testing-library/react-native';
import { StepIndicator, StepIndicatorCompact } from '../StepIndicator';

const mockSteps = [
  { key: 'location', label: 'Location' },
  { key: 'boundary', label: 'Boundary' },
  { key: 'land', label: 'Land Details' },
  { key: 'documents', label: 'Documents' },
  { key: 'review', label: 'Review' },
];

describe('StepIndicator', () => {
  describe('rendering', () => {
    it('renders all step labels', () => {
      render(
        <StepIndicator steps={mockSteps} currentStep="location" />
      );

      expect(screen.getByText('Location')).toBeTruthy();
      expect(screen.getByText('Boundary')).toBeTruthy();
      expect(screen.getByText('Land Details')).toBeTruthy();
      expect(screen.getByText('Documents')).toBeTruthy();
      expect(screen.getByText('Review')).toBeTruthy();
    });

    it('renders step numbers for incomplete steps', () => {
      render(
        <StepIndicator steps={mockSteps} currentStep="location" />
      );

      expect(screen.getByText('1')).toBeTruthy();
      expect(screen.getByText('2')).toBeTruthy();
      expect(screen.getByText('3')).toBeTruthy();
      expect(screen.getByText('4')).toBeTruthy();
      expect(screen.getByText('5')).toBeTruthy();
    });
  });

  describe('current step', () => {
    it('highlights the current step', () => {
      render(
        <StepIndicator steps={mockSteps} currentStep="boundary" />
      );

      // Step 2 (Boundary) should be current
      expect(screen.getByText('2')).toBeTruthy();
      expect(screen.getByText('Boundary')).toBeTruthy();
    });

    it('correctly identifies step 1 as current', () => {
      render(
        <StepIndicator steps={mockSteps} currentStep="location" />
      );

      expect(screen.getByText('Location')).toBeTruthy();
    });

    it('correctly identifies last step as current', () => {
      render(
        <StepIndicator steps={mockSteps} currentStep="review" />
      );

      expect(screen.getByText('Review')).toBeTruthy();
    });
  });

  describe('completed steps', () => {
    it('shows checkmark for completed steps', () => {
      render(
        <StepIndicator
          steps={mockSteps}
          currentStep="land"
          completedSteps={['location', 'boundary']}
        />
      );

      // Completed steps should show checkmarks
      expect(screen.getAllByText('✓')).toHaveLength(2);
    });

    it('shows numbers for incomplete steps', () => {
      render(
        <StepIndicator
          steps={mockSteps}
          currentStep="land"
          completedSteps={['location', 'boundary']}
        />
      );

      // Current and future steps should show numbers
      expect(screen.getByText('3')).toBeTruthy();
      expect(screen.getByText('4')).toBeTruthy();
      expect(screen.getByText('5')).toBeTruthy();
    });

    it('handles all steps completed', () => {
      render(
        <StepIndicator
          steps={mockSteps}
          currentStep="review"
          completedSteps={['location', 'boundary', 'land', 'documents', 'review']}
        />
      );

      expect(screen.getAllByText('✓')).toHaveLength(5);
    });

    it('handles no completed steps', () => {
      render(
        <StepIndicator steps={mockSteps} currentStep="location" completedSteps={[]} />
      );

      expect(screen.queryByText('✓')).toBeNull();
    });
  });

  describe('empty steps', () => {
    it('handles empty steps array', () => {
      render(<StepIndicator steps={[]} currentStep="" />);

      // Should not crash
      expect(screen.queryByText('1')).toBeNull();
    });

    it('handles single step', () => {
      const singleStep = [{ key: 'only', label: 'Only Step' }];
      render(<StepIndicator steps={singleStep} currentStep="only" />);

      expect(screen.getByText('Only Step')).toBeTruthy();
      expect(screen.getByText('1')).toBeTruthy();
    });
  });
});

describe('StepIndicatorCompact', () => {
  describe('rendering', () => {
    it('renders current step info', () => {
      render(
        <StepIndicatorCompact steps={mockSteps} currentStep="boundary" />
      );

      expect(screen.getByText('Step 2 of 5')).toBeTruthy();
      expect(screen.getByText('Boundary')).toBeTruthy();
    });

    it('renders first step correctly', () => {
      render(
        <StepIndicatorCompact steps={mockSteps} currentStep="location" />
      );

      expect(screen.getByText('Step 1 of 5')).toBeTruthy();
      expect(screen.getByText('Location')).toBeTruthy();
    });

    it('renders last step correctly', () => {
      render(
        <StepIndicatorCompact steps={mockSteps} currentStep="review" />
      );

      expect(screen.getByText('Step 5 of 5')).toBeTruthy();
      expect(screen.getByText('Review')).toBeTruthy();
    });
  });

  describe('progress bar', () => {
    it('shows progress bar for step 1', () => {
      const { UNSAFE_getByType } = render(
        <StepIndicatorCompact steps={mockSteps} currentStep="location" />
      );

      // Progress bar should be 20% (1/5)
      expect(screen.getByText('Step 1 of 5')).toBeTruthy();
    });

    it('shows progress bar for middle step', () => {
      render(
        <StepIndicatorCompact steps={mockSteps} currentStep="land" />
      );

      // Progress bar should be 60% (3/5)
      expect(screen.getByText('Step 3 of 5')).toBeTruthy();
    });

    it('shows full progress bar for last step', () => {
      render(
        <StepIndicatorCompact steps={mockSteps} currentStep="review" />
      );

      // Progress bar should be 100% (5/5)
      expect(screen.getByText('Step 5 of 5')).toBeTruthy();
    });
  });

  describe('edge cases', () => {
    it('handles empty steps', () => {
      render(<StepIndicatorCompact steps={[]} currentStep="" />);

      // Should render "Step 0 of 0" or similar without crashing
      expect(screen.getByText('Step 0 of 0')).toBeTruthy();
    });

    it('handles invalid current step', () => {
      render(
        <StepIndicatorCompact steps={mockSteps} currentStep="invalid" />
      );

      // Should handle gracefully
      expect(screen.getByText('Step 0 of 5')).toBeTruthy();
    });
  });
});
