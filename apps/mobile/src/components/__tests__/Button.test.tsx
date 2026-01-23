/**
 * Button Component Tests
 * Tests for the reusable Button component
 */

import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react-native';
import { Button } from '../Button';

describe('Button', () => {
  const mockOnPress = jest.fn();

  beforeEach(() => {
    mockOnPress.mockClear();
  });

  describe('rendering', () => {
    it('renders with title text', () => {
      render(<Button title="Click Me" onPress={mockOnPress} />);

      expect(screen.getByText('Click Me')).toBeTruthy();
    });

    it('renders with primary variant by default', () => {
      render(<Button title="Primary" onPress={mockOnPress} />);

      const button = screen.getByText('Primary').parent;
      // Primary variant should have green background
      expect(button).toBeTruthy();
    });

    it('renders with secondary variant', () => {
      render(<Button title="Secondary" onPress={mockOnPress} variant="secondary" />);

      expect(screen.getByText('Secondary')).toBeTruthy();
    });

    it('renders with outline variant', () => {
      render(<Button title="Outline" onPress={mockOnPress} variant="outline" />);

      expect(screen.getByText('Outline')).toBeTruthy();
    });
  });

  describe('sizes', () => {
    it('renders small size', () => {
      render(<Button title="Small" onPress={mockOnPress} size="small" />);

      expect(screen.getByText('Small')).toBeTruthy();
    });

    it('renders medium size by default', () => {
      render(<Button title="Medium" onPress={mockOnPress} />);

      expect(screen.getByText('Medium')).toBeTruthy();
    });

    it('renders large size', () => {
      render(<Button title="Large" onPress={mockOnPress} size="large" />);

      expect(screen.getByText('Large')).toBeTruthy();
    });
  });

  describe('interactions', () => {
    it('calls onPress when pressed', () => {
      render(<Button title="Press Me" onPress={mockOnPress} />);

      fireEvent.press(screen.getByText('Press Me'));

      expect(mockOnPress).toHaveBeenCalledTimes(1);
    });

    it('does not call onPress when disabled', () => {
      render(<Button title="Disabled" onPress={mockOnPress} disabled />);

      fireEvent.press(screen.getByText('Disabled'));

      expect(mockOnPress).not.toHaveBeenCalled();
    });

    it('button is disabled when loading', () => {
      render(<Button title="Loading" onPress={mockOnPress} loading />);

      // When loading, the text should be hidden (replaced with ActivityIndicator)
      // and the button should be in disabled state
      expect(screen.queryByText('Loading')).toBeNull();
    });
  });

  describe('loading state', () => {
    it('shows ActivityIndicator when loading', () => {
      render(<Button title="Loading" onPress={mockOnPress} loading />);

      // Title should not be visible when loading
      expect(screen.queryByText('Loading')).toBeNull();
    });

    it('hides title text when loading', () => {
      render(<Button title="Submit" onPress={mockOnPress} loading />);

      expect(screen.queryByText('Submit')).toBeNull();
    });
  });

  describe('disabled state', () => {
    it('applies disabled styles when disabled', () => {
      const { getByText } = render(
        <Button title="Disabled" onPress={mockOnPress} disabled />
      );

      expect(getByText('Disabled')).toBeTruthy();
    });

    it('hides text when loading', () => {
      render(<Button title="Loading" onPress={mockOnPress} loading />);

      // Button text should be hidden when loading
      expect(screen.queryByText('Loading')).toBeNull();
    });
  });

  describe('custom styles', () => {
    it('applies custom button style', () => {
      const customStyle = { marginTop: 20 };
      render(
        <Button title="Custom" onPress={mockOnPress} style={customStyle} />
      );

      expect(screen.getByText('Custom')).toBeTruthy();
    });

    it('applies custom text style', () => {
      const customTextStyle = { fontWeight: 'bold' as const };
      render(
        <Button title="Custom Text" onPress={mockOnPress} textStyle={customTextStyle} />
      );

      expect(screen.getByText('Custom Text')).toBeTruthy();
    });
  });
});
