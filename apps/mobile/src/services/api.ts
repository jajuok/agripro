import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { useAuthStore } from '@/store/auth';

// Get the development server host dynamically
// This extracts the IP from Expo's manifest (e.g., "192.168.1.64:8084" -> "192.168.1.64")
const getDevServerHost = (): string => {
  // In development, get the host from Expo's manifest
  const debuggerHost = Constants.expoConfig?.hostUri ?? Constants.manifest2?.extra?.expoGo?.debuggerHost;

  if (debuggerHost) {
    // Extract just the IP/hostname (remove port)
    return debuggerHost.split(':')[0];
  }

  // Fallback for Android emulator (special IP that routes to host machine)
  if (Platform.OS === 'android') {
    return '10.0.2.2';
  }

  // Fallback for iOS simulator and web
  return 'localhost';
};

// Build API URLs dynamically based on environment
const buildApiUrl = (port: number): string => {
  // Use environment variables if set (for production)
  if (process.env.EXPO_PUBLIC_API_HOST) {
    return `http://${process.env.EXPO_PUBLIC_API_HOST}:${port}/api/v1`;
  }

  // In development, detect host automatically
  const host = getDevServerHost();
  return `http://${host}:${port}/api/v1`;
};

const AUTH_API_URL = process.env.EXPO_PUBLIC_AUTH_API_URL || buildApiUrl(9001);
const FARMER_API_URL = process.env.EXPO_PUBLIC_FARMER_API_URL || buildApiUrl(9002);

// Debug logging for API URLs
console.log('API Configuration:', {
  AUTH_API_URL,
  FARMER_API_URL,
  debuggerHost: Constants.expoConfig?.hostUri ?? Constants.manifest2?.extra?.expoGo?.debuggerHost,
  platform: Platform.OS,
});

// Auth service client
export const apiClient = axios.create({
  baseURL: AUTH_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Farmer service client
export const farmerClient = axios.create({
  baseURL: FARMER_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && originalRequest) {
      try {
        await useAuthStore.getState().refreshTokens();
        const token = useAuthStore.getState().accessToken;
        if (token && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return apiClient(originalRequest);
      } catch {
        useAuthStore.getState().logout();
      }
    }

    return Promise.reject(error);
  }
);

// Farmer client interceptors
farmerClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

farmerClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && originalRequest) {
      try {
        await useAuthStore.getState().refreshTokens();
        const token = useAuthStore.getState().accessToken;
        if (token && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return farmerClient(originalRequest);
      } catch {
        useAuthStore.getState().logout();
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (data: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    password: string;
  }) => {
    const payload = {
      email: data.email,
      password: data.password,
      first_name: data.firstName,
      last_name: data.lastName,
      phone_number: data.phone,
    };
    console.log('Attempting registration with:', { ...payload, password: '***' });
    console.log('API URL:', apiClient.defaults.baseURL);
    try {
      const response = await apiClient.post('/auth/register', payload);
      console.log('Registration successful:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Registration API error:', error.message);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw error;
    }
  },

  refresh: async (refreshToken: string) => {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  logout: async (refreshToken: string) => {
    await apiClient.post('/auth/logout', { refresh_token: refreshToken });
  },
};

// Farmer API
export const farmerApi = {
  getProfile: async (farmerId: string) => {
    const response = await farmerClient.get(`/farmers/${farmerId}`);
    return response.data;
  },

  updateProfile: async (farmerId: string, data: any) => {
    const response = await farmerClient.patch(`/farmers/${farmerId}`, data);
    return response.data;
  },

  getKycStatus: async (farmerId: string) => {
    const response = await farmerClient.get(`/kyc/${farmerId}/status`);
    return response.data;
  },
};

// Farm API
export const farmApi = {
  list: async (farmerId: string) => {
    const response = await farmerClient.get(`/farms/farmer/${farmerId}`);
    return response.data;
  },

  get: async (farmId: string) => {
    const response = await farmerClient.get(`/farms/${farmId}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await farmerClient.post('/farms', data);
    return response.data;
  },

  update: async (farmId: string, data: any) => {
    const response = await farmerClient.patch(`/farms/${farmId}`, data);
    return response.data;
  },
};

// Document API
export const documentApi = {
  upload: async (farmerId: string, documentType: string, file: any) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const response = await farmerClient.post(
      `/documents/upload/${farmerId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  list: async (farmerId: string) => {
    const response = await farmerClient.get(`/documents/farmer/${farmerId}`);
    return response.data;
  },
};

// Farm Registration API (uses farmer service)
export const farmRegistrationApi = {
  start: async (data: {
    farmer_id: string;
    name: string;
    latitude: number;
    longitude: number;
  }) => {
    const response = await farmerClient.post('/farm-registration/start', data);
    return response.data;
  },

  getStatus: async (farmId: string) => {
    const response = await farmerClient.get(`/farm-registration/${farmId}/status`);
    return response.data;
  },

  updateLocation: async (
    farmId: string,
    latitude: number,
    longitude: number,
    altitude?: number
  ) => {
    const params = new URLSearchParams();
    params.append('latitude', latitude.toString());
    params.append('longitude', longitude.toString());
    if (altitude) params.append('altitude', altitude.toString());

    const response = await farmerClient.patch(
      `/farm-registration/${farmId}/location?${params.toString()}`
    );
    return response.data;
  },

  setBoundary: async (farmId: string, boundaryGeojson: any) => {
    const response = await farmerClient.patch(`/farm-registration/${farmId}/boundary`, {
      boundary_geojson: boundaryGeojson,
    });
    return response.data;
  },

  updateLandDetails: async (
    farmId: string,
    data: {
      total_acreage: number;
      cultivable_acreage?: number;
      ownership_type: string;
      land_reference_number?: string;
    }
  ) => {
    const response = await farmerClient.patch(
      `/farm-registration/${farmId}/land-details`,
      data
    );
    return response.data;
  },

  updateSoilWater: async (
    farmId: string,
    data: {
      soil_type?: string;
      soil_ph?: number;
      water_source?: string;
      irrigation_type?: string;
    }
  ) => {
    const response = await farmerClient.patch(
      `/farm-registration/${farmId}/soil-water`,
      data
    );
    return response.data;
  },

  completeStep: async (farmId: string, step: string) => {
    const response = await farmerClient.post(
      `/farm-registration/${farmId}/complete-step?step=${step}`
    );
    return response.data;
  },

  complete: async (farmId: string) => {
    const response = await farmerClient.post(`/farm-registration/${farmId}/complete`);
    return response.data;
  },

  // Documents
  addDocument: async (
    farmId: string,
    data: {
      document_type: string;
      document_number?: string;
      file_url: string;
      file_name: string;
      file_size?: number;
      mime_type?: string;
      gps_latitude?: number;
      gps_longitude?: number;
    }
  ) => {
    const response = await farmerClient.post(
      `/farm-registration/${farmId}/documents`,
      data
    );
    return response.data;
  },

  listDocuments: async (farmId: string) => {
    const response = await farmerClient.get(`/farm-registration/${farmId}/documents`);
    return response.data;
  },

  // Assets
  addAsset: async (
    farmId: string,
    data: {
      asset_type: string;
      name: string;
      description?: string;
      quantity?: number;
      estimated_value?: number;
      condition?: string;
    }
  ) => {
    const response = await farmerClient.post(`/farm-registration/${farmId}/assets`, data);
    return response.data;
  },

  listAssets: async (farmId: string) => {
    const response = await farmerClient.get(`/farm-registration/${farmId}/assets`);
    return response.data;
  },

  // Crop Records
  addCropRecord: async (
    farmId: string,
    data: {
      crop_name: string;
      variety?: string;
      season: string;
      year: number;
      planted_acreage: number;
      expected_yield_kg?: number;
      actual_yield_kg?: number;
      is_current?: boolean;
    }
  ) => {
    const response = await farmerClient.post(`/farm-registration/${farmId}/crops`, data);
    return response.data;
  },

  listCropRecords: async (farmId: string) => {
    const response = await farmerClient.get(`/farm-registration/${farmId}/crops`);
    return response.data;
  },

  // Soil Tests
  addSoilTest: async (
    farmId: string,
    data: {
      test_date: string;
      tested_by?: string;
      lab_name?: string;
      ph_level?: number;
      nitrogen_ppm?: number;
      phosphorus_ppm?: number;
      potassium_ppm?: number;
      organic_matter_percent?: number;
      texture?: string;
      recommendations?: string;
    }
  ) => {
    const response = await farmerClient.post(`/farm-registration/${farmId}/soil-tests`, data);
    return response.data;
  },

  listSoilTests: async (farmId: string) => {
    const response = await farmerClient.get(`/farm-registration/${farmId}/soil-tests`);
    return response.data;
  },
};

// GIS API (connects to GIS service)
const GIS_API_URL = process.env.EXPO_PUBLIC_GIS_API_URL || buildApiUrl(9003);

const gisClient = axios.create({
  baseURL: GIS_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const gisApi = {
  reverseGeocode: async (latitude: number, longitude: number) => {
    const response = await gisClient.post('/gis/reverse-geocode', {
      latitude,
      longitude,
    });
    return response.data;
  },

  validateCoordinates: async (latitude: number, longitude: number) => {
    const response = await gisClient.post('/gis/validate-coordinates', {
      latitude,
      longitude,
    });
    return response.data;
  },

  validatePolygon: async (geojson: any) => {
    const response = await gisClient.post('/gis/validate-polygon', {
      geojson,
    });
    return response.data;
  },

  calculateArea: async (geojson: any) => {
    const response = await gisClient.post('/gis/calculate-area', {
      geojson,
    });
    return response.data;
  },

  checkPointInBoundary: async (
    latitude: number,
    longitude: number,
    boundary: any
  ) => {
    const response = await gisClient.post('/gis/point-in-boundary', {
      latitude,
      longitude,
      boundary,
    });
    return response.data;
  },

  checkOverlap: async (boundary1: any, boundary2: any) => {
    const response = await gisClient.post('/gis/check-overlap', {
      boundary1,
      boundary2,
    });
    return response.data;
  },

  simplifyPolygon: async (geojson: any, tolerance: number = 0.0001) => {
    const response = await gisClient.post('/gis/simplify-polygon', {
      geojson,
      tolerance,
    });
    return response.data;
  },
};
