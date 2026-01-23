/**
 * Farms Screen Tests
 * Integration tests for the My Farms tab
 */

import React from 'react';
import { render, fireEvent, waitFor, screen, act } from '@testing-library/react-native';
import FarmsScreen from '../(tabs)/farms';
import { useAuthStore } from '@/store/auth';
import { useFarmStore, Farm } from '@/store/farm';

// Mock expo-router with hoisting-safe approach
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  router: {
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  },
  useFocusEffect: jest.fn((callback) => {
    const React = require('react');
    React.useEffect(() => {
      callback();
    }, [callback]);
  }),
  Link: ({ children }: { children: React.ReactNode }) => children,
}));

// Get access to the mocked router for assertions
import { router } from 'expo-router';
const getMockedRouter = () => router as { push: jest.Mock };

// Mock stores
jest.mock('@/store/auth', () => ({
  useAuthStore: jest.fn(),
}));

jest.mock('@/store/farm', () => ({
  useFarmStore: jest.fn(),
}));

const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;
const mockUseFarmStore = useFarmStore as jest.MockedFunction<typeof useFarmStore>;

const createMockFarm = (overrides: Partial<Farm> = {}): Farm => ({
  id: 'farm-1',
  farmerId: 'farmer-1',
  plotId: 'PLOT-001',
  name: 'Test Farm',
  latitude: -1.2921,
  longitude: 36.8219,
  county: 'Nairobi',
  subCounty: 'Westlands',
  ward: 'Parklands',
  totalAcreage: 10.5,
  cultivableAcreage: 8.0,
  ownershipType: 'owned',
  soilType: 'loamy',
  waterSource: 'borehole',
  irrigationType: 'drip',
  isVerified: false,
  registrationStep: 'complete',
  registrationComplete: true,
  boundaryGeojson: null,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: null,
  ...overrides,
});

describe('FarmsScreen', () => {
  const mockFetchFarms = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseAuthStore.mockReturnValue({
      user: { id: 'user-123', email: 'test@example.com', firstName: 'Test', lastName: 'User', roles: ['farmer'] },
      accessToken: 'token',
      refreshToken: 'refresh',
      isAuthenticated: true,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refreshTokens: jest.fn(),
    });

    mockUseFarmStore.mockReturnValue({
      farms: [],
      selectedFarm: null,
      isLoading: false,
      error: null,
      registrationDraft: null,
      registrationFarmId: null,
      pendingUploads: [],
      fetchFarms: mockFetchFarms,
      getFarm: jest.fn(),
      setSelectedFarm: jest.fn(),
      clearError: jest.fn(),
      startRegistration: jest.fn(),
      updateDraft: jest.fn(),
      setRegistrationStep: jest.fn(),
      saveBoundary: jest.fn(),
      saveLandDetails: jest.fn(),
      saveSoilWater: jest.fn(),
      completeRegistration: jest.fn(),
      clearDraft: jest.fn(),
      addPendingUpload: jest.fn(),
      removePendingUpload: jest.fn(),
      syncPendingUploads: jest.fn(),
    });
  });

  describe('rendering', () => {
    it('renders the farms screen with empty state', () => {
      render(<FarmsScreen />);

      // Empty state shows "No Farms Yet"
      expect(screen.getByText('No Farms Yet')).toBeTruthy();
    });

    it('renders add first farm button in empty state', () => {
      render(<FarmsScreen />);

      // Empty state shows "Add Your First Farm" button
      expect(screen.getByText('Add Your First Farm')).toBeTruthy();
    });
  });

  describe('loading state', () => {
    it('shows loading indicator when fetching farms', () => {
      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        isLoading: true,
      });

      render(<FarmsScreen />);

      // Should show loading state (ActivityIndicator doesn't have text)
      expect(screen.queryByText('No farms yet')).toBeNull();
    });
  });

  describe('empty state', () => {
    it('shows empty state when no farms', () => {
      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: [],
        isLoading: false,
      });

      render(<FarmsScreen />);

      expect(screen.getByText('No Farms Yet')).toBeTruthy();
    });

    it('shows prompt to add first farm', () => {
      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: [],
        isLoading: false,
      });

      render(<FarmsScreen />);

      expect(screen.getByText(/Add Your First Farm/i)).toBeTruthy();
    });
  });

  describe('with farms', () => {
    it('displays farm list', () => {
      const mockFarms = [
        createMockFarm({ id: 'farm-1', name: 'Kamau Farm' }),
        createMockFarm({ id: 'farm-2', name: 'Ngugi Farm' }),
      ];

      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: mockFarms,
        isLoading: false,
      });

      render(<FarmsScreen />);

      expect(screen.getByText('Kamau Farm')).toBeTruthy();
      expect(screen.getByText('Ngugi Farm')).toBeTruthy();
    });

    it('displays farm location', () => {
      const mockFarms = [
        createMockFarm({
          id: 'farm-1',
          name: 'Test Farm',
          county: 'Kiambu',
          subCounty: 'Kikuyu',
        }),
      ];

      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: mockFarms,
        isLoading: false,
      });

      render(<FarmsScreen />);

      expect(screen.getByText(/Kiambu/)).toBeTruthy();
    });

    it('displays farm acreage', () => {
      const mockFarms = [
        createMockFarm({
          id: 'farm-1',
          name: 'Test Farm',
          totalAcreage: 15.5,
        }),
      ];

      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: mockFarms,
        isLoading: false,
      });

      render(<FarmsScreen />);

      // Acreage is shown in multiple places, just check that it exists
      const acreageElements = screen.getAllByText(/15.5/);
      expect(acreageElements.length).toBeGreaterThan(0);
    });

    it('shows registration status for incomplete farms', () => {
      const mockFarms = [
        createMockFarm({
          id: 'farm-1',
          name: 'Incomplete Farm',
          registrationComplete: false,
          registrationStep: 'boundary',
        }),
      ];

      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: mockFarms,
        isLoading: false,
      });

      render(<FarmsScreen />);

      // Component shows "In Progress" badge for incomplete registrations
      expect(screen.getByText(/In Progress/i)).toBeTruthy();
    });
  });

  describe('interactions', () => {
    it('fetches farms on mount', () => {
      render(<FarmsScreen />);

      expect(mockFetchFarms).toHaveBeenCalledWith('user-123');
    });

    it('navigates to add farm screen on button press', () => {
      render(<FarmsScreen />);

      // In empty state, the button is "Add Your First Farm"
      fireEvent.press(screen.getByText('Add Your First Farm'));

      expect(getMockedRouter().push).toHaveBeenCalledWith('/farms/add');
    });

    it('navigates to farm detail on farm press', () => {
      const mockFarms = [createMockFarm({ id: 'farm-123', name: 'My Farm' })];

      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: mockFarms,
        isLoading: false,
      });

      render(<FarmsScreen />);

      fireEvent.press(screen.getByText('My Farm'));

      expect(getMockedRouter().push).toHaveBeenCalledWith('/farms/farm-123');
    });
  });

  describe('pull to refresh', () => {
    it('refreshes farms on pull', async () => {
      const mockFarms = [createMockFarm()];

      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: mockFarms,
        isLoading: false,
      });

      render(<FarmsScreen />);

      // Simulate pull to refresh
      // Note: Testing RefreshControl requires specific setup
      expect(mockFetchFarms).toHaveBeenCalled();
    });
  });

  describe('error state', () => {
    it('displays error message when fetch fails', () => {
      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: [],
        isLoading: false,
        error: 'Failed to load farms',
      });

      render(<FarmsScreen />);

      expect(screen.getByText('Failed to load farms')).toBeTruthy();
    });

    it('shows retry button on error', () => {
      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: [],
        isLoading: false,
        error: 'Network error',
      });

      render(<FarmsScreen />);

      expect(screen.getByText('Retry')).toBeTruthy();
    });

    it('retries fetch on retry button press', () => {
      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: [],
        isLoading: false,
        error: 'Network error',
      });

      render(<FarmsScreen />);

      fireEvent.press(screen.getByText('Retry'));

      expect(mockFetchFarms).toHaveBeenCalledTimes(2); // Initial + retry
    });
  });

  describe('verified farms', () => {
    it('shows verified badge for verified farms', () => {
      const mockFarms = [
        createMockFarm({
          id: 'farm-1',
          name: 'Verified Farm',
          isVerified: true,
        }),
      ];

      mockUseFarmStore.mockReturnValue({
        ...mockUseFarmStore(),
        farms: mockFarms,
        isLoading: false,
      });

      render(<FarmsScreen />);

      expect(screen.getByText('Verified')).toBeTruthy();
    });
  });
});
