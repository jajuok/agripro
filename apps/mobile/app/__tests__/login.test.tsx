/**
 * Login Screen Tests
 * Integration tests for the login screen
 */

import React from 'react';
import { render, fireEvent, waitFor, screen, act } from '@testing-library/react-native';
import LoginScreen from '../(auth)/login';
import { useAuthStore } from '@/store/auth';

// Mock expo-router
const mockReplace = jest.fn();
jest.mock('expo-router', () => ({
  router: {
    replace: (path: string) => mockReplace(path),
  },
  Link: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock the auth store
jest.mock('@/store/auth', () => ({
  useAuthStore: jest.fn(),
}));

const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

describe('LoginScreen', () => {
  const mockLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuthStore.mockReturnValue({
      login: mockLogin,
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      register: jest.fn(),
      logout: jest.fn(),
      refreshTokens: jest.fn(),
    });
  });

  describe('rendering', () => {
    it('renders the login form', () => {
      render(<LoginScreen />);

      expect(screen.getByText('AgriScheme Pro')).toBeTruthy();
      expect(screen.getByText('Farm Management System')).toBeTruthy();
      expect(screen.getByPlaceholderText('Email')).toBeTruthy();
      expect(screen.getByPlaceholderText('Password')).toBeTruthy();
      expect(screen.getByText('Login')).toBeTruthy();
    });

    it('renders forgot password link', () => {
      render(<LoginScreen />);

      expect(screen.getByText('Forgot Password?')).toBeTruthy();
    });

    it('renders register link', () => {
      render(<LoginScreen />);

      expect(screen.getByText("Don't have an account?")).toBeTruthy();
      expect(screen.getByText('Register')).toBeTruthy();
    });
  });

  describe('form validation', () => {
    it('shows error when submitting empty form', async () => {
      render(<LoginScreen />);

      fireEvent.press(screen.getByText('Login'));

      await waitFor(() => {
        expect(screen.getByText('Please enter email and password')).toBeTruthy();
      });
    });

    it('shows error when only email is entered', async () => {
      render(<LoginScreen />);

      fireEvent.changeText(screen.getByPlaceholderText('Email'), 'test@example.com');
      fireEvent.press(screen.getByText('Login'));

      await waitFor(() => {
        expect(screen.getByText('Please enter email and password')).toBeTruthy();
      });
    });

    it('shows error when only password is entered', async () => {
      render(<LoginScreen />);

      fireEvent.changeText(screen.getByPlaceholderText('Password'), 'password123');
      fireEvent.press(screen.getByText('Login'));

      await waitFor(() => {
        expect(screen.getByText('Please enter email and password')).toBeTruthy();
      });
    });
  });

  describe('form input', () => {
    it('updates email input value', () => {
      render(<LoginScreen />);

      const emailInput = screen.getByPlaceholderText('Email');
      fireEvent.changeText(emailInput, 'test@example.com');

      expect(emailInput.props.value).toBe('test@example.com');
    });

    it('updates password input value', () => {
      render(<LoginScreen />);

      const passwordInput = screen.getByPlaceholderText('Password');
      fireEvent.changeText(passwordInput, 'mypassword');

      expect(passwordInput.props.value).toBe('mypassword');
    });

    it('has secure text entry for password', () => {
      render(<LoginScreen />);

      const passwordInput = screen.getByPlaceholderText('Password');
      expect(passwordInput.props.secureTextEntry).toBe(true);
    });

    it('has email keyboard type for email input', () => {
      render(<LoginScreen />);

      const emailInput = screen.getByPlaceholderText('Email');
      expect(emailInput.props.keyboardType).toBe('email-address');
    });
  });

  describe('successful login', () => {
    it('calls login with email and password', async () => {
      mockLogin.mockResolvedValueOnce(undefined);
      render(<LoginScreen />);

      fireEvent.changeText(screen.getByPlaceholderText('Email'), 'test@example.com');
      fireEvent.changeText(screen.getByPlaceholderText('Password'), 'password123');
      fireEvent.press(screen.getByText('Login'));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
      });
    });

    it('navigates to home after successful login', async () => {
      mockLogin.mockResolvedValueOnce(undefined);
      render(<LoginScreen />);

      fireEvent.changeText(screen.getByPlaceholderText('Email'), 'test@example.com');
      fireEvent.changeText(screen.getByPlaceholderText('Password'), 'password123');
      fireEvent.press(screen.getByText('Login'));

      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/(tabs)/home');
      });
    });
  });

  describe('failed login', () => {
    it('shows error message on login failure', async () => {
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));
      render(<LoginScreen />);

      fireEvent.changeText(screen.getByPlaceholderText('Email'), 'test@example.com');
      fireEvent.changeText(screen.getByPlaceholderText('Password'), 'wrongpassword');
      fireEvent.press(screen.getByText('Login'));

      await waitFor(() => {
        expect(screen.getByText('Invalid email or password')).toBeTruthy();
      });
    });

    it('does not navigate on login failure', async () => {
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));
      render(<LoginScreen />);

      fireEvent.changeText(screen.getByPlaceholderText('Email'), 'test@example.com');
      fireEvent.changeText(screen.getByPlaceholderText('Password'), 'wrongpassword');
      fireEvent.press(screen.getByText('Login'));

      await waitFor(() => {
        expect(mockReplace).not.toHaveBeenCalled();
      });
    });
  });

  describe('loading state', () => {
    it('shows loading indicator while logging in', async () => {
      mockLogin.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );
      render(<LoginScreen />);

      fireEvent.changeText(screen.getByPlaceholderText('Email'), 'test@example.com');
      fireEvent.changeText(screen.getByPlaceholderText('Password'), 'password123');
      fireEvent.press(screen.getByText('Login'));

      // Button should be in loading state
      await waitFor(() => {
        expect(screen.queryByText('Login')).toBeNull();
      });
    });

    it('disables button while loading', async () => {
      mockLogin.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );
      render(<LoginScreen />);

      fireEvent.changeText(screen.getByPlaceholderText('Email'), 'test@example.com');
      fireEvent.changeText(screen.getByPlaceholderText('Password'), 'password123');

      const loginButton = screen.getByText('Login').parent;
      fireEvent.press(screen.getByText('Login'));

      // Button text should disappear during loading
      await waitFor(() => {
        expect(screen.queryByText('Login')).toBeNull();
      });
    });
  });
});
