import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { farmRegistrationApi, farmApi } from '@/services/api';

// Types
export type Farm = {
  id: string;
  farmerId: string;
  plotId: string | null;
  name: string;
  latitude: number | null;
  longitude: number | null;
  county: string | null;
  subCounty: string | null;
  ward: string | null;
  totalAcreage: number | null;
  cultivableAcreage: number | null;
  ownershipType: string | null;
  soilType: string | null;
  waterSource: string | null;
  irrigationType: string | null;
  isVerified: boolean;
  registrationStep: string;
  registrationComplete: boolean;
  boundaryGeojson: GeoJSONPolygon | null;
  createdAt: string;
  updatedAt: string | null;
};

export type GeoJSONPolygon = {
  type: 'Polygon';
  coordinates: number[][][];
};

export type RegistrationDraft = {
  farmerId: string;
  currentStep: RegistrationStep;
  // Step 1: Location
  name: string;
  latitude: number | null;
  longitude: number | null;
  altitude: number | null;
  addressDescription: string | null;
  // Step 2: Boundary
  boundaryGeojson: GeoJSONPolygon | null;
  boundaryAreaAcres: number | null;
  // Step 3: Land Details
  totalAcreage: number | null;
  cultivableAcreage: number | null;
  ownershipType: string | null;
  landReferenceNumber: string | null;
  // Step 4: Soil & Water
  soilType: string | null;
  soilPh: number | null;
  waterSource: string | null;
  irrigationType: string | null;
  // Geocoded location
  county: string | null;
  subCounty: string | null;
  ward: string | null;
};

export type RegistrationStep =
  | 'location'
  | 'boundary'
  | 'land_details'
  | 'documents'
  | 'soil_water'
  | 'assets'
  | 'crop_history'
  | 'review'
  | 'complete';

export type PendingUpload = {
  id: string;
  farmId: string;
  type: 'document' | 'photo' | 'boundary';
  data: any;
  createdAt: string;
  retryCount: number;
};

type FarmState = {
  // Cached farms
  farms: Farm[];
  selectedFarm: Farm | null;
  isLoading: boolean;
  error: string | null;

  // Registration
  registrationDraft: RegistrationDraft | null;
  registrationFarmId: string | null;

  // Offline sync
  pendingUploads: PendingUpload[];

  // Actions - Farm CRUD
  fetchFarms: (farmerId: string) => Promise<void>;
  getFarm: (farmId: string) => Promise<Farm>;
  setSelectedFarm: (farm: Farm | null) => void;
  clearError: () => void;

  // Actions - Registration
  startRegistration: (farmerId: string, name: string, latitude: number, longitude: number) => Promise<string>;
  updateDraft: (updates: Partial<RegistrationDraft>) => void;
  setRegistrationStep: (step: RegistrationStep) => void;
  saveBoundary: (farmId: string, boundary: GeoJSONPolygon) => Promise<void>;
  saveLandDetails: (farmId: string, data: LandDetailsData) => Promise<void>;
  saveSoilWater: (farmId: string, data: SoilWaterData) => Promise<void>;
  completeRegistration: (farmId: string) => Promise<void>;
  clearDraft: () => void;

  // Actions - Offline sync
  addPendingUpload: (upload: Omit<PendingUpload, 'id' | 'createdAt' | 'retryCount'>) => void;
  removePendingUpload: (id: string) => void;
  syncPendingUploads: () => Promise<void>;
};

type LandDetailsData = {
  totalAcreage: number;
  cultivableAcreage?: number;
  ownershipType: string;
  landReferenceNumber?: string;
};

type SoilWaterData = {
  soilType?: string;
  soilPh?: number;
  waterSource?: string;
  irrigationType?: string;
};

const initialDraft: RegistrationDraft = {
  farmerId: '',
  currentStep: 'location',
  name: '',
  latitude: null,
  longitude: null,
  altitude: null,
  addressDescription: null,
  boundaryGeojson: null,
  boundaryAreaAcres: null,
  totalAcreage: null,
  cultivableAcreage: null,
  ownershipType: null,
  landReferenceNumber: null,
  soilType: null,
  soilPh: null,
  waterSource: null,
  irrigationType: null,
  county: null,
  subCounty: null,
  ward: null,
};

// Helper to convert API response to Farm type
const mapApiResponseToFarm = (data: any): Farm => ({
  id: data.id,
  farmerId: data.farmer_id,
  plotId: data.plot_id,
  name: data.name,
  latitude: data.latitude,
  longitude: data.longitude,
  county: data.county,
  subCounty: data.sub_county,
  ward: data.ward,
  totalAcreage: data.total_acreage,
  cultivableAcreage: data.cultivable_acreage,
  ownershipType: data.ownership_type,
  soilType: data.soil_type,
  waterSource: data.water_source,
  irrigationType: data.irrigation_type,
  isVerified: data.is_verified,
  registrationStep: data.registration_step || 'location',
  registrationComplete: data.registration_complete || false,
  boundaryGeojson: data.boundary_geojson,
  createdAt: data.created_at,
  updatedAt: data.updated_at,
});

export const useFarmStore = create<FarmState>()(
  persist(
    (set, get) => ({
      farms: [],
      selectedFarm: null,
      isLoading: false,
      error: null,
      registrationDraft: null,
      registrationFarmId: null,
      pendingUploads: [],

      // Farm CRUD
      fetchFarms: async (farmerId: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await farmApi.list(farmerId);
          const farms = response.map(mapApiResponseToFarm);
          set({ farms, isLoading: false });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to fetch farms',
            isLoading: false,
          });
          throw error;
        }
      },

      getFarm: async (farmId: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await farmApi.get(farmId);
          const farm = mapApiResponseToFarm(response);
          set({ selectedFarm: farm, isLoading: false });
          return farm;
        } catch (error: any) {
          set({
            error: error.message || 'Failed to fetch farm',
            isLoading: false,
          });
          throw error;
        }
      },

      setSelectedFarm: (farm: Farm | null) => {
        set({ selectedFarm: farm });
      },

      clearError: () => {
        set({ error: null });
      },

      // Registration
      startRegistration: async (farmerId: string, name: string, latitude: number, longitude: number) => {
        set({ isLoading: true, error: null });
        try {
          const response = await farmRegistrationApi.start({
            farmer_id: farmerId,
            name,
            latitude,
            longitude,
          });

          const farmId = response.farm_id;

          // Initialize draft
          set({
            registrationDraft: {
              ...initialDraft,
              farmerId,
              name,
              latitude,
              longitude,
              currentStep: 'boundary',
            },
            registrationFarmId: farmId,
            isLoading: false,
          });

          return farmId;
        } catch (error: any) {
          set({
            error: error.message || 'Failed to start registration',
            isLoading: false,
          });
          throw error;
        }
      },

      updateDraft: (updates: Partial<RegistrationDraft>) => {
        const { registrationDraft } = get();
        if (registrationDraft) {
          set({
            registrationDraft: { ...registrationDraft, ...updates },
          });
        }
      },

      setRegistrationStep: (step: RegistrationStep) => {
        const { registrationDraft } = get();
        if (registrationDraft) {
          set({
            registrationDraft: { ...registrationDraft, currentStep: step },
          });
        }
      },

      saveBoundary: async (farmId: string, boundary: GeoJSONPolygon) => {
        set({ isLoading: true, error: null });
        try {
          const response = await farmRegistrationApi.setBoundary(farmId, boundary);

          // Update draft with boundary info
          const { registrationDraft } = get();
          if (registrationDraft) {
            set({
              registrationDraft: {
                ...registrationDraft,
                boundaryGeojson: boundary,
                currentStep: 'land_details',
              },
              isLoading: false,
            });
          }
        } catch (error: any) {
          // Queue for offline sync if network error
          if (!error.response) {
            get().addPendingUpload({
              farmId,
              type: 'boundary',
              data: boundary,
            });
          }
          set({
            error: error.message || 'Failed to save boundary',
            isLoading: false,
          });
          throw error;
        }
      },

      saveLandDetails: async (farmId: string, data: LandDetailsData) => {
        set({ isLoading: true, error: null });
        try {
          await farmRegistrationApi.updateLandDetails(farmId, {
            total_acreage: data.totalAcreage,
            cultivable_acreage: data.cultivableAcreage,
            ownership_type: data.ownershipType,
            land_reference_number: data.landReferenceNumber,
          });

          const { registrationDraft } = get();
          if (registrationDraft) {
            set({
              registrationDraft: {
                ...registrationDraft,
                totalAcreage: data.totalAcreage,
                cultivableAcreage: data.cultivableAcreage || null,
                ownershipType: data.ownershipType,
                landReferenceNumber: data.landReferenceNumber || null,
                currentStep: 'documents',
              },
              isLoading: false,
            });
          }
        } catch (error: any) {
          set({
            error: error.message || 'Failed to save land details',
            isLoading: false,
          });
          throw error;
        }
      },

      saveSoilWater: async (farmId: string, data: SoilWaterData) => {
        set({ isLoading: true, error: null });
        try {
          await farmRegistrationApi.updateSoilWater(farmId, {
            soil_type: data.soilType,
            soil_ph: data.soilPh,
            water_source: data.waterSource,
            irrigation_type: data.irrigationType,
          });

          const { registrationDraft } = get();
          if (registrationDraft) {
            set({
              registrationDraft: {
                ...registrationDraft,
                soilType: data.soilType || null,
                soilPh: data.soilPh || null,
                waterSource: data.waterSource || null,
                irrigationType: data.irrigationType || null,
                currentStep: 'assets',
              },
              isLoading: false,
            });
          }
        } catch (error: any) {
          set({
            error: error.message || 'Failed to save soil/water info',
            isLoading: false,
          });
          throw error;
        }
      },

      completeRegistration: async (farmId: string) => {
        set({ isLoading: true, error: null });
        try {
          await farmRegistrationApi.complete(farmId);

          // Clear draft and refresh farms
          const { registrationDraft } = get();
          if (registrationDraft) {
            await get().fetchFarms(registrationDraft.farmerId);
          }

          set({
            registrationDraft: null,
            registrationFarmId: null,
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to complete registration',
            isLoading: false,
          });
          throw error;
        }
      },

      clearDraft: () => {
        set({
          registrationDraft: null,
          registrationFarmId: null,
        });
      },

      // Offline sync
      addPendingUpload: (upload) => {
        const newUpload: PendingUpload = {
          ...upload,
          id: Date.now().toString(),
          createdAt: new Date().toISOString(),
          retryCount: 0,
        };
        set((state) => ({
          pendingUploads: [...state.pendingUploads, newUpload],
        }));
      },

      removePendingUpload: (id: string) => {
        set((state) => ({
          pendingUploads: state.pendingUploads.filter((u) => u.id !== id),
        }));
      },

      syncPendingUploads: async () => {
        const { pendingUploads } = get();
        if (pendingUploads.length === 0) return;

        for (const upload of pendingUploads) {
          try {
            if (upload.type === 'boundary') {
              await farmRegistrationApi.setBoundary(upload.farmId, upload.data);
            }
            // Add other upload types as needed

            get().removePendingUpload(upload.id);
          } catch (error) {
            // Increment retry count
            set((state) => ({
              pendingUploads: state.pendingUploads.map((u) =>
                u.id === upload.id ? { ...u, retryCount: u.retryCount + 1 } : u
              ),
            }));
          }
        }
      },
    }),
    {
      name: 'farm-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        farms: state.farms,
        registrationDraft: state.registrationDraft,
        registrationFarmId: state.registrationFarmId,
        pendingUploads: state.pendingUploads,
      }),
    }
  )
);
