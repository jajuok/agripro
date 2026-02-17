"""Crop Planning Schemas (Phase 3.1)."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class Season(str, Enum):
    """Growing seasons in Kenya."""

    LONG_RAINS = "long_rains"
    SHORT_RAINS = "short_rains"
    IRRIGATED = "irrigated"
    DRY_SEASON = "dry_season"


class CropPlanStatus(str, Enum):
    """Crop plan lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ActivityStatus(str, Enum):
    """Planned activity status."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    OVERDUE = "overdue"


class ActivityType(str, Enum):
    """Types of farming activities."""

    LAND_PREPARATION = "land_preparation"
    PLANTING = "planting"
    FERTILIZER_APPLICATION = "fertilizer_application"
    PESTICIDE_APPLICATION = "pesticide_application"
    WEEDING = "weeding"
    IRRIGATION = "irrigation"
    PRUNING = "pruning"
    THINNING = "thinning"
    STAKING = "staking"
    HARVESTING = "harvesting"
    POST_HARVEST = "post_harvest"
    SOIL_TESTING = "soil_testing"
    SCOUTING = "scouting"
    OTHER = "other"


class InputCategory(str, Enum):
    """Categories of farm inputs."""

    SEED = "seed"
    FERTILIZER = "fertilizer"
    PESTICIDE = "pesticide"
    HERBICIDE = "herbicide"
    FUNGICIDE = "fungicide"
    GROWTH_REGULATOR = "growth_regulator"
    OTHER = "other"


class ProcurementStatus(str, Enum):
    """Input procurement status."""

    PLANNED = "planned"
    ORDERED = "ordered"
    RECEIVED = "received"
    APPLIED = "applied"


class IrrigationMethod(str, Enum):
    """Irrigation methods."""

    DRIP = "drip"
    SPRINKLER = "sprinkler"
    FURROW = "furrow"
    FLOOD = "flood"
    MANUAL = "manual"
    PIVOT = "pivot"
    SUBSURFACE = "subsurface"


class IrrigationStatus(str, Enum):
    """Irrigation schedule status."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class AlertType(str, Enum):
    """Types of crop planning alerts."""

    ACTIVITY_REMINDER = "activity_reminder"
    ACTIVITY_OVERDUE = "activity_overdue"
    WEATHER_WARNING = "weather_warning"
    PLANTING_WINDOW = "planting_window"
    IRRIGATION_REMINDER = "irrigation_reminder"
    INPUT_REMINDER = "input_reminder"
    STAGE_TRANSITION = "stage_transition"
    HARVEST_REMINDER = "harvest_reminder"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# =============================================================================
# Growth Stage Schema
# =============================================================================


class GrowthStageActivity(BaseModel):
    """Activity definition within a growth stage."""

    activity_type: ActivityType
    title: str
    description: str | None = None
    day_offset: int  # Days from stage start
    duration_hours: float | None = None
    is_weather_dependent: bool = False
    weather_conditions: dict | None = None


class GrowthStage(BaseModel):
    """Growth stage definition in a crop calendar template."""

    name: str
    start_day: int  # Days from planting
    end_day: int
    description: str | None = None
    activities: list[GrowthStageActivity] = []
    water_requirement_mm_per_day: float | None = None
    critical_for_yield: bool = False


# =============================================================================
# Crop Calendar Template Schemas
# =============================================================================


class CropCalendarTemplateBase(BaseModel):
    """Base template schema."""

    crop_name: str = Field(..., min_length=1, max_length=100)
    variety: str | None = None
    region_type: str = Field(..., max_length=50)
    region_value: str | None = None
    season: Season
    recommended_planting_start_month: int = Field(..., ge=1, le=12)
    recommended_planting_end_month: int = Field(..., ge=1, le=12)
    total_days_to_harvest: int = Field(..., gt=0)


class CropCalendarTemplateCreate(CropCalendarTemplateBase):
    """Create template schema."""

    tenant_id: UUID
    growth_stages: list[GrowthStage] | None = None
    seed_rate_kg_per_acre: float | None = None
    fertilizer_requirements: dict | None = None
    expected_yield_kg_per_acre_min: float | None = None
    expected_yield_kg_per_acre_max: float | None = None
    water_requirements_mm: float | None = None
    critical_water_stages: list[str] | None = None
    source: str | None = None
    source_url: str | None = None


class CropCalendarTemplateUpdate(BaseModel):
    """Update template schema."""

    crop_name: str | None = None
    variety: str | None = None
    region_type: str | None = None
    region_value: str | None = None
    season: Season | None = None
    recommended_planting_start_month: int | None = Field(None, ge=1, le=12)
    recommended_planting_end_month: int | None = Field(None, ge=1, le=12)
    total_days_to_harvest: int | None = None
    growth_stages: list[GrowthStage] | None = None
    seed_rate_kg_per_acre: float | None = None
    fertilizer_requirements: dict | None = None
    expected_yield_kg_per_acre_min: float | None = None
    expected_yield_kg_per_acre_max: float | None = None
    water_requirements_mm: float | None = None
    source: str | None = None
    is_active: bool | None = None


class CropCalendarTemplateResponse(CropCalendarTemplateBase):
    """Template response schema."""

    id: UUID
    tenant_id: UUID
    growth_stages: list[GrowthStage] | None
    seed_rate_kg_per_acre: float | None
    fertilizer_requirements: dict | None
    expected_yield_kg_per_acre_min: float | None
    expected_yield_kg_per_acre_max: float | None
    water_requirements_mm: float | None
    critical_water_stages: list[str] | None
    source: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CropCalendarTemplateListResponse(BaseModel):
    """Paginated template list."""

    items: list[CropCalendarTemplateResponse]
    total: int
    page: int
    page_size: int


class TemplateRecommendation(BaseModel):
    """Template recommendation based on farm and timing."""

    template: CropCalendarTemplateResponse
    match_score: float
    match_reasons: list[str]
    warnings: list[str] | None = None


# =============================================================================
# Crop Plan Schemas
# =============================================================================


class CropPlanBase(BaseModel):
    """Base crop plan schema."""

    name: str = Field(..., min_length=1, max_length=200)
    crop_name: str = Field(..., min_length=1, max_length=100)
    variety: str | None = None
    season: Season
    year: int = Field(..., ge=2020, le=2100)
    planned_planting_date: datetime
    planned_acreage: float = Field(..., gt=0)


class CropPlanCreate(CropPlanBase):
    """Create crop plan schema."""

    farmer_id: UUID
    farm_id: UUID
    template_id: UUID | None = None
    expected_harvest_date: datetime | None = None
    expected_yield_kg: float | None = None
    notes: str | None = None
    # Auto-generate activities from template
    generate_activities: bool = True


class CropPlanUpdate(BaseModel):
    """Update crop plan schema."""

    name: str | None = None
    variety: str | None = None
    planned_planting_date: datetime | None = None
    expected_harvest_date: datetime | None = None
    actual_planting_date: datetime | None = None
    actual_harvest_date: datetime | None = None
    planned_acreage: float | None = None
    actual_planted_acreage: float | None = None
    expected_yield_kg: float | None = None
    actual_yield_kg: float | None = None
    notes: str | None = None
    status: CropPlanStatus | None = None


class CropPlanActivate(BaseModel):
    """Activate crop plan schema."""

    actual_planting_date: datetime | None = None
    actual_planted_acreage: float | None = None


class CropPlanAdvanceStage(BaseModel):
    """Advance to next growth stage."""

    new_stage: str
    notes: str | None = None


class CropPlanComplete(BaseModel):
    """Complete crop plan schema."""

    actual_harvest_date: datetime
    actual_yield_kg: float
    notes: str | None = None


class CropPlanSummary(BaseModel):
    """Crop plan summary for list views."""

    id: UUID
    name: str
    crop_name: str
    variety: str | None
    season: str
    year: int
    status: str
    farm_id: UUID
    farm_name: str
    planned_planting_date: datetime
    planned_acreage: float
    current_growth_stage: str | None
    activities_total: int
    activities_completed: int
    activities_overdue: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CropPlanResponse(CropPlanBase):
    """Full crop plan response."""

    id: UUID
    farmer_id: UUID
    farm_id: UUID
    template_id: UUID | None
    status: str
    expected_harvest_date: datetime | None
    actual_planting_date: datetime | None
    actual_harvest_date: datetime | None
    optimal_planting_window_start: datetime | None
    optimal_planting_window_end: datetime | None
    actual_planted_acreage: float | None
    expected_yield_kg: float | None
    actual_yield_kg: float | None
    current_growth_stage: str | None
    current_growth_stage_start: datetime | None
    growth_stage_history: list[dict] | None
    estimated_total_cost: float | None
    actual_total_cost: float | None
    weather_data_snapshot: dict | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    # Computed fields
    activities_total: int | None = None
    activities_completed: int | None = None
    inputs_total_cost: float | None = None

    model_config = {"from_attributes": True}


class CropPlanListResponse(BaseModel):
    """Paginated crop plan list."""

    items: list[CropPlanSummary]
    total: int
    page: int
    page_size: int


# =============================================================================
# Planned Activity Schemas
# =============================================================================


class PlannedActivityBase(BaseModel):
    """Base activity schema."""

    activity_type: ActivityType
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    growth_stage: str | None = None
    scheduled_date: datetime
    scheduled_end_date: datetime | None = None
    duration_hours: float | None = None


class PlannedActivityCreate(PlannedActivityBase):
    """Create activity schema."""

    crop_plan_id: UUID
    earliest_date: datetime | None = None
    latest_date: datetime | None = None
    is_weather_dependent: bool = False
    weather_conditions_required: dict | None = None
    estimated_cost: float | None = None
    priority: int = 5
    reminder_days_before: int = 1


class PlannedActivityUpdate(BaseModel):
    """Update activity schema."""

    title: str | None = None
    description: str | None = None
    scheduled_date: datetime | None = None
    scheduled_end_date: datetime | None = None
    duration_hours: float | None = None
    earliest_date: datetime | None = None
    latest_date: datetime | None = None
    is_weather_dependent: bool | None = None
    weather_conditions_required: dict | None = None
    estimated_cost: float | None = None
    priority: int | None = None
    status: ActivityStatus | None = None


class ActivityCompletion(BaseModel):
    """Complete an activity."""

    completion_notes: str | None = None
    completion_photos: list[str] | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    inputs_used: list[dict] | None = None
    actual_cost: float | None = None
    actual_date: datetime | None = None


class ActivitySkip(BaseModel):
    """Skip an activity."""

    reason: str


class PlannedActivityResponse(PlannedActivityBase):
    """Activity response schema."""

    id: UUID
    crop_plan_id: UUID
    status: str
    earliest_date: datetime | None
    latest_date: datetime | None
    is_weather_dependent: bool
    weather_conditions_required: dict | None
    completed_at: datetime | None
    actual_date: datetime | None
    completion_notes: str | None
    completion_photos: list[str] | None
    gps_latitude: float | None
    gps_longitude: float | None
    inputs_used: list[dict] | None
    estimated_cost: float | None
    actual_cost: float | None
    priority: int
    reminder_days_before: int
    alert_sent: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlannedActivityListResponse(BaseModel):
    """Paginated activity list."""

    items: list[PlannedActivityResponse]
    total: int
    page: int
    page_size: int


class UpcomingActivity(BaseModel):
    """Upcoming activity with plan context."""

    activity: PlannedActivityResponse
    plan_id: UUID
    plan_name: str
    crop_name: str
    farm_name: str
    days_until: int
    is_overdue: bool


class UpcomingActivitiesResponse(BaseModel):
    """List of upcoming activities."""

    items: list[UpcomingActivity]
    total: int


# =============================================================================
# Input Requirement Schemas
# =============================================================================


class InputRequirementBase(BaseModel):
    """Base input requirement schema."""

    category: InputCategory
    name: str = Field(..., min_length=1, max_length=200)
    brand: str | None = None
    quantity_required: float = Field(..., gt=0)
    unit: str = Field(..., max_length=50)


class InputRequirementCreate(InputRequirementBase):
    """Create input requirement schema."""

    crop_plan_id: UUID
    is_certified: bool | None = None
    certification_number: str | None = None
    quantity_per_acre: float | None = None
    application_stage: str | None = None
    application_date: datetime | None = None
    application_method: str | None = None
    unit_price: float | None = None
    supplier_name: str | None = None
    notes: str | None = None


class InputRequirementUpdate(BaseModel):
    """Update input requirement schema."""

    name: str | None = None
    brand: str | None = None
    quantity_required: float | None = None
    unit: str | None = None
    is_certified: bool | None = None
    certification_number: str | None = None
    quantity_per_acre: float | None = None
    application_stage: str | None = None
    application_date: datetime | None = None
    application_method: str | None = None
    unit_price: float | None = None
    supplier_name: str | None = None
    procurement_status: ProcurementStatus | None = None
    purchase_date: datetime | None = None
    purchase_location: str | None = None
    quantity_used: float | None = None
    actual_cost: float | None = None
    notes: str | None = None


class QrCodeVerification(BaseModel):
    """QR code verification data."""

    qr_code_data: dict


class QrCodeVerificationResult(BaseModel):
    """QR code verification result."""

    verified: bool
    product_name: str | None = None
    manufacturer: str | None = None
    batch_number: str | None = None
    expiry_date: datetime | None = None
    certification_status: str | None = None
    warnings: list[str] | None = None


class InputRequirementResponse(InputRequirementBase):
    """Input requirement response schema."""

    id: UUID
    crop_plan_id: UUID
    is_certified: bool | None
    certification_number: str | None
    qr_code_verified: bool
    qr_code_data: dict | None
    qr_verified_at: datetime | None
    quantity_per_acre: float | None
    application_stage: str | None
    application_date: datetime | None
    application_method: str | None
    unit_price: float | None
    total_estimated_cost: float | None
    actual_cost: float | None
    procurement_status: str
    supplier_name: str | None
    purchase_date: datetime | None
    purchase_location: str | None
    quantity_used: float | None
    quantity_remaining: float | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InputRequirementListResponse(BaseModel):
    """Paginated input list."""

    items: list[InputRequirementResponse]
    total: int
    total_estimated_cost: float | None
    total_actual_cost: float | None


class InputCalculation(BaseModel):
    """Calculated input requirements based on crop and acreage."""

    crop_name: str
    variety: str | None
    acreage: float
    recommendations: list[InputRequirementBase]
    total_estimated_cost: float | None
    source: str | None


# =============================================================================
# Irrigation Schedule Schemas
# =============================================================================


class IrrigationScheduleBase(BaseModel):
    """Base irrigation schedule schema."""

    method: IrrigationMethod
    scheduled_date: datetime
    scheduled_duration_minutes: int | None = None
    water_amount_liters: float | None = None
    water_amount_mm: float | None = None


class IrrigationScheduleCreate(IrrigationScheduleBase):
    """Create irrigation schedule schema."""

    crop_plan_id: UUID
    growth_stage: str | None = None
    is_deficit_irrigation: bool = False
    deficit_percentage: float | None = None
    notes: str | None = None


class IrrigationScheduleUpdate(BaseModel):
    """Update irrigation schedule schema."""

    scheduled_date: datetime | None = None
    scheduled_duration_minutes: int | None = None
    water_amount_liters: float | None = None
    water_amount_mm: float | None = None
    method: IrrigationMethod | None = None
    status: IrrigationStatus | None = None
    notes: str | None = None


class IrrigationCompletion(BaseModel):
    """Complete an irrigation event."""

    actual_duration_minutes: int | None = None
    actual_water_used_liters: float | None = None
    soil_moisture_before: float | None = None
    soil_moisture_after: float | None = None
    notes: str | None = None
    actual_date: datetime | None = None


class IrrigationScheduleResponse(IrrigationScheduleBase):
    """Irrigation schedule response schema."""

    id: UUID
    crop_plan_id: UUID
    status: str
    actual_date: datetime | None
    actual_duration_minutes: int | None
    actual_water_used_liters: float | None
    soil_moisture_before: float | None
    soil_moisture_after: float | None
    rainfall_mm_last_24h: float | None
    temperature_celsius: float | None
    evapotranspiration_mm: float | None
    is_deficit_irrigation: bool
    deficit_percentage: float | None
    growth_stage: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IrrigationScheduleListResponse(BaseModel):
    """Paginated irrigation schedule list."""

    items: list[IrrigationScheduleResponse]
    total: int
    total_water_planned_liters: float | None
    total_water_used_liters: float | None


class IrrigationGenerateRequest(BaseModel):
    """Request to auto-generate irrigation schedule."""

    start_date: datetime
    end_date: datetime
    method: IrrigationMethod
    frequency_days: int = 7
    water_amount_per_event_liters: float | None = None
    consider_rainfall: bool = True


class IrrigationRecommendation(BaseModel):
    """Irrigation recommendation based on weather and crop needs."""

    recommended_date: datetime
    recommended_amount_liters: float
    recommended_amount_mm: float
    growth_stage: str | None
    reasoning: str
    weather_forecast: dict | None
    soil_moisture_estimate: float | None


# =============================================================================
# Alert Schemas
# =============================================================================


class CropPlanAlertResponse(BaseModel):
    """Alert response schema."""

    id: UUID
    farmer_id: UUID
    crop_plan_id: UUID | None
    activity_id: UUID | None
    alert_type: str
    title: str
    message: str
    severity: str
    data: dict | None
    channels: list[str]
    scheduled_for: datetime | None
    sent_at: datetime | None
    read_at: datetime | None
    dismissed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CropPlanAlertListResponse(BaseModel):
    """Paginated alert list."""

    items: list[CropPlanAlertResponse]
    total: int
    unread_count: int


# =============================================================================
# Weather Schemas
# =============================================================================


class WeatherForecast(BaseModel):
    """Weather forecast data."""

    date: datetime
    temperature_min_celsius: float
    temperature_max_celsius: float
    precipitation_mm: float
    precipitation_probability: float
    humidity_percent: float
    wind_speed_kmh: float
    condition: str
    is_suitable_for_planting: bool | None = None
    is_suitable_for_spraying: bool | None = None


class WeatherForecastResponse(BaseModel):
    """Weather forecast response."""

    latitude: float
    longitude: float
    location_name: str | None
    forecasts: list[WeatherForecast]
    source: str
    fetched_at: datetime


class PlantingWindowRecommendation(BaseModel):
    """Recommended planting window based on weather."""

    crop_name: str
    optimal_start_date: datetime
    optimal_end_date: datetime
    confidence: float
    rainfall_expected_mm: float
    average_temperature_celsius: float
    reasoning: str
    warnings: list[str] | None = None


# =============================================================================
# Dashboard/Summary Schemas
# =============================================================================


class CropPlanningDashboard(BaseModel):
    """Dashboard summary for crop planning."""

    farmer_id: UUID
    active_plans_count: int
    draft_plans_count: int
    completed_plans_count: int
    total_planned_acreage: float
    activities_today: int
    activities_overdue: int
    activities_this_week: int
    upcoming_activities: list[UpcomingActivity]
    alerts_unread: int
    recent_alerts: list[CropPlanAlertResponse]


class CropPlanStatistics(BaseModel):
    """Statistics for a crop plan."""

    plan_id: UUID
    days_since_planting: int | None
    days_to_harvest: int | None
    activities_total: int
    activities_completed: int
    activities_pending: int
    activities_overdue: int
    completion_percentage: float
    estimated_cost: float | None
    actual_cost: float | None
    cost_variance: float | None
    inputs_procured_percentage: float | None
