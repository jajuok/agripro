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

// =============================================================================
// Crop Planning Constants
// =============================================================================

export const SEASONS = {
  LONG_RAINS: 'long_rains',
  SHORT_RAINS: 'short_rains',
  IRRIGATED: 'irrigated',
  DRY_SEASON: 'dry_season',
} as const;

export const SEASON_LABELS: Record<string, string> = {
  long_rains: 'Long Rains',
  short_rains: 'Short Rains',
  irrigated: 'Irrigated',
  dry_season: 'Dry Season',
};

export const CROP_PLAN_STATUS = {
  DRAFT: 'draft',
  ACTIVE: 'active',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
} as const;

export const CROP_PLAN_STATUS_COLORS: Record<string, string> = {
  draft: '#9E9E9E',
  active: '#4CAF50',
  completed: '#2196F3',
  cancelled: '#D32F2F',
};

export const ACTIVITY_TYPES = {
  LAND_PREPARATION: 'land_preparation',
  PLANTING: 'planting',
  FERTILIZER_APPLICATION: 'fertilizer_application',
  PESTICIDE_APPLICATION: 'pesticide_application',
  WEEDING: 'weeding',
  IRRIGATION: 'irrigation',
  PRUNING: 'pruning',
  THINNING: 'thinning',
  STAKING: 'staking',
  HARVESTING: 'harvesting',
  POST_HARVEST: 'post_harvest',
  SOIL_TESTING: 'soil_testing',
  SCOUTING: 'scouting',
  OTHER: 'other',
} as const;

export const ACTIVITY_TYPE_LABELS: Record<string, string> = {
  land_preparation: 'Land Preparation',
  planting: 'Planting',
  fertilizer_application: 'Fertilizer',
  pesticide_application: 'Pesticide',
  weeding: 'Weeding',
  irrigation: 'Irrigation',
  pruning: 'Pruning',
  thinning: 'Thinning',
  staking: 'Staking',
  harvesting: 'Harvesting',
  post_harvest: 'Post Harvest',
  soil_testing: 'Soil Testing',
  scouting: 'Scouting',
  other: 'Other',
};

export const ACTIVITY_TYPE_ICONS: Record<string, string> = {
  land_preparation: '🚜',
  planting: '🌱',
  fertilizer_application: '🧪',
  pesticide_application: '🛡️',
  weeding: '🌿',
  irrigation: '💧',
  pruning: '✂️',
  thinning: '🌾',
  staking: '🪵',
  harvesting: '🌽',
  post_harvest: '📦',
  soil_testing: '🔬',
  scouting: '👀',
  other: '📋',
};

export const ACTIVITY_STATUS = {
  SCHEDULED: 'scheduled',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  SKIPPED: 'skipped',
  OVERDUE: 'overdue',
} as const;

export const ACTIVITY_STATUS_COLORS: Record<string, string> = {
  scheduled: '#2196F3',
  in_progress: '#FF9800',
  completed: '#4CAF50',
  skipped: '#9E9E9E',
  overdue: '#D32F2F',
};

export const INPUT_CATEGORIES = {
  SEED: 'seed',
  FERTILIZER: 'fertilizer',
  PESTICIDE: 'pesticide',
  HERBICIDE: 'herbicide',
  FUNGICIDE: 'fungicide',
  GROWTH_REGULATOR: 'growth_regulator',
  OTHER: 'other',
} as const;

export const INPUT_CATEGORY_LABELS: Record<string, string> = {
  seed: 'Seeds',
  fertilizer: 'Fertilizer',
  pesticide: 'Pesticide',
  herbicide: 'Herbicide',
  fungicide: 'Fungicide',
  growth_regulator: 'Growth Regulator',
  other: 'Other',
};

export const PROCUREMENT_STATUS = {
  PLANNED: 'planned',
  ORDERED: 'ordered',
  RECEIVED: 'received',
  APPLIED: 'applied',
} as const;

export const PROCUREMENT_STATUS_COLORS: Record<string, string> = {
  planned: '#9E9E9E',
  ordered: '#FF9800',
  received: '#2196F3',
  applied: '#4CAF50',
};

export const IRRIGATION_METHODS = {
  DRIP: 'drip',
  SPRINKLER: 'sprinkler',
  FURROW: 'furrow',
  FLOOD: 'flood',
  MANUAL: 'manual',
  PIVOT: 'pivot',
  SUBSURFACE: 'subsurface',
} as const;

export const IRRIGATION_METHOD_LABELS: Record<string, string> = {
  drip: 'Drip',
  sprinkler: 'Sprinkler',
  furrow: 'Furrow',
  flood: 'Flood',
  manual: 'Manual',
  pivot: 'Pivot',
  subsurface: 'Subsurface',
};

export const ALERT_SEVERITY_COLORS: Record<string, string> = {
  info: '#2196F3',
  warning: '#FF9800',
  critical: '#D32F2F',
};

// =============================================================================
// Task Management Constants
// =============================================================================

export const TASK_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
} as const;

export const TASK_STATUS_COLORS: Record<string, string> = {
  pending: '#FF9800',
  in_progress: '#2196F3',
  completed: '#4CAF50',
  cancelled: '#9E9E9E',
};

export const TASK_CATEGORY_LABELS: Record<string, string> = {
  maintenance: 'Maintenance',
  administrative: 'Administrative',
  equipment: 'Equipment',
  infrastructure: 'Infrastructure',
  procurement: 'Procurement',
  inspection: 'Inspection',
  livestock: 'Livestock',
  general: 'General',
  other: 'Other',
};

export const TASK_CATEGORY_ICONS: Record<string, string> = {
  maintenance: '🔧',
  administrative: '📋',
  equipment: '🚜',
  infrastructure: '🏗️',
  procurement: '🛒',
  inspection: '🔍',
  livestock: '🐄',
  general: '📌',
  other: '📝',
};
