/**
 * Auth Store Tests
 * Tests for authentication state management
 */

import { act, renderHook } from '@testing-library/react-native';
import { useAuthStore } from '../auth';
import { authApi } from '@/services/api';

// Mock the API
jest.mock('@/services/api', () => ({
  authApi: {
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(() => Promise.resolve()),
    refresh: jest.fn(),
  },
}));

const mockAuthApi = authApi as jest.Mocked<typeof authApi>;

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { result } = renderHook(() => useAuthStore());
    act(() => {
      result.current.logout();
    });

    // Clear all mocks
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('starts with null user', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.user).toBeNull();
    });

    it('starts with null tokens', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.accessToken).toBeNull();
      expect(result.current.refreshToken).toBeNull();
    });

    it('starts as not authenticated', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.isAuthenticated).toBe(false);
    });

    it('starts with isLoading false', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('login', () => {
    const mockLoginResponse = {
      user_id: 'user-123',
      email: 'test@example.com',
      access_token: 'access-token-123',
      refresh_token: 'refresh-token-123',
      roles: ['farmer'],
    };

    it('successfully logs in user', async () => {
      mockAuthApi.login.mockResolvedValueOnce(mockLoginResponse);
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual({
        id: 'user-123',
        email: 'test@example.com',
        firstName: '',
        lastName: '',
        roles: ['farmer'],
      });
    });

    it('stores tokens on successful login', async () => {
      mockAuthApi.login.mockResolvedValueOnce(mockLoginResponse);
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });

      expect(result.current.accessToken).toBe('access-token-123');
      expect(result.current.refreshToken).toBe('refresh-token-123');
    });

    it('sets isLoading during login', async () => {
      mockAuthApi.login.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockLoginResponse), 100))
      );
      const { result } = renderHook(() => useAuthStore());

      let loginPromise: Promise<void>;
      act(() => {
        loginPromise = result.current.login('test@example.com', 'password123');
      });

      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        await loginPromise;
      });

      expect(result.current.isLoading).toBe(false);
    });

    it('throws error on failed login', async () => {
      const loginError = new Error('Invalid credentials');
      mockAuthApi.login.mockRejectedValueOnce(loginError);
      const { result } = renderHook(() => useAuthStore());

      await expect(
        act(async () => {
          await result.current.login('test@example.com', 'wrong-password');
        })
      ).rejects.toThrow('Invalid credentials');

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    it('calls authApi.login with correct parameters', async () => {
      mockAuthApi.login.mockResolvedValueOnce(mockLoginResponse);
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login('user@test.com', 'mypassword');
      });

      expect(mockAuthApi.login).toHaveBeenCalledWith('user@test.com', 'mypassword');
    });
  });

  describe('register', () => {
    const mockRegisterData = {
      firstName: 'John',
      lastName: 'Doe',
      email: 'john@example.com',
      phone: '+254700000000',
      password: 'password123',
    };

    const mockRegisterResponse = {
      user_id: 'new-user-123',
      email: 'john@example.com',
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token',
      roles: ['farmer'],
    };

    it('successfully registers new user', async () => {
      mockAuthApi.register.mockResolvedValueOnce(mockRegisterResponse);
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.register(mockRegisterData);
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual({
        id: 'new-user-123',
        email: 'john@example.com',
        firstName: 'John',
        lastName: 'Doe',
        roles: ['farmer'],
      });
    });

    it('stores name from registration data', async () => {
      mockAuthApi.register.mockResolvedValueOnce(mockRegisterResponse);
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.register(mockRegisterData);
      });

      expect(result.current.user?.firstName).toBe('John');
      expect(result.current.user?.lastName).toBe('Doe');
    });

    it('stores tokens on successful registration', async () => {
      mockAuthApi.register.mockResolvedValueOnce(mockRegisterResponse);
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.register(mockRegisterData);
      });

      expect(result.current.accessToken).toBe('new-access-token');
      expect(result.current.refreshToken).toBe('new-refresh-token');
    });

    it('throws error on failed registration', async () => {
      mockAuthApi.register.mockRejectedValueOnce(new Error('Email already exists'));
      const { result } = renderHook(() => useAuthStore());

      await expect(
        act(async () => {
          await result.current.register(mockRegisterData);
        })
      ).rejects.toThrow('Email already exists');

      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('logout', () => {
    it('clears user data on logout', async () => {
      // First login
      mockAuthApi.login.mockResolvedValueOnce({
        user_id: 'user-123',
        email: 'test@example.com',
        access_token: 'token',
        refresh_token: 'refresh',
        roles: ['farmer'],
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login('test@example.com', 'password');
      });

      expect(result.current.isAuthenticated).toBe(true);

      // Then logout
      act(() => {
        result.current.logout();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.accessToken).toBeNull();
      expect(result.current.refreshToken).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('calls authApi.logout with refresh token', async () => {
      mockAuthApi.login.mockResolvedValueOnce({
        user_id: 'user-123',
        email: 'test@example.com',
        access_token: 'token',
        refresh_token: 'my-refresh-token',
        roles: ['farmer'],
      });
      mockAuthApi.logout.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login('test@example.com', 'password');
      });

      act(() => {
        result.current.logout();
      });

      expect(mockAuthApi.logout).toHaveBeenCalledWith('my-refresh-token');
    });
  });

  describe('refreshTokens', () => {
    it('updates tokens on successful refresh', async () => {
      // Setup initial authenticated state
      mockAuthApi.login.mockResolvedValueOnce({
        user_id: 'user-123',
        email: 'test@example.com',
        access_token: 'old-access',
        refresh_token: 'old-refresh',
        roles: ['farmer'],
      });

      mockAuthApi.refresh.mockResolvedValueOnce({
        access_token: 'new-access',
        refresh_token: 'new-refresh',
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login('test@example.com', 'password');
      });

      await act(async () => {
        await result.current.refreshTokens();
      });

      expect(result.current.accessToken).toBe('new-access');
      expect(result.current.refreshToken).toBe('new-refresh');
    });

    it('logs out on refresh failure', async () => {
      mockAuthApi.login.mockResolvedValueOnce({
        user_id: 'user-123',
        email: 'test@example.com',
        access_token: 'access',
        refresh_token: 'refresh',
        roles: ['farmer'],
      });

      mockAuthApi.refresh.mockRejectedValueOnce(new Error('Token expired'));

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login('test@example.com', 'password');
      });

      await act(async () => {
        await result.current.refreshTokens();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('does nothing if no refresh token exists', async () => {
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.refreshTokens();
      });

      expect(mockAuthApi.refresh).not.toHaveBeenCalled();
    });
  });
});
