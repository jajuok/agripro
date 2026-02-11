import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import * as SecureStore from 'expo-secure-store';
import { authApi, farmerApi } from '@/services/api';

type User = {
  id: string;
  farmerId: string | null;
  email: string | null;
  phoneNumber: string;
  firstName: string;
  lastName: string;
  roles: string[];
};

type AuthState = {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  cachedPhoneNumber: string | null;
  login: (phoneNumber: string, pin: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<void>;
};

type RegisterData = {
  firstName: string;
  lastName: string;
  phone: string;
  pin: string;
};

const secureStorage = {
  getItem: async (name: string) => {
    return await SecureStore.getItemAsync(name);
  },
  setItem: async (name: string, value: string) => {
    await SecureStore.setItemAsync(name, value);
  },
  removeItem: async (name: string) => {
    await SecureStore.deleteItemAsync(name);
  },
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      cachedPhoneNumber: null,

      login: async (phoneNumber: string, pin: string) => {
        set({ isLoading: true });
        try {
          const response = await authApi.loginPhone(phoneNumber, pin);

          // Resolve farmer profile
          let farmerId: string | null = null;
          try {
            const farmer = await farmerApi.getByUserId(response.user_id);
            farmerId = farmer.id;
          } catch {
            // Farmer profile may not exist yet
          }

          set({
            user: {
              id: response.user_id,
              farmerId,
              email: response.email || null,
              phoneNumber: response.phone_number || phoneNumber,
              firstName: response.first_name || '',
              lastName: response.last_name || '',
              roles: response.roles,
            },
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
            cachedPhoneNumber: phoneNumber,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true });
        try {
          const response = await authApi.registerPhone(data);

          // Auto-create farmer profile
          let farmerId: string | null = null;
          try {
            const farmer = await farmerApi.create({
              user_id: response.user_id,
              tenant_id: '00000000-0000-0000-0000-000000000001',
              first_name: data.firstName,
              last_name: data.lastName,
              phone_number: data.phone,
            });
            farmerId = farmer.id;
          } catch {
            // Farmer profile creation failed - user can still use the app
            console.warn('Failed to create farmer profile');
          }

          set({
            user: {
              id: response.user_id,
              farmerId,
              email: response.email || null,
              phoneNumber: data.phone,
              firstName: data.firstName,
              lastName: data.lastName,
              roles: response.roles,
            },
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
            cachedPhoneNumber: data.phone,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        const { refreshToken } = get();
        // Revoke the refresh token on the server first (with timeout to prevent hanging)
        if (refreshToken) {
          try {
            await Promise.race([
              authApi.logout(refreshToken),
              new Promise((_, reject) => setTimeout(() => reject(new Error('Logout timeout')), 5000))
            ]);
          } catch {
            // Ignore logout errors - we'll clear state regardless
          }
        }
        // Clear state after API call completes (or times out)
        // NOTE: cachedPhoneNumber is intentionally NOT cleared so returning users only need PIN
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      refreshTokens: async () => {
        const { refreshToken } = get();
        if (!refreshToken) return;

        try {
          const response = await authApi.refresh(refreshToken);
          set({
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
          });
        } catch {
          await get().logout();
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => secureStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        cachedPhoneNumber: state.cachedPhoneNumber,
      }),
    }
  )
);
