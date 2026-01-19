import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/store/auth';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
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
    const response = await apiClient.post('/auth/register', {
      email: data.email,
      password: data.password,
      first_name: data.firstName,
      last_name: data.lastName,
      phone_number: data.phone,
    });
    return response.data;
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
    const response = await apiClient.get(`/farmers/${farmerId}`);
    return response.data;
  },

  updateProfile: async (farmerId: string, data: any) => {
    const response = await apiClient.patch(`/farmers/${farmerId}`, data);
    return response.data;
  },

  getKycStatus: async (farmerId: string) => {
    const response = await apiClient.get(`/kyc/${farmerId}/status`);
    return response.data;
  },
};

// Farm API
export const farmApi = {
  list: async (farmerId: string) => {
    const response = await apiClient.get(`/farms/farmer/${farmerId}`);
    return response.data;
  },

  get: async (farmId: string) => {
    const response = await apiClient.get(`/farms/${farmId}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await apiClient.post('/farms', data);
    return response.data;
  },

  update: async (farmId: string, data: any) => {
    const response = await apiClient.patch(`/farms/${farmId}`, data);
    return response.data;
  },
};

// Document API
export const documentApi = {
  upload: async (farmerId: string, documentType: string, file: any) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const response = await apiClient.post(
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
    const response = await apiClient.get(`/documents/farmer/${farmerId}`);
    return response.data;
  },
};
