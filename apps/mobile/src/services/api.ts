import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Lazy getter to avoid require cycle with auth store
const getAuthStore = () => require('@/store/auth').useAuthStore;

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

// Production service URLs (individual FQDNs)
const PRODUCTION_SERVICE_URLS = {
  auth: process.env.EXPO_PUBLIC_AUTH_URL,
  farmer: process.env.EXPO_PUBLIC_FARMER_URL,
  farm: process.env.EXPO_PUBLIC_FARM_URL,
  gis: process.env.EXPO_PUBLIC_GIS_URL,
  financial: process.env.EXPO_PUBLIC_FINANCIAL_URL,
  market: process.env.EXPO_PUBLIC_MARKET_URL,
  ai: process.env.EXPO_PUBLIC_AI_URL,
  iot: process.env.EXPO_PUBLIC_IOT_URL,
  livestock: process.env.EXPO_PUBLIC_LIVESTOCK_URL,
  task: process.env.EXPO_PUBLIC_TASK_URL,
  inventory: process.env.EXPO_PUBLIC_INVENTORY_URL,
  notification: process.env.EXPO_PUBLIC_NOTIFICATION_URL,
  traceability: process.env.EXPO_PUBLIC_TRACEABILITY_URL,
  compliance: process.env.EXPO_PUBLIC_COMPLIANCE_URL,
  integration: process.env.EXPO_PUBLIC_INTEGRATION_URL,
};

// Build unified API Gateway URL (fallback for development)
const buildApiGatewayUrl = (): string => {
  // Use environment variable if set (for unified gateway)
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }

  // In development, use Traefik gateway on port 80
  const host = getDevServerHost();
  return `http://${host}/api/v1`;
};

const API_GATEWAY_URL = buildApiGatewayUrl();

// Check if we're using unified gateway (highest priority)
const isUnifiedGatewayMode = !!process.env.EXPO_PUBLIC_API_URL;

// Check if we're using production individual service URLs (only if no unified gateway)
const isProductionMode = !isUnifiedGatewayMode && !!PRODUCTION_SERVICE_URLS.auth;

// Check if we're in development mode (no production URLs and no unified gateway)
const isDevelopmentMode = !isUnifiedGatewayMode && !isProductionMode;

// Debug logging for API URL
console.log('API Configuration:', {
  mode: isUnifiedGatewayMode ? 'UNIFIED GATEWAY' : isProductionMode ? 'PRODUCTION (individual services)' : 'DEVELOPMENT (direct ports)',
  API_GATEWAY_URL,
  isUnifiedGatewayMode,
  isProductionMode,
  isDevelopmentMode,
  productionServices: isProductionMode ? Object.keys(PRODUCTION_SERVICE_URLS).filter(k => PRODUCTION_SERVICE_URLS[k as keyof typeof PRODUCTION_SERVICE_URLS]).length : 0,
  debuggerHost: Constants.expoConfig?.hostUri ?? Constants.manifest2?.extra?.expoGo?.debuggerHost,
  platform: Platform.OS,
});

// Service port mapping for local development (when gateway isn't available)
const SERVICE_PORTS: Record<string, number> = {
  '/auth': 9000,
  '/farmers': 9001,
  '/farms': 9001,
  '/kyc': 9001,
  '/documents': 9001,
  '/farm-registration': 9001,
  '/crop-planning': 9001,
  '/gis': 9003,
  '/financial': 8000,
  '/market': 8000,
  '/ai': 8000,
  '/iot': 8000,
  '/livestock': 8000,
  '/tasks': 9009,
  '/inventory': 8000,
  '/notifications': 8000,
  '/traceability': 8000,
  '/compliance': 8000,
  '/integration': 8000,
};

// Unified API client (production uses individual services, dev uses direct ports)
export const apiClient = axios.create({
  baseURL: API_GATEWAY_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Legacy alias for backward compatibility (points to same client)
export const farmerClient = apiClient;

// Request interceptor - route to appropriate service
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (config.url) {
      // Extract the service path (e.g., "/auth" from "/auth/login")
      const urlParts = config.url.split('/').filter(Boolean);
      if (urlParts.length > 0) {
        const servicePath = '/' + urlParts[0];
        const serviceName = urlParts[0]; // e.g., "auth", "farmers", etc.

        // Production mode - use individual service URLs
        if (isProductionMode) {
          let serviceUrl: string | undefined;

          // Map service paths to service URLs
          switch (serviceName) {
            case 'auth':
              serviceUrl = PRODUCTION_SERVICE_URLS.auth;
              break;
            case 'farmers':
            case 'farms':
            case 'kyc':
            case 'documents':
            case 'farm-registration':
            case 'crop-planning':
            case 'eligibility':
              // All these use the farmer service
              serviceUrl = PRODUCTION_SERVICE_URLS.farmer;
              break;
            case 'gis':
              serviceUrl = PRODUCTION_SERVICE_URLS.gis;
              break;
            case 'financial':
              serviceUrl = PRODUCTION_SERVICE_URLS.financial;
              break;
            case 'market':
              serviceUrl = PRODUCTION_SERVICE_URLS.market;
              break;
            case 'ai':
              serviceUrl = PRODUCTION_SERVICE_URLS.ai;
              break;
            case 'iot':
              serviceUrl = PRODUCTION_SERVICE_URLS.iot;
              break;
            case 'livestock':
              serviceUrl = PRODUCTION_SERVICE_URLS.livestock;
              break;
            case 'tasks':
              serviceUrl = PRODUCTION_SERVICE_URLS.task;
              break;
            case 'inventory':
              serviceUrl = PRODUCTION_SERVICE_URLS.inventory;
              break;
            case 'notifications':
              serviceUrl = PRODUCTION_SERVICE_URLS.notification;
              break;
            case 'traceability':
              serviceUrl = PRODUCTION_SERVICE_URLS.traceability;
              break;
            case 'compliance':
              serviceUrl = PRODUCTION_SERVICE_URLS.compliance;
              break;
            case 'integration':
              serviceUrl = PRODUCTION_SERVICE_URLS.integration;
              break;
          }

          if (serviceUrl) {
            config.baseURL = serviceUrl;
            // Keep the full path including service prefix, prepend /api/v1
            // e.g., /auth/register/phone -> /api/v1/auth/register/phone
            // Backend services expect the service prefix in the route path
            config.url = '/api/v1' + config.url;
            console.log(`[PRODUCTION] Routing to ${config.baseURL}${config.url}`);
          }
        }
        // Development mode - use direct service ports
        else if (isDevelopmentMode) {
          const servicePort = SERVICE_PORTS[servicePath];

          if (servicePort) {
            const host = getDevServerHost();
            config.baseURL = `http://${host}:${servicePort}`;
            // Keep the full path including service prefix, prepend /api/v1
            config.url = '/api/v1' + config.url;
            console.log(`[DEV MODE] Routing to ${config.baseURL}${config.url}`);
          }
        }
        // Otherwise use unified gateway (config.baseURL already set)
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAuthStore().getState().accessToken;
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
        await getAuthStore().getState().refreshTokens();
        const token = getAuthStore().getState().accessToken;
        if (token && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return apiClient(originalRequest);
      } catch {
        await getAuthStore().getState().logout();
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

  loginPhone: async (phoneNumber: string, pin: string) => {
    const response = await apiClient.post('/auth/login/phone', {
      phone_number: phoneNumber,
      pin,
    });
    return response.data;
  },

  registerPhone: async (data: {
    firstName: string;
    lastName: string;
    phone: string;
    pin: string;
  }) => {
    const response = await apiClient.post('/auth/register/phone', {
      first_name: data.firstName,
      last_name: data.lastName,
      phone_number: data.phone,
      pin: data.pin,
    });
    return response.data;
  },
};

// Farmer API
export const farmerApi = {
  getProfile: async (farmerId: string) => {
    const response = await farmerClient.get(`/farmers/${farmerId}`);
    return response.data;
  },

  getByUserId: async (userId: string) => {
    const response = await farmerClient.get(`/farmers/by-user/${userId}`);
    return response.data;
  },

  create: async (data: {
    user_id: string;
    tenant_id: string;
    first_name: string;
    last_name: string;
    phone_number: string;
    email?: string;
  }) => {
    const response = await farmerClient.post('/farmers', data);
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

// KYC API
export const kycApi = {
  startKYC: async (farmerId: string, requiredDocuments?: string[], requiredBiometrics?: string[]) => {
    const response = await apiClient.post(`/kyc/${farmerId}/start`, {
      required_documents: requiredDocuments,
      required_biometrics: requiredBiometrics,
    });
    return response.data;
  },

  getStatus: async (farmerId: string) => {
    const response = await apiClient.get(`/kyc/${farmerId}/status`);
    return response.data;
  },

  completeStep: async (farmerId: string, step: string, data?: any) => {
    const response = await apiClient.post(`/kyc/${farmerId}/step/complete`, {
      step,
      data,
    });
    return response.data;
  },

  uploadDocument: async (
    farmerId: string,
    file: any,
    documentType: string,
    documentNumber?: string
  ) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    if (documentNumber) {
      formData.append('document_number', documentNumber);
    }

    const response = await apiClient.post(`/kyc/${farmerId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  submitForReview: async (farmerId: string) => {
    const response = await apiClient.post(`/kyc/${farmerId}/submit`);
    return response.data;
  },

  runExternalVerifications: async (farmerId: string) => {
    const response = await apiClient.post(`/kyc/${farmerId}/verify/external`);
    return response.data;
  },

  getVerificationStatus: async (farmerId: string) => {
    const response = await apiClient.get(`/kyc/${farmerId}/verify/status`);
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

// GIS API (uses unified gateway client)
export const gisApi = {
  reverseGeocode: async (latitude: number, longitude: number) => {
    const response = await apiClient.post('/gis/reverse-geocode', {
      latitude,
      longitude,
    });
    return response.data;
  },

  validateCoordinates: async (latitude: number, longitude: number) => {
    const response = await apiClient.post('/gis/validate-coordinates', {
      latitude,
      longitude,
    });
    return response.data;
  },

  validatePolygon: async (geojson: any) => {
    const response = await apiClient.post('/gis/validate-polygon', {
      geojson,
    });
    return response.data;
  },

  calculateArea: async (geojson: any) => {
    const response = await apiClient.post('/gis/calculate-area', {
      geojson,
    });
    return response.data;
  },

  checkPointInBoundary: async (
    latitude: number,
    longitude: number,
    boundary: any
  ) => {
    const response = await apiClient.post('/gis/point-in-boundary', {
      latitude,
      longitude,
      boundary,
    });
    return response.data;
  },

  checkOverlap: async (boundary1: any, boundary2: any) => {
    const response = await apiClient.post('/gis/check-overlap', {
      boundary1,
      boundary2,
    });
    return response.data;
  },

  simplifyPolygon: async (geojson: any, tolerance: number = 0.0001) => {
    const response = await apiClient.post('/gis/simplify-polygon', {
      geojson,
      tolerance,
    });
    return response.data;
  },
};

// Crop Planning API (uses farmer service)
export const cropPlanningApi = {
  // Dashboard
  getDashboard: async (farmerId: string) => {
    const response = await apiClient.get(`/crop-planning/dashboard?farmer_id=${farmerId}`);
    return response.data;
  },

  // Templates
  listTemplates: async (tenantId: string, params?: { cropName?: string; region?: string; season?: string; page?: number; pageSize?: number }) => {
    const queryParams = new URLSearchParams({ tenant_id: tenantId });
    if (params?.cropName) queryParams.append('crop_name', params.cropName);
    if (params?.region) queryParams.append('region', params.region);
    if (params?.season) queryParams.append('season', params.season);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());
    const response = await apiClient.get(`/crop-planning/templates?${queryParams.toString()}`);
    return response.data;
  },

  getTemplate: async (templateId: string) => {
    const response = await apiClient.get(`/crop-planning/templates/${templateId}`);
    return response.data;
  },

  getTemplateRecommendations: async (tenantId: string, farmId: string, cropName: string, plannedDate: string) => {
    const queryParams = new URLSearchParams({
      tenant_id: tenantId,
      farm_id: farmId,
      crop_name: cropName,
      planned_date: plannedDate,
    });
    const response = await apiClient.get(`/crop-planning/templates/recommend?${queryParams.toString()}`);
    return response.data;
  },

  // Plans
  listPlans: async (params?: { farmerId?: string; farmId?: string; status?: string; season?: string; year?: number; page?: number; pageSize?: number }) => {
    const queryParams = new URLSearchParams();
    if (params?.farmerId) queryParams.append('farmer_id', params.farmerId);
    if (params?.farmId) queryParams.append('farm_id', params.farmId);
    if (params?.status) queryParams.append('plan_status', params.status);
    if (params?.season) queryParams.append('season', params.season);
    if (params?.year) queryParams.append('year', params.year.toString());
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());
    const response = await apiClient.get(`/crop-planning/plans?${queryParams.toString()}`);
    return response.data;
  },

  createPlan: async (data: {
    farmer_id: string;
    farm_id: string;
    template_id?: string | null;
    name: string;
    crop_name: string;
    variety?: string | null;
    season: string;
    year: number;
    planned_planting_date: string;
    planned_acreage: number;
    expected_harvest_date?: string | null;
    expected_yield_kg?: number | null;
    notes?: string | null;
    generate_activities?: boolean;
  }) => {
    const response = await apiClient.post('/crop-planning/plans', data);
    return response.data;
  },

  getPlan: async (planId: string) => {
    const response = await apiClient.get(`/crop-planning/plans/${planId}`);
    return response.data;
  },

  updatePlan: async (planId: string, data: Record<string, any>) => {
    const response = await apiClient.patch(`/crop-planning/plans/${planId}`, data);
    return response.data;
  },

  deletePlan: async (planId: string) => {
    await apiClient.delete(`/crop-planning/plans/${planId}`);
  },

  activatePlan: async (planId: string, data?: { actual_planting_date?: string; actual_planted_acreage?: number }) => {
    const response = await apiClient.post(`/crop-planning/plans/${planId}/activate`, data || {});
    return response.data;
  },

  advanceStage: async (planId: string, data: { new_stage: string; notes?: string }) => {
    const response = await apiClient.post(`/crop-planning/plans/${planId}/advance-stage`, data);
    return response.data;
  },

  completePlan: async (planId: string, data: { actual_harvest_date: string; actual_yield_kg: number; notes?: string }) => {
    const response = await apiClient.post(`/crop-planning/plans/${planId}/complete`, data);
    return response.data;
  },

  getPlanStatistics: async (planId: string) => {
    const response = await apiClient.get(`/crop-planning/plans/${planId}/statistics`);
    return response.data;
  },

  // Activities
  listActivities: async (planId: string, params?: { status?: string; fromDate?: string; toDate?: string; page?: number; pageSize?: number }) => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('activity_status', params.status);
    if (params?.fromDate) queryParams.append('from_date', params.fromDate);
    if (params?.toDate) queryParams.append('to_date', params.toDate);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());
    const response = await apiClient.get(`/crop-planning/plans/${planId}/activities?${queryParams.toString()}`);
    return response.data;
  },

  getActivity: async (activityId: string) => {
    const response = await apiClient.get(`/crop-planning/activities/${activityId}`);
    return response.data;
  },

  completeActivity: async (activityId: string, data: Record<string, any>) => {
    const response = await apiClient.post(`/crop-planning/activities/${activityId}/complete`, data);
    return response.data;
  },

  skipActivity: async (activityId: string, reason: string) => {
    const response = await apiClient.post(`/crop-planning/activities/${activityId}/skip`, { reason });
    return response.data;
  },

  getUpcomingActivities: async (farmerId: string, daysAhead: number = 7) => {
    const response = await apiClient.get(`/crop-planning/activities/upcoming?farmer_id=${farmerId}&days_ahead=${daysAhead}`);
    return response.data;
  },

  // Inputs
  listInputs: async (planId: string) => {
    const response = await apiClient.get(`/crop-planning/plans/${planId}/inputs`);
    return response.data;
  },

  createInput: async (planId: string, data: Record<string, any>) => {
    const response = await apiClient.post(`/crop-planning/plans/${planId}/inputs`, { ...data, crop_plan_id: planId });
    return response.data;
  },

  getInput: async (inputId: string) => {
    const response = await apiClient.get(`/crop-planning/inputs/${inputId}`);
    return response.data;
  },

  updateInput: async (inputId: string, data: Record<string, any>) => {
    const response = await apiClient.patch(`/crop-planning/inputs/${inputId}`, data);
    return response.data;
  },

  verifyInputQr: async (inputId: string, qrCodeData: Record<string, any>) => {
    const response = await apiClient.post(`/crop-planning/inputs/${inputId}/verify-qr`, { qr_code_data: qrCodeData });
    return response.data;
  },

  calculateInputs: async (tenantId: string, cropName: string, acreage: number, variety?: string) => {
    const queryParams = new URLSearchParams({ tenant_id: tenantId, crop_name: cropName, acreage: acreage.toString() });
    if (variety) queryParams.append('variety', variety);
    const response = await apiClient.get(`/crop-planning/calculate-inputs?${queryParams.toString()}`);
    return response.data;
  },

  // Irrigation
  listIrrigation: async (planId: string) => {
    const response = await apiClient.get(`/crop-planning/plans/${planId}/irrigation`);
    return response.data;
  },

  createIrrigation: async (planId: string, data: Record<string, any>) => {
    const response = await apiClient.post(`/crop-planning/plans/${planId}/irrigation`, { ...data, crop_plan_id: planId });
    return response.data;
  },

  generateIrrigation: async (planId: string, data: Record<string, any>) => {
    const response = await apiClient.post(`/crop-planning/plans/${planId}/irrigation/generate`, data);
    return response.data;
  },

  getIrrigation: async (scheduleId: string) => {
    const response = await apiClient.get(`/crop-planning/irrigation/${scheduleId}`);
    return response.data;
  },

  updateIrrigation: async (scheduleId: string, data: Record<string, any>) => {
    const response = await apiClient.patch(`/crop-planning/irrigation/${scheduleId}`, data);
    return response.data;
  },

  completeIrrigation: async (scheduleId: string, data: Record<string, any>) => {
    const response = await apiClient.post(`/crop-planning/irrigation/${scheduleId}/complete`, data);
    return response.data;
  },

  // Alerts
  listAlerts: async (farmerId: string, params?: { unreadOnly?: boolean; page?: number; pageSize?: number }) => {
    const queryParams = new URLSearchParams({ farmer_id: farmerId });
    if (params?.unreadOnly) queryParams.append('unread_only', 'true');
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());
    const response = await apiClient.get(`/crop-planning/alerts?${queryParams.toString()}`);
    return response.data;
  },

  markAlertRead: async (alertId: string) => {
    const response = await apiClient.post(`/crop-planning/alerts/${alertId}/read`);
    return response.data;
  },

  dismissAlert: async (alertId: string) => {
    const response = await apiClient.post(`/crop-planning/alerts/${alertId}/dismiss`);
    return response.data;
  },
};

// Task API (uses task service)
export const taskApi = {
  list: async (farmerId: string, params?: { status?: string; category?: string; limit?: number; offset?: number }) => {
    const queryParams = new URLSearchParams({ farmer_id: farmerId });
    if (params?.status) queryParams.append('status', params.status);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    const response = await apiClient.get(`/tasks/?${queryParams.toString()}`);
    return response.data;
  },

  create: async (data: Record<string, any>) => {
    const response = await apiClient.post('/tasks/', data);
    return response.data;
  },

  get: async (taskId: string) => {
    const response = await apiClient.get(`/tasks/${taskId}`);
    return response.data;
  },

  update: async (taskId: string, data: Record<string, any>) => {
    const response = await apiClient.patch(`/tasks/${taskId}`, data);
    return response.data;
  },

  delete: async (taskId: string) => {
    await apiClient.delete(`/tasks/${taskId}`);
  },

  complete: async (taskId: string, notes?: string) => {
    const response = await apiClient.post(`/tasks/${taskId}/complete`, notes ? { notes } : {});
    return response.data;
  },

  listComments: async (taskId: string) => {
    const response = await apiClient.get(`/tasks/${taskId}/comments`);
    return response.data;
  },

  addComment: async (taskId: string, data: { content: string; author_id: string }) => {
    const response = await apiClient.post(`/tasks/${taskId}/comments`, data);
    return response.data;
  },

  getStats: async (farmerId: string) => {
    const response = await apiClient.get(`/tasks/stats?farmer_id=${farmerId}`);
    return response.data;
  },
};
