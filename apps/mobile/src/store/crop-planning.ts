import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { cropPlanningApi } from '@/services/api';
import type {
  CropPlan,
  CropPlanSummary,
  CropCalendarTemplate,
  TemplateRecommendation,
  PlannedActivity,
  UpcomingActivity,
  InputRequirement,
  IrrigationSchedule,
  CropPlanAlert,
  CropPlanningDashboard,
  CropPlanStatistics,
  CropPlanCreateData,
  ActivityCompletionData,
  IrrigationGenerateData,
  IrrigationCompletionData,
} from '@/types/crop-planning';

// =============================================================================
// snake_case API -> camelCase TS mappers
// =============================================================================

const mapActivity = (d: any): PlannedActivity => ({
  id: d.id,
  cropPlanId: d.crop_plan_id,
  activityType: d.activity_type,
  title: d.title,
  description: d.description ?? null,
  growthStage: d.growth_stage ?? null,
  scheduledDate: d.scheduled_date,
  scheduledEndDate: d.scheduled_end_date ?? null,
  durationHours: d.duration_hours ?? null,
  status: d.status,
  earliestDate: d.earliest_date ?? null,
  latestDate: d.latest_date ?? null,
  isWeatherDependent: d.is_weather_dependent ?? false,
  weatherConditionsRequired: d.weather_conditions_required ?? null,
  completedAt: d.completed_at ?? null,
  actualDate: d.actual_date ?? null,
  completionNotes: d.completion_notes ?? null,
  completionPhotos: d.completion_photos ?? null,
  gpsLatitude: d.gps_latitude ?? null,
  gpsLongitude: d.gps_longitude ?? null,
  inputsUsed: d.inputs_used ?? null,
  estimatedCost: d.estimated_cost ?? null,
  actualCost: d.actual_cost ?? null,
  priority: d.priority ?? 5,
  reminderDaysBefore: d.reminder_days_before ?? 1,
  alertSent: d.alert_sent ?? false,
  createdAt: d.created_at,
  updatedAt: d.updated_at,
});

const mapUpcomingActivity = (d: any): UpcomingActivity => ({
  activity: mapActivity(d.activity),
  planId: d.plan_id,
  planName: d.plan_name,
  cropName: d.crop_name,
  farmName: d.farm_name,
  daysUntil: d.days_until,
  isOverdue: d.is_overdue,
});

const mapPlanSummary = (data: any): CropPlanSummary => ({
  id: data.id,
  name: data.name,
  cropName: data.crop_name,
  variety: data.variety ?? null,
  season: data.season,
  year: data.year,
  status: data.status,
  farmId: data.farm_id,
  farmName: data.farm_name ?? '',
  plannedPlantingDate: data.planned_planting_date,
  plannedAcreage: data.planned_acreage,
  currentGrowthStage: data.current_growth_stage ?? null,
  activitiesTotal: data.activities_total || 0,
  activitiesCompleted: data.activities_completed || 0,
  activitiesOverdue: data.activities_overdue || 0,
  createdAt: data.created_at,
});

const mapPlan = (d: any): CropPlan => ({
  id: d.id,
  farmerId: d.farmer_id,
  farmId: d.farm_id,
  templateId: d.template_id ?? null,
  name: d.name,
  cropName: d.crop_name,
  variety: d.variety ?? null,
  season: d.season,
  year: d.year,
  status: d.status,
  plannedPlantingDate: d.planned_planting_date,
  expectedHarvestDate: d.expected_harvest_date ?? null,
  actualPlantingDate: d.actual_planting_date ?? null,
  actualHarvestDate: d.actual_harvest_date ?? null,
  optimalPlantingWindowStart: d.optimal_planting_window_start ?? null,
  optimalPlantingWindowEnd: d.optimal_planting_window_end ?? null,
  plannedAcreage: d.planned_acreage,
  actualPlantedAcreage: d.actual_planted_acreage ?? null,
  expectedYieldKg: d.expected_yield_kg ?? null,
  actualYieldKg: d.actual_yield_kg ?? null,
  currentGrowthStage: d.current_growth_stage ?? null,
  currentGrowthStageStart: d.current_growth_stage_start ?? null,
  growthStageHistory: d.growth_stage_history ?? null,
  estimatedTotalCost: d.estimated_total_cost ?? null,
  actualTotalCost: d.actual_total_cost ?? null,
  weatherDataSnapshot: d.weather_data_snapshot ?? null,
  notes: d.notes ?? null,
  createdAt: d.created_at,
  updatedAt: d.updated_at,
  activitiesTotal: d.activities_total ?? null,
  activitiesCompleted: d.activities_completed ?? null,
  inputsTotalCost: d.inputs_total_cost ?? null,
});

const mapTemplate = (d: any): CropCalendarTemplate => ({
  id: d.id,
  tenantId: d.tenant_id,
  cropName: d.crop_name,
  variety: d.variety ?? null,
  regionType: d.region_type,
  regionValue: d.region_value ?? null,
  season: d.season,
  recommendedPlantingStartMonth: d.recommended_planting_start_month,
  recommendedPlantingEndMonth: d.recommended_planting_end_month,
  totalDaysToHarvest: d.total_days_to_harvest,
  growthStages: d.growth_stages ?? null,
  seedRateKgPerAcre: d.seed_rate_kg_per_acre ?? null,
  fertilizerRequirements: d.fertilizer_requirements ?? null,
  expectedYieldKgPerAcreMin: d.expected_yield_kg_per_acre_min ?? null,
  expectedYieldKgPerAcreMax: d.expected_yield_kg_per_acre_max ?? null,
  waterRequirementsMm: d.water_requirements_mm ?? null,
  criticalWaterStages: d.critical_water_stages ?? null,
  source: d.source ?? null,
  isActive: d.is_active ?? true,
  createdAt: d.created_at,
  updatedAt: d.updated_at,
});

const mapInput = (d: any): InputRequirement => ({
  id: d.id,
  cropPlanId: d.crop_plan_id,
  category: d.category,
  name: d.name,
  brand: d.brand ?? null,
  quantityRequired: d.quantity_required,
  unit: d.unit,
  isCertified: d.is_certified ?? null,
  certificationNumber: d.certification_number ?? null,
  qrCodeVerified: d.qr_code_verified ?? false,
  qrCodeData: d.qr_code_data ?? null,
  qrVerifiedAt: d.qr_verified_at ?? null,
  quantityPerAcre: d.quantity_per_acre ?? null,
  applicationStage: d.application_stage ?? null,
  applicationDate: d.application_date ?? null,
  applicationMethod: d.application_method ?? null,
  unitPrice: d.unit_price ?? null,
  totalEstimatedCost: d.total_estimated_cost ?? null,
  actualCost: d.actual_cost ?? null,
  procurementStatus: d.procurement_status ?? 'planned',
  supplierName: d.supplier_name ?? null,
  purchaseDate: d.purchase_date ?? null,
  purchaseLocation: d.purchase_location ?? null,
  quantityUsed: d.quantity_used ?? null,
  quantityRemaining: d.quantity_remaining ?? null,
  notes: d.notes ?? null,
  createdAt: d.created_at,
  updatedAt: d.updated_at,
});

const mapIrrigation = (d: any): IrrigationSchedule => ({
  id: d.id,
  cropPlanId: d.crop_plan_id,
  method: d.method,
  scheduledDate: d.scheduled_date,
  scheduledDurationMinutes: d.scheduled_duration_minutes ?? null,
  waterAmountLiters: d.water_amount_liters ?? null,
  waterAmountMm: d.water_amount_mm ?? null,
  status: d.status,
  actualDate: d.actual_date ?? null,
  actualDurationMinutes: d.actual_duration_minutes ?? null,
  actualWaterUsedLiters: d.actual_water_used_liters ?? null,
  soilMoistureBefore: d.soil_moisture_before ?? null,
  soilMoistureAfter: d.soil_moisture_after ?? null,
  rainfallMmLast24h: d.rainfall_mm_last_24h ?? null,
  temperatureCelsius: d.temperature_celsius ?? null,
  evapotranspirationMm: d.evapotranspiration_mm ?? null,
  isDeficitIrrigation: d.is_deficit_irrigation ?? false,
  deficitPercentage: d.deficit_percentage ?? null,
  growthStage: d.growth_stage ?? null,
  notes: d.notes ?? null,
  createdAt: d.created_at,
  updatedAt: d.updated_at,
});

const mapAlert = (d: any): CropPlanAlert => ({
  id: d.id,
  farmerId: d.farmer_id,
  cropPlanId: d.crop_plan_id ?? null,
  activityId: d.activity_id ?? null,
  alertType: d.alert_type,
  title: d.title,
  message: d.message,
  severity: d.severity,
  data: d.data ?? null,
  channels: d.channels ?? [],
  scheduledFor: d.scheduled_for ?? null,
  sentAt: d.sent_at ?? null,
  readAt: d.read_at ?? null,
  dismissedAt: d.dismissed_at ?? null,
  createdAt: d.created_at,
});

const mapDashboard = (d: any): CropPlanningDashboard => ({
  farmerId: d.farmer_id,
  activePlansCount: d.active_plans_count ?? 0,
  draftPlansCount: d.draft_plans_count ?? 0,
  completedPlansCount: d.completed_plans_count ?? 0,
  totalPlannedAcreage: d.total_planned_acreage ?? 0,
  activitiesToday: d.activities_today ?? 0,
  activitiesOverdue: d.activities_overdue ?? 0,
  activitiesThisWeek: d.activities_this_week ?? 0,
  upcomingActivities: (d.upcoming_activities || []).map(mapUpcomingActivity),
  alertsUnread: d.alerts_unread ?? 0,
  recentAlerts: (d.recent_alerts || []).map(mapAlert),
});

const mapStatistics = (d: any): CropPlanStatistics => ({
  planId: d.plan_id,
  daysSincePlanting: d.days_since_planting ?? null,
  daysToHarvest: d.days_to_harvest ?? null,
  activitiesTotal: d.activities_total ?? 0,
  activitiesCompleted: d.activities_completed ?? 0,
  activitiesPending: d.activities_pending ?? 0,
  activitiesOverdue: d.activities_overdue ?? 0,
  completionPercentage: d.completion_percentage ?? 0,
  estimatedCost: d.estimated_cost ?? null,
  actualCost: d.actual_cost ?? null,
  costVariance: d.cost_variance ?? null,
  inputsProcuredPercentage: d.inputs_procured_percentage ?? null,
});

// =============================================================================
// Store Type
// =============================================================================

type CropPlanningState = {
  // Data
  dashboard: CropPlanningDashboard | null;
  plans: CropPlanSummary[];
  selectedPlan: CropPlan | null;
  templates: CropCalendarTemplate[];
  activities: PlannedActivity[];
  upcomingActivities: UpcomingActivity[];
  inputs: InputRequirement[];
  irrigationSchedules: IrrigationSchedule[];
  alerts: CropPlanAlert[];
  unreadAlertCount: number;
  statistics: CropPlanStatistics | null;
  createPlanDraft: Partial<CropPlanCreateData> | null;
  isLoading: boolean;
  error: string | null;

  // Dashboard
  fetchDashboard: (farmerId: string) => Promise<void>;

  // Templates
  fetchTemplates: (tenantId: string, params?: { cropName?: string; region?: string; season?: string; page?: number; pageSize?: number }) => Promise<void>;

  // Plans
  fetchPlans: (params?: { farmerId?: string; farmId?: string; status?: string; season?: string; year?: number; page?: number; pageSize?: number }) => Promise<void>;
  createPlan: () => Promise<CropPlan>;
  fetchPlan: (planId: string) => Promise<void>;
  updatePlan: (planId: string, data: Record<string, any>) => Promise<void>;
  deletePlan: (planId: string) => Promise<void>;
  activatePlan: (planId: string, data?: { actual_planting_date?: string; actual_planted_acreage?: number }) => Promise<void>;
  advanceStage: (planId: string, data: { new_stage: string; notes?: string }) => Promise<void>;
  completePlan: (planId: string, data: { actual_harvest_date: string; actual_yield_kg: number; notes?: string }) => Promise<void>;
  fetchStatistics: (planId: string) => Promise<void>;

  // Activities
  fetchActivities: (planId: string, params?: { status?: string; fromDate?: string; toDate?: string; page?: number; pageSize?: number }) => Promise<void>;
  completeActivity: (activityId: string, data: ActivityCompletionData) => Promise<void>;
  skipActivity: (activityId: string, reason: string) => Promise<void>;
  fetchUpcomingActivities: (farmerId: string, daysAhead?: number) => Promise<void>;

  // Inputs
  fetchInputs: (planId: string) => Promise<void>;
  createInput: (planId: string, data: Record<string, any>) => Promise<void>;
  updateInput: (inputId: string, data: Record<string, any>) => Promise<void>;

  // Irrigation
  fetchIrrigation: (planId: string) => Promise<void>;
  createIrrigation: (planId: string, data: Record<string, any>) => Promise<void>;
  generateIrrigation: (planId: string, data: IrrigationGenerateData) => Promise<void>;
  completeIrrigation: (scheduleId: string, data: IrrigationCompletionData) => Promise<void>;

  // Alerts
  fetchAlerts: (farmerId: string) => Promise<void>;
  markAlertRead: (alertId: string) => Promise<void>;
  dismissAlert: (alertId: string) => Promise<void>;

  // Draft management
  updateCreateDraft: (data: Partial<CropPlanCreateData>) => void;
  clearCreateDraft: () => void;

  clearError: () => void;
};

// =============================================================================
// Store
// =============================================================================

export const useCropPlanningStore = create<CropPlanningState>()(
  persist(
    (set, get) => ({
      // Initial state
      dashboard: null,
      plans: [],
      selectedPlan: null,
      templates: [],
      activities: [],
      upcomingActivities: [],
      inputs: [],
      irrigationSchedules: [],
      alerts: [],
      unreadAlertCount: 0,
      statistics: null,
      createPlanDraft: null,
      isLoading: false,
      error: null,

      // -----------------------------------------------------------------------
      // Dashboard
      // -----------------------------------------------------------------------

      fetchDashboard: async (farmerId: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.getDashboard(farmerId);
          set({ dashboard: mapDashboard(response), isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch dashboard', isLoading: false });
          throw error;
        }
      },

      // -----------------------------------------------------------------------
      // Templates
      // -----------------------------------------------------------------------

      fetchTemplates: async (tenantId: string, params?) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.listTemplates(tenantId, params);
          const templates = (response.items || []).map(mapTemplate);
          set({ templates, isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch templates', isLoading: false });
          throw error;
        }
      },

      // -----------------------------------------------------------------------
      // Plans
      // -----------------------------------------------------------------------

      fetchPlans: async (params?) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.listPlans(params);
          const plans = (response.items || []).map(mapPlanSummary);
          set({ plans, isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch plans', isLoading: false });
          throw error;
        }
      },

      createPlan: async () => {
        const { createPlanDraft } = get();
        if (!createPlanDraft) throw new Error('No draft');
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.createPlan({
            farmer_id: createPlanDraft.farmerId!,
            farm_id: createPlanDraft.farmId!,
            template_id: createPlanDraft.templateId || null,
            name: createPlanDraft.name!,
            crop_name: createPlanDraft.cropName!,
            variety: createPlanDraft.variety || null,
            season: createPlanDraft.season!,
            year: createPlanDraft.year!,
            planned_planting_date: createPlanDraft.plannedPlantingDate!,
            planned_acreage: createPlanDraft.plannedAcreage!,
            expected_harvest_date: createPlanDraft.expectedHarvestDate || null,
            notes: createPlanDraft.notes || null,
            generate_activities: createPlanDraft.generateActivities ?? true,
          });
          const plan = mapPlan(response);
          set({ selectedPlan: plan, createPlanDraft: null, isLoading: false });
          return plan;
        } catch (error: any) {
          set({ error: error.message || 'Failed to create plan', isLoading: false });
          throw error;
        }
      },

      fetchPlan: async (planId: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.getPlan(planId);
          set({ selectedPlan: mapPlan(response), isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch plan', isLoading: false });
          throw error;
        }
      },

      updatePlan: async (planId: string, data: Record<string, any>) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.updatePlan(planId, data);
          set({ selectedPlan: mapPlan(response), isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to update plan', isLoading: false });
          throw error;
        }
      },

      deletePlan: async (planId: string) => {
        set({ isLoading: true, error: null });
        try {
          await cropPlanningApi.deletePlan(planId);
          set((state) => ({
            plans: state.plans.filter((p) => p.id !== planId),
            selectedPlan: state.selectedPlan?.id === planId ? null : state.selectedPlan,
            isLoading: false,
          }));
        } catch (error: any) {
          set({ error: error.message || 'Failed to delete plan', isLoading: false });
          throw error;
        }
      },

      activatePlan: async (planId: string, data?) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.activatePlan(planId, data);
          set({ selectedPlan: mapPlan(response), isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to activate plan', isLoading: false });
          throw error;
        }
      },

      advanceStage: async (planId: string, data: { new_stage: string; notes?: string }) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.advanceStage(planId, data);
          set({ selectedPlan: mapPlan(response), isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to advance stage', isLoading: false });
          throw error;
        }
      },

      completePlan: async (planId: string, data: { actual_harvest_date: string; actual_yield_kg: number; notes?: string }) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.completePlan(planId, data);
          set({ selectedPlan: mapPlan(response), isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to complete plan', isLoading: false });
          throw error;
        }
      },

      fetchStatistics: async (planId: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.getPlanStatistics(planId);
          set({ statistics: mapStatistics(response), isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch statistics', isLoading: false });
          throw error;
        }
      },

      // -----------------------------------------------------------------------
      // Activities
      // -----------------------------------------------------------------------

      fetchActivities: async (planId: string, params?) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.listActivities(planId, params);
          const activities = (response.items || []).map(mapActivity);
          set({ activities, isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch activities', isLoading: false });
          throw error;
        }
      },

      completeActivity: async (activityId: string, data: ActivityCompletionData) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.completeActivity(activityId, data);
          const updated = mapActivity(response);
          set((state) => ({
            activities: state.activities.map((a) => (a.id === activityId ? updated : a)),
            isLoading: false,
          }));
        } catch (error: any) {
          set({ error: error.message || 'Failed to complete activity', isLoading: false });
          throw error;
        }
      },

      skipActivity: async (activityId: string, reason: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.skipActivity(activityId, reason);
          const updated = mapActivity(response);
          set((state) => ({
            activities: state.activities.map((a) => (a.id === activityId ? updated : a)),
            isLoading: false,
          }));
        } catch (error: any) {
          set({ error: error.message || 'Failed to skip activity', isLoading: false });
          throw error;
        }
      },

      fetchUpcomingActivities: async (farmerId: string, daysAhead: number = 7) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.getUpcomingActivities(farmerId, daysAhead);
          const upcomingActivities = (response.items || []).map(mapUpcomingActivity);
          set({ upcomingActivities, isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch upcoming activities', isLoading: false });
          throw error;
        }
      },

      // -----------------------------------------------------------------------
      // Inputs
      // -----------------------------------------------------------------------

      fetchInputs: async (planId: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.listInputs(planId);
          const inputs = (response.items || []).map(mapInput);
          set({ inputs, isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch inputs', isLoading: false });
          throw error;
        }
      },

      createInput: async (planId: string, data: Record<string, any>) => {
        set({ isLoading: true, error: null });
        try {
          await cropPlanningApi.createInput(planId, data);
          await get().fetchInputs(planId);
          set({ isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to create input', isLoading: false });
          throw error;
        }
      },

      updateInput: async (inputId: string, data: Record<string, any>) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.updateInput(inputId, data);
          const updated = mapInput(response);
          set((state) => ({
            inputs: state.inputs.map((i) => (i.id === inputId ? updated : i)),
            isLoading: false,
          }));
        } catch (error: any) {
          set({ error: error.message || 'Failed to update input', isLoading: false });
          throw error;
        }
      },

      // -----------------------------------------------------------------------
      // Irrigation
      // -----------------------------------------------------------------------

      fetchIrrigation: async (planId: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.listIrrigation(planId);
          const irrigationSchedules = (response.items || []).map(mapIrrigation);
          set({ irrigationSchedules, isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch irrigation', isLoading: false });
          throw error;
        }
      },

      createIrrigation: async (planId: string, data: Record<string, any>) => {
        set({ isLoading: true, error: null });
        try {
          await cropPlanningApi.createIrrigation(planId, data);
          await get().fetchIrrigation(planId);
          set({ isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to create irrigation schedule', isLoading: false });
          throw error;
        }
      },

      generateIrrigation: async (planId: string, data: IrrigationGenerateData) => {
        set({ isLoading: true, error: null });
        try {
          await cropPlanningApi.generateIrrigation(planId, {
            start_date: data.startDate,
            end_date: data.endDate,
            method: data.method,
            frequency_days: data.frequencyDays,
            water_amount_per_event_liters: data.waterAmountPerEventLiters,
            consider_rainfall: data.considerRainfall,
          });
          await get().fetchIrrigation(planId);
          set({ isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to generate irrigation', isLoading: false });
          throw error;
        }
      },

      completeIrrigation: async (scheduleId: string, data: IrrigationCompletionData) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.completeIrrigation(scheduleId, {
            actual_duration_minutes: data.actualDurationMinutes,
            actual_water_used_liters: data.actualWaterUsedLiters,
            soil_moisture_before: data.soilMoistureBefore,
            soil_moisture_after: data.soilMoistureAfter,
            notes: data.notes,
            actual_date: data.actualDate,
          });
          const updated = mapIrrigation(response);
          set((state) => ({
            irrigationSchedules: state.irrigationSchedules.map((i) => (i.id === scheduleId ? updated : i)),
            isLoading: false,
          }));
        } catch (error: any) {
          set({ error: error.message || 'Failed to complete irrigation', isLoading: false });
          throw error;
        }
      },

      // -----------------------------------------------------------------------
      // Alerts
      // -----------------------------------------------------------------------

      fetchAlerts: async (farmerId: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await cropPlanningApi.listAlerts(farmerId);
          const alerts = (response.items || []).map(mapAlert);
          set({ alerts, unreadAlertCount: response.unread_count || 0, isLoading: false });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch alerts', isLoading: false });
          throw error;
        }
      },

      markAlertRead: async (alertId: string) => {
        try {
          await cropPlanningApi.markAlertRead(alertId);
          set((state) => ({
            alerts: state.alerts.map((a) =>
              a.id === alertId ? { ...a, readAt: new Date().toISOString() } : a
            ),
            unreadAlertCount: Math.max(0, state.unreadAlertCount - 1),
          }));
        } catch (error: any) {
          set({ error: error.message || 'Failed to mark alert read' });
        }
      },

      dismissAlert: async (alertId: string) => {
        try {
          await cropPlanningApi.dismissAlert(alertId);
          set((state) => ({
            alerts: state.alerts.filter((a) => a.id !== alertId),
            unreadAlertCount: Math.max(0, state.unreadAlertCount - 1),
          }));
        } catch (error: any) {
          set({ error: error.message || 'Failed to dismiss alert' });
        }
      },

      // -----------------------------------------------------------------------
      // Draft management
      // -----------------------------------------------------------------------

      updateCreateDraft: (data: Partial<CropPlanCreateData>) => {
        const { createPlanDraft } = get();
        set({ createPlanDraft: { ...createPlanDraft, ...data } });
      },

      clearCreateDraft: () => {
        set({ createPlanDraft: null });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'crop-planning-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        plans: state.plans,
        createPlanDraft: state.createPlanDraft,
        unreadAlertCount: state.unreadAlertCount,
      }),
    }
  )
);
