/**
 * Crop Planning TypeScript types.
 * Mirrors Pydantic schemas from services/farmer/app/schemas/crop_planning.py
 */

// =============================================================================
// Enums (as string union types)
// =============================================================================

export type Season = 'long_rains' | 'short_rains' | 'irrigated' | 'dry_season';

export type CropPlanStatus = 'draft' | 'active' | 'completed' | 'cancelled';

export type ActivityStatus = 'scheduled' | 'in_progress' | 'completed' | 'skipped' | 'overdue';

export type ActivityType =
  | 'land_preparation'
  | 'planting'
  | 'fertilizer_application'
  | 'pesticide_application'
  | 'weeding'
  | 'irrigation'
  | 'pruning'
  | 'thinning'
  | 'staking'
  | 'harvesting'
  | 'post_harvest'
  | 'soil_testing'
  | 'scouting'
  | 'other';

export type InputCategory =
  | 'seed'
  | 'fertilizer'
  | 'pesticide'
  | 'herbicide'
  | 'fungicide'
  | 'growth_regulator'
  | 'other';

export type ProcurementStatus = 'planned' | 'ordered' | 'received' | 'applied';

export type IrrigationMethod =
  | 'drip'
  | 'sprinkler'
  | 'furrow'
  | 'flood'
  | 'manual'
  | 'pivot'
  | 'subsurface';

export type IrrigationStatus = 'scheduled' | 'completed' | 'skipped';

export type AlertType =
  | 'activity_reminder'
  | 'activity_overdue'
  | 'weather_warning'
  | 'planting_window'
  | 'irrigation_reminder'
  | 'input_reminder'
  | 'stage_transition'
  | 'harvest_reminder';

export type AlertSeverity = 'info' | 'warning' | 'critical';

// =============================================================================
// Growth Stage Types
// =============================================================================

export type GrowthStageActivity = {
  activityType: ActivityType;
  title: string;
  description: string | null;
  dayOffset: number;
  durationHours: number | null;
  isWeatherDependent: boolean;
  weatherConditions: Record<string, any> | null;
};

export type GrowthStage = {
  name: string;
  startDay: number;
  endDay: number;
  description: string | null;
  activities: GrowthStageActivity[];
  waterRequirementMmPerDay: number | null;
  criticalForYield: boolean;
};

// =============================================================================
// Crop Calendar Template
// =============================================================================

export type CropCalendarTemplate = {
  id: string;
  tenantId: string;
  cropName: string;
  variety: string | null;
  regionType: string;
  regionValue: string | null;
  season: Season;
  recommendedPlantingStartMonth: number;
  recommendedPlantingEndMonth: number;
  totalDaysToHarvest: number;
  growthStages: GrowthStage[] | null;
  seedRateKgPerAcre: number | null;
  fertilizerRequirements: Record<string, any> | null;
  expectedYieldKgPerAcreMin: number | null;
  expectedYieldKgPerAcreMax: number | null;
  waterRequirementsMm: number | null;
  criticalWaterStages: string[] | null;
  source: string | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
};

export type TemplateRecommendation = {
  template: CropCalendarTemplate;
  matchScore: number;
  matchReasons: string[];
  warnings: string[] | null;
};

// =============================================================================
// Crop Plan Summary
// =============================================================================

export type CropPlanSummary = {
  id: string;
  name: string;
  cropName: string;
  variety: string | null;
  season: string;
  year: number;
  status: CropPlanStatus;
  farmId: string;
  farmName: string;
  plannedPlantingDate: string;
  plannedAcreage: number;
  currentGrowthStage: string | null;
  activitiesTotal: number;
  activitiesCompleted: number;
  activitiesOverdue: number;
  createdAt: string;
};

// =============================================================================
// Crop Plan
// =============================================================================

export type CropPlan = {
  id: string;
  farmerId: string;
  farmId: string;
  templateId: string | null;
  name: string;
  cropName: string;
  variety: string | null;
  season: Season;
  year: number;
  status: CropPlanStatus;
  plannedPlantingDate: string;
  expectedHarvestDate: string | null;
  actualPlantingDate: string | null;
  actualHarvestDate: string | null;
  optimalPlantingWindowStart: string | null;
  optimalPlantingWindowEnd: string | null;
  plannedAcreage: number;
  actualPlantedAcreage: number | null;
  expectedYieldKg: number | null;
  actualYieldKg: number | null;
  currentGrowthStage: string | null;
  currentGrowthStageStart: string | null;
  growthStageHistory: Record<string, any>[] | null;
  estimatedTotalCost: number | null;
  actualTotalCost: number | null;
  weatherDataSnapshot: Record<string, any> | null;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
  activitiesTotal: number | null;
  activitiesCompleted: number | null;
  inputsTotalCost: number | null;
};

// =============================================================================
// Planned Activity
// =============================================================================

export type PlannedActivity = {
  id: string;
  cropPlanId: string;
  activityType: ActivityType;
  title: string;
  description: string | null;
  growthStage: string | null;
  scheduledDate: string;
  scheduledEndDate: string | null;
  durationHours: number | null;
  status: ActivityStatus;
  earliestDate: string | null;
  latestDate: string | null;
  isWeatherDependent: boolean;
  weatherConditionsRequired: Record<string, any> | null;
  completedAt: string | null;
  actualDate: string | null;
  completionNotes: string | null;
  completionPhotos: string[] | null;
  gpsLatitude: number | null;
  gpsLongitude: number | null;
  inputsUsed: Record<string, any>[] | null;
  estimatedCost: number | null;
  actualCost: number | null;
  priority: number;
  reminderDaysBefore: number;
  alertSent: boolean;
  createdAt: string;
  updatedAt: string;
};

export type UpcomingActivity = {
  activity: PlannedActivity;
  planId: string;
  planName: string;
  cropName: string;
  farmName: string;
  daysUntil: number;
  isOverdue: boolean;
};

// =============================================================================
// Input Requirement
// =============================================================================

export type InputRequirement = {
  id: string;
  cropPlanId: string;
  category: InputCategory;
  name: string;
  brand: string | null;
  quantityRequired: number;
  unit: string;
  isCertified: boolean | null;
  certificationNumber: string | null;
  qrCodeVerified: boolean;
  qrCodeData: Record<string, any> | null;
  qrVerifiedAt: string | null;
  quantityPerAcre: number | null;
  applicationStage: string | null;
  applicationDate: string | null;
  applicationMethod: string | null;
  unitPrice: number | null;
  totalEstimatedCost: number | null;
  actualCost: number | null;
  procurementStatus: ProcurementStatus;
  supplierName: string | null;
  purchaseDate: string | null;
  purchaseLocation: string | null;
  quantityUsed: number | null;
  quantityRemaining: number | null;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
};

// =============================================================================
// Irrigation Schedule
// =============================================================================

export type IrrigationSchedule = {
  id: string;
  cropPlanId: string;
  method: IrrigationMethod;
  scheduledDate: string;
  scheduledDurationMinutes: number | null;
  waterAmountLiters: number | null;
  waterAmountMm: number | null;
  status: IrrigationStatus;
  actualDate: string | null;
  actualDurationMinutes: number | null;
  actualWaterUsedLiters: number | null;
  soilMoistureBefore: number | null;
  soilMoistureAfter: number | null;
  rainfallMmLast24h: number | null;
  temperatureCelsius: number | null;
  evapotranspirationMm: number | null;
  isDeficitIrrigation: boolean;
  deficitPercentage: number | null;
  growthStage: string | null;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
};

// =============================================================================
// Alert
// =============================================================================

export type CropPlanAlert = {
  id: string;
  farmerId: string;
  cropPlanId: string | null;
  activityId: string | null;
  alertType: AlertType;
  title: string;
  message: string;
  severity: AlertSeverity;
  data: Record<string, any> | null;
  channels: string[];
  scheduledFor: string | null;
  sentAt: string | null;
  readAt: string | null;
  dismissedAt: string | null;
  createdAt: string;
};

// =============================================================================
// Dashboard & Statistics
// =============================================================================

export type CropPlanningDashboard = {
  farmerId: string;
  activePlansCount: number;
  draftPlansCount: number;
  completedPlansCount: number;
  totalPlannedAcreage: number;
  activitiesToday: number;
  activitiesOverdue: number;
  activitiesThisWeek: number;
  upcomingActivities: UpcomingActivity[];
  alertsUnread: number;
  recentAlerts: CropPlanAlert[];
};

export type CropPlanStatistics = {
  planId: string;
  daysSincePlanting: number | null;
  daysToHarvest: number | null;
  activitiesTotal: number;
  activitiesCompleted: number;
  activitiesPending: number;
  activitiesOverdue: number;
  completionPercentage: number;
  estimatedCost: number | null;
  actualCost: number | null;
  costVariance: number | null;
  inputsProcuredPercentage: number | null;
};

// =============================================================================
// Request Types
// =============================================================================

export type CropPlanCreateData = {
  farmerId: string;
  farmId: string;
  templateId?: string | null;
  name: string;
  cropName: string;
  variety?: string | null;
  season: Season;
  year: number;
  plannedPlantingDate: string;
  plannedAcreage: number;
  expectedHarvestDate?: string | null;
  expectedYieldKg?: number | null;
  notes?: string | null;
  generateActivities?: boolean;
};

export type ActivityCompletionData = {
  completionNotes?: string | null;
  completionPhotos?: string[] | null;
  gpsLatitude?: number | null;
  gpsLongitude?: number | null;
  inputsUsed?: Record<string, any>[] | null;
  actualCost?: number | null;
  actualDate?: string | null;
};

export type IrrigationGenerateData = {
  startDate: string;
  endDate: string;
  method: IrrigationMethod;
  frequencyDays?: number;
  waterAmountPerEventLiters?: number | null;
  considerRainfall?: boolean;
};

export type IrrigationCompletionData = {
  actualDurationMinutes?: number | null;
  actualWaterUsedLiters?: number | null;
  soilMoistureBefore?: number | null;
  soilMoistureAfter?: number | null;
  notes?: string | null;
  actualDate?: string | null;
};
