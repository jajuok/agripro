export const COLORS = {
  primary: '#1B5E20',
  primaryLight: '#4CAF50',
  primaryDark: '#0D3D14',
  secondary: '#FF9800',
  success: '#4CAF50',
  warning: '#FF9800',
  error: '#D32F2F',
  info: '#2196F3',
  white: '#FFFFFF',
  black: '#000000',
  gray: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#EEEEEE',
    300: '#E0E0E0',
    400: '#BDBDBD',
    500: '#9E9E9E',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
  },
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const FONT_SIZES = {
  xs: 10,
  sm: 12,
  md: 14,
  lg: 16,
  xl: 18,
  xxl: 24,
  xxxl: 32,
};

export const KYC_STATUS = {
  PENDING: 'pending',
  IN_REVIEW: 'in_review',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  EXPIRED: 'expired',
} as const;

export const DOCUMENT_TYPES = {
  NATIONAL_ID: 'national_id',
  PASSPORT: 'passport',
  LAND_TITLE: 'land_title',
  LEASE_AGREEMENT: 'lease_agreement',
  TAX_ID: 'tax_id',
  BANK_STATEMENT: 'bank_statement',
  SOIL_TEST: 'soil_test',
} as const;

export const OWNERSHIP_TYPES = {
  OWNED: 'owned',
  LEASED: 'leased',
  COMMUNAL: 'communal',
  FAMILY: 'family',
} as const;
