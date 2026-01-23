/**
 * Farm Store Tests
 * Tests for farm state management and registration workflow
 */

import { act, renderHook } from '@testing-library/react-native';
import { useFarmStore, Farm, GeoJSONPolygon } from '../farm';
import { farmApi, farmRegistrationApi } from '@/services/api';

// Mock the APIs
jest.mock('@/services/api', () => ({
  farmApi: {
    list: jest.fn(),
    get: jest.fn(),
  },
  farmRegistrationApi: {
    start: jest.fn(),
    setBoundary: jest.fn(),
    updateLandDetails: jest.fn(),
    updateSoilWater: jest.fn(),
    complete: jest.fn(),
  },
}));

const mockFarmApi = farmApi as jest.Mocked<typeof farmApi>;
const mockFarmRegistrationApi = farmRegistrationApi as jest.Mocked<typeof farmRegistrationApi>;

const mockFarmResponse = {
  id: 'farm-123',
  farmer_id: 'farmer-456',
  plot_id: 'PLOT-001',
  name: 'Test Farm',
  latitude: -1.2921,
  longitude: 36.8219,
  county: 'Nairobi',
  sub_county: 'Westlands',
  ward: 'Parklands',
  total_acreage: 10.5,
  cultivable_acreage: 8.0,
  ownership_type: 'owned',
  soil_type: 'loamy',
  water_source: 'borehole',
  irrigation_type: 'drip',
  is_verified: false,
  registration_step: 'complete',
  registration_complete: true,
  boundary_geojson: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

describe('useFarmStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { result } = renderHook(() => useFarmStore());
    act(() => {
      result.current.clearDraft();
      result.current.clearError();
    });
    useFarmStore.setState({
      farms: [],
      selectedFarm: null,
      isLoading: false,
      error: null,
      pendingUploads: [],
    });

    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('starts with empty farms array', () => {
      const { result } = renderHook(() => useFarmStore());
      expect(result.current.farms).toEqual([]);
    });

    it('starts with no selected farm', () => {
      const { result } = renderHook(() => useFarmStore());
      expect(result.current.selectedFarm).toBeNull();
    });

    it('starts with no registration draft', () => {
      const { result } = renderHook(() => useFarmStore());
      expect(result.current.registrationDraft).toBeNull();
    });

    it('starts with empty pending uploads', () => {
      const { result } = renderHook(() => useFarmStore());
      expect(result.current.pendingUploads).toEqual([]);
    });
  });

  describe('fetchFarms', () => {
    it('fetches and stores farms', async () => {
      mockFarmApi.list.mockResolvedValueOnce([mockFarmResponse]);
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.fetchFarms('farmer-456');
      });

      expect(result.current.farms).toHaveLength(1);
      expect(result.current.farms[0].id).toBe('farm-123');
      expect(result.current.farms[0].name).toBe('Test Farm');
    });

    it('maps API response to Farm type correctly', async () => {
      mockFarmApi.list.mockResolvedValueOnce([mockFarmResponse]);
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.fetchFarms('farmer-456');
      });

      const farm = result.current.farms[0];
      expect(farm.farmerId).toBe('farmer-456');
      expect(farm.totalAcreage).toBe(10.5);
      expect(farm.ownershipType).toBe('owned');
      expect(farm.registrationComplete).toBe(true);
    });

    it('sets isLoading during fetch', async () => {
      mockFarmApi.list.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve([mockFarmResponse]), 100))
      );
      const { result } = renderHook(() => useFarmStore());

      let fetchPromise: Promise<void>;
      act(() => {
        fetchPromise = result.current.fetchFarms('farmer-456');
      });

      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        await fetchPromise;
      });

      expect(result.current.isLoading).toBe(false);
    });

    it('sets error on fetch failure', async () => {
      mockFarmApi.list.mockRejectedValueOnce(new Error('Network error'));
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        try {
          await result.current.fetchFarms('farmer-456');
        } catch (e) {
          // Expected error
        }
      });

      expect(result.current.error).toBe('Network error');
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('getFarm', () => {
    it('fetches and sets selected farm', async () => {
      mockFarmApi.get.mockResolvedValueOnce(mockFarmResponse);
      const { result } = renderHook(() => useFarmStore());

      let farm: Farm;
      await act(async () => {
        farm = await result.current.getFarm('farm-123');
      });

      expect(result.current.selectedFarm).not.toBeNull();
      expect(result.current.selectedFarm?.id).toBe('farm-123');
    });

    it('returns the fetched farm', async () => {
      mockFarmApi.get.mockResolvedValueOnce(mockFarmResponse);
      const { result } = renderHook(() => useFarmStore());

      let farm: Farm;
      await act(async () => {
        farm = await result.current.getFarm('farm-123');
      });

      expect(farm!.name).toBe('Test Farm');
    });
  });

  describe('setSelectedFarm', () => {
    it('sets selected farm', () => {
      const { result } = renderHook(() => useFarmStore());
      const mockFarm: Farm = {
        id: 'farm-1',
        farmerId: 'farmer-1',
        plotId: null,
        name: 'Selected Farm',
        latitude: -1.3,
        longitude: 36.8,
        county: null,
        subCounty: null,
        ward: null,
        totalAcreage: 5,
        cultivableAcreage: 4,
        ownershipType: 'owned',
        soilType: null,
        waterSource: null,
        irrigationType: null,
        isVerified: false,
        registrationStep: 'location',
        registrationComplete: false,
        boundaryGeojson: null,
        createdAt: '2024-01-01',
        updatedAt: null,
      };

      act(() => {
        result.current.setSelectedFarm(mockFarm);
      });

      expect(result.current.selectedFarm).toEqual(mockFarm);
    });

    it('clears selected farm when set to null', () => {
      const { result } = renderHook(() => useFarmStore());

      act(() => {
        result.current.setSelectedFarm(null);
      });

      expect(result.current.selectedFarm).toBeNull();
    });
  });

  describe('startRegistration', () => {
    it('starts registration and returns farm ID', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({
        farm_id: 'new-farm-123',
        status: 'created',
      });
      const { result } = renderHook(() => useFarmStore());

      let farmId: string;
      await act(async () => {
        farmId = await result.current.startRegistration(
          'farmer-456',
          'New Farm',
          -1.2921,
          36.8219
        );
      });

      expect(farmId!).toBe('new-farm-123');
    });

    it('initializes registration draft', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({
        farm_id: 'new-farm-123',
      });
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'New Farm', -1.2921, 36.8219);
      });

      expect(result.current.registrationDraft).not.toBeNull();
      expect(result.current.registrationDraft?.name).toBe('New Farm');
      expect(result.current.registrationDraft?.latitude).toBe(-1.2921);
      expect(result.current.registrationDraft?.longitude).toBe(36.8219);
      expect(result.current.registrationDraft?.currentStep).toBe('boundary');
    });

    it('stores registration farm ID', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({
        farm_id: 'new-farm-123',
      });
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'New Farm', -1.3, 36.8);
      });

      expect(result.current.registrationFarmId).toBe('new-farm-123');
    });
  });

  describe('updateDraft', () => {
    it('updates draft with partial data', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({ farm_id: 'farm-123' });
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'Farm', -1.3, 36.8);
      });

      act(() => {
        result.current.updateDraft({
          county: 'Nairobi',
          subCounty: 'Westlands',
        });
      });

      expect(result.current.registrationDraft?.county).toBe('Nairobi');
      expect(result.current.registrationDraft?.subCounty).toBe('Westlands');
      // Other fields should remain unchanged
      expect(result.current.registrationDraft?.name).toBe('Farm');
    });

    it('does nothing if no draft exists', () => {
      const { result } = renderHook(() => useFarmStore());

      act(() => {
        result.current.updateDraft({ county: 'Test' });
      });

      expect(result.current.registrationDraft).toBeNull();
    });
  });

  describe('setRegistrationStep', () => {
    it('updates current step', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({ farm_id: 'farm-123' });
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'Farm', -1.3, 36.8);
      });

      act(() => {
        result.current.setRegistrationStep('land_details');
      });

      expect(result.current.registrationDraft?.currentStep).toBe('land_details');
    });
  });

  describe('saveBoundary', () => {
    const mockBoundary: GeoJSONPolygon = {
      type: 'Polygon',
      coordinates: [[[36.8, -1.3], [36.81, -1.3], [36.81, -1.31], [36.8, -1.31], [36.8, -1.3]]],
    };

    it('saves boundary and advances step', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({ farm_id: 'farm-123' });
      mockFarmRegistrationApi.setBoundary.mockResolvedValueOnce({ status: 'updated' });
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'Farm', -1.3, 36.8);
      });

      await act(async () => {
        await result.current.saveBoundary('farm-123', mockBoundary);
      });

      expect(result.current.registrationDraft?.boundaryGeojson).toEqual(mockBoundary);
      expect(result.current.registrationDraft?.currentStep).toBe('land_details');
    });

    it('queues upload on network error', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({ farm_id: 'farm-123' });
      // Network error without response property triggers offline queueing
      const networkError = new Error('Network error');
      mockFarmRegistrationApi.setBoundary.mockRejectedValueOnce(networkError);
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'Farm', -1.3, 36.8);
      });

      await act(async () => {
        try {
          await result.current.saveBoundary('farm-123', mockBoundary);
        } catch (e) {
          // Expected error
        }
      });

      expect(result.current.pendingUploads).toHaveLength(1);
      expect(result.current.pendingUploads[0].type).toBe('boundary');
    });
  });

  describe('saveLandDetails', () => {
    it('saves land details and advances step', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({ farm_id: 'farm-123' });
      mockFarmRegistrationApi.updateLandDetails.mockResolvedValueOnce({ status: 'updated' });
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'Farm', -1.3, 36.8);
      });

      await act(async () => {
        await result.current.saveLandDetails('farm-123', {
          totalAcreage: 10,
          cultivableAcreage: 8,
          ownershipType: 'owned',
        });
      });

      expect(result.current.registrationDraft?.totalAcreage).toBe(10);
      expect(result.current.registrationDraft?.ownershipType).toBe('owned');
      expect(result.current.registrationDraft?.currentStep).toBe('documents');
    });
  });

  describe('saveSoilWater', () => {
    it('saves soil and water info', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({ farm_id: 'farm-123' });
      mockFarmRegistrationApi.updateSoilWater.mockResolvedValueOnce({ status: 'updated' });
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'Farm', -1.3, 36.8);
      });

      await act(async () => {
        await result.current.saveSoilWater('farm-123', {
          soilType: 'loamy',
          waterSource: 'borehole',
        });
      });

      expect(result.current.registrationDraft?.soilType).toBe('loamy');
      expect(result.current.registrationDraft?.waterSource).toBe('borehole');
      expect(result.current.registrationDraft?.currentStep).toBe('assets');
    });
  });

  describe('completeRegistration', () => {
    it('completes registration and clears draft', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({ farm_id: 'farm-123' });
      mockFarmRegistrationApi.complete.mockResolvedValueOnce({ registration_complete: true });
      mockFarmApi.list.mockResolvedValueOnce([mockFarmResponse]);
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'Farm', -1.3, 36.8);
      });

      await act(async () => {
        await result.current.completeRegistration('farm-123');
      });

      expect(result.current.registrationDraft).toBeNull();
      expect(result.current.registrationFarmId).toBeNull();
    });

    it('refreshes farms after completion', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({ farm_id: 'farm-123' });
      mockFarmRegistrationApi.complete.mockResolvedValueOnce({ registration_complete: true });
      mockFarmApi.list.mockResolvedValueOnce([mockFarmResponse]);
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'Farm', -1.3, 36.8);
      });

      await act(async () => {
        await result.current.completeRegistration('farm-123');
      });

      expect(mockFarmApi.list).toHaveBeenCalledWith('farmer-456');
    });
  });

  describe('clearDraft', () => {
    it('clears registration draft and farm ID', async () => {
      mockFarmRegistrationApi.start.mockResolvedValueOnce({ farm_id: 'farm-123' });
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        await result.current.startRegistration('farmer-456', 'Farm', -1.3, 36.8);
      });

      expect(result.current.registrationDraft).not.toBeNull();

      act(() => {
        result.current.clearDraft();
      });

      expect(result.current.registrationDraft).toBeNull();
      expect(result.current.registrationFarmId).toBeNull();
    });
  });

  describe('pending uploads (offline sync)', () => {
    it('adds pending upload', () => {
      const { result } = renderHook(() => useFarmStore());

      act(() => {
        result.current.addPendingUpload({
          farmId: 'farm-123',
          type: 'document',
          data: { name: 'test.pdf' },
        });
      });

      expect(result.current.pendingUploads).toHaveLength(1);
      expect(result.current.pendingUploads[0].type).toBe('document');
      expect(result.current.pendingUploads[0].retryCount).toBe(0);
    });

    it('removes pending upload by ID', () => {
      const { result } = renderHook(() => useFarmStore());

      act(() => {
        result.current.addPendingUpload({
          farmId: 'farm-123',
          type: 'document',
          data: {},
        });
      });

      const uploadId = result.current.pendingUploads[0].id;

      act(() => {
        result.current.removePendingUpload(uploadId);
      });

      expect(result.current.pendingUploads).toHaveLength(0);
    });

    it('syncs pending boundary uploads', async () => {
      mockFarmRegistrationApi.setBoundary.mockResolvedValueOnce({ status: 'updated' });
      const { result } = renderHook(() => useFarmStore());

      const mockBoundary = {
        type: 'Polygon' as const,
        coordinates: [[[36.8, -1.3]]],
      };

      act(() => {
        result.current.addPendingUpload({
          farmId: 'farm-123',
          type: 'boundary',
          data: mockBoundary,
        });
      });

      await act(async () => {
        await result.current.syncPendingUploads();
      });

      expect(mockFarmRegistrationApi.setBoundary).toHaveBeenCalledWith('farm-123', mockBoundary);
      expect(result.current.pendingUploads).toHaveLength(0);
    });

    it('increments retry count on sync failure', async () => {
      mockFarmRegistrationApi.setBoundary.mockRejectedValueOnce(new Error('Network error'));
      const { result } = renderHook(() => useFarmStore());

      act(() => {
        result.current.addPendingUpload({
          farmId: 'farm-123',
          type: 'boundary',
          data: { type: 'Polygon', coordinates: [] },
        });
      });

      await act(async () => {
        await result.current.syncPendingUploads();
      });

      expect(result.current.pendingUploads[0].retryCount).toBe(1);
    });
  });

  describe('clearError', () => {
    it('clears error state', async () => {
      mockFarmApi.list.mockRejectedValueOnce(new Error('Test error'));
      const { result } = renderHook(() => useFarmStore());

      await act(async () => {
        try {
          await result.current.fetchFarms('farmer-456');
        } catch (e) {
          // Expected error
        }
      });

      expect(result.current.error).toBe('Test error');

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });
});
