import { create } from 'zustand';
import { kycApi } from '@/services/api';

export type KYCStep =
  | 'personal_info'
  | 'documents'
  | 'biometrics'
  | 'bank_info'
  | 'external_verification'
  | 'review'
  | 'complete';

export type DocumentType =
  | 'national_id'
  | 'passport'
  | 'land_title'
  | 'lease_agreement'
  | 'tax_id'
  | 'bank_statement'
  | 'soil_test'
  | 'other';

export type DocumentSubmission = {
  document_type: string;
  document_id?: string;
  is_submitted: boolean;
  is_verified: boolean;
  verified_at?: string;
};

export type BiometricCapture = {
  biometric_type: string;
  is_captured: boolean;
  is_verified: boolean;
  quality_score?: number;
};

export type ExternalVerification = {
  verification_type: string;
  provider: string;
  status: string;
  is_verified: boolean;
  completed_at?: string;
};

export type KYCStatus = {
  farmer_id: string;
  current_step: KYCStep;
  overall_status: string;
  progress_percentage: number;

  // Step completion
  personal_info_complete: boolean;
  documents_complete: boolean;
  biometrics_complete: boolean;
  bank_info_complete: boolean;

  // Document status
  required_documents: string[];
  documents_submitted: DocumentSubmission[];
  missing_documents: string[];

  // Biometric status
  required_biometrics: string[];
  biometrics_captured: BiometricCapture[];
  missing_biometrics: string[];

  // External verifications
  external_verifications: ExternalVerification[];

  // Review status
  in_review_queue: boolean;
  submitted_at?: string;
  reviewed_at?: string;
  rejection_reason?: string;

  created_at?: string;
  updated_at?: string;
};

type KYCState = {
  status: KYCStatus | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  startKYC: (farmerId: string) => Promise<void>;
  getStatus: (farmerId: string) => Promise<void>;
  completeStep: (farmerId: string, step: KYCStep, data?: any) => Promise<void>;
  uploadDocument: (farmerId: string, file: any, documentType: string, documentNumber?: string) => Promise<any>;
  submitForReview: (farmerId: string) => Promise<void>;
  reset: () => void;
};

export const useKYCStore = create<KYCState>((set, get) => ({
  status: null,
  isLoading: false,
  error: null,

  startKYC: async (farmerId: string) => {
    set({ isLoading: true, error: null });
    try {
      const status = await kycApi.startKYC(farmerId);
      set({ status, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || error.message || 'Failed to start KYC',
        isLoading: false
      });
      throw error;
    }
  },

  getStatus: async (farmerId: string) => {
    set({ isLoading: true, error: null });
    try {
      const status = await kycApi.getStatus(farmerId);
      set({ status, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || error.message || 'Failed to get KYC status',
        isLoading: false
      });
      throw error;
    }
  },

  completeStep: async (farmerId: string, step: KYCStep, data?: any) => {
    set({ isLoading: true, error: null });
    try {
      const status = await kycApi.completeStep(farmerId, step, data);
      set({ status, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || error.message || 'Failed to complete step',
        isLoading: false
      });
      throw error;
    }
  },

  uploadDocument: async (farmerId: string, file: any, documentType: string, documentNumber?: string) => {
    set({ isLoading: true, error: null });
    try {
      const result = await kycApi.uploadDocument(farmerId, file, documentType, documentNumber);
      // Refresh status after upload
      await get().getStatus(farmerId);
      return result;
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || error.message || 'Failed to upload document',
        isLoading: false
      });
      throw error;
    }
  },

  submitForReview: async (farmerId: string) => {
    set({ isLoading: true, error: null });
    try {
      const status = await kycApi.submitForReview(farmerId);
      set({ status, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || error.message || 'Failed to submit for review',
        isLoading: false
      });
      throw error;
    }
  },

  reset: () => {
    set({ status: null, isLoading: false, error: null });
  },
}));
