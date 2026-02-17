"""Crop Planning Models (Phase 3.1)."""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import JSONBCompatible
from app.models.farmer import Base

if TYPE_CHECKING:
    from app.models.farmer import Farmer, FarmProfile


# =============================================================================
# Enums
# =============================================================================


class Season(str, Enum):
    """Growing seasons in Kenya."""

    LONG_RAINS = "long_rains"  # March-May
    SHORT_RAINS = "short_rains"  # October-December
    IRRIGATED = "irrigated"  # Year-round with irrigation
    DRY_SEASON = "dry_season"  # June-September


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
# Crop Calendar Template Model
# =============================================================================


class CropCalendarTemplate(Base):
    """Regional/crop-specific templates defining growth stages and timelines."""

    __tablename__ = "crop_calendar_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)

    # Crop identification
    crop_name: Mapped[str] = mapped_column(String(100), index=True)
    variety: Mapped[str | None] = mapped_column(String(100))

    # Regional targeting
    region_type: Mapped[str] = mapped_column(String(50))  # national, county, agro_ecological_zone
    region_value: Mapped[str | None] = mapped_column(String(100))  # e.g., "Nakuru", "Highland"

    # Season
    season: Mapped[str] = mapped_column(String(50))  # Season enum value

    # Planting window
    recommended_planting_start_month: Mapped[int] = mapped_column(Integer)  # 1-12
    recommended_planting_end_month: Mapped[int] = mapped_column(Integer)  # 1-12

    # Duration
    total_days_to_harvest: Mapped[int] = mapped_column(Integer)

    # Growth stages with activities
    # Format: [{"name": "Germination", "start_day": 0, "end_day": 14, "activities": [...]}]
    growth_stages: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Input requirements
    seed_rate_kg_per_acre: Mapped[float | None] = mapped_column(Float)
    fertilizer_requirements: Mapped[dict | None] = mapped_column(JSONBCompatible)
    # Format: {"basal": {"type": "DAP", "rate_kg_per_acre": 50}, "topdress": {...}}

    # Expected yield
    expected_yield_kg_per_acre_min: Mapped[float | None] = mapped_column(Float)
    expected_yield_kg_per_acre_max: Mapped[float | None] = mapped_column(Float)

    # Water requirements
    water_requirements_mm: Mapped[float | None] = mapped_column(Float)  # Total water needed
    critical_water_stages: Mapped[list | None] = mapped_column(JSONBCompatible)

    # Source and validation
    source: Mapped[str | None] = mapped_column(String(100))  # KALRO, Ministry of Agriculture, etc.
    source_url: Mapped[str | None] = mapped_column(String(500))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# =============================================================================
# Crop Plan Model
# =============================================================================


class CropPlan(Base):
    """Farmer's active crop plan for a specific farm/season."""

    __tablename__ = "crop_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE"), index=True
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farm_profiles.id", ondelete="CASCADE"), index=True
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_calendar_templates.id", ondelete="SET NULL")
    )

    # Plan identification
    name: Mapped[str] = mapped_column(String(200))

    # Crop details
    crop_name: Mapped[str] = mapped_column(String(100), index=True)
    variety: Mapped[str | None] = mapped_column(String(100))

    # Season and timing
    season: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer, index=True)

    # Key dates
    planned_planting_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expected_harvest_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_planting_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_harvest_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Optimal planting window from weather analysis
    optimal_planting_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    optimal_planting_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Area
    planned_acreage: Mapped[float] = mapped_column(Float)
    actual_planted_acreage: Mapped[float | None] = mapped_column(Float)

    # Yield
    expected_yield_kg: Mapped[float | None] = mapped_column(Float)
    actual_yield_kg: Mapped[float | None] = mapped_column(Float)

    # Growth stage tracking
    current_growth_stage: Mapped[str | None] = mapped_column(String(100))
    current_growth_stage_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    growth_stage_history: Mapped[list | None] = mapped_column(JSONBCompatible)
    # Format: [{"stage": "Germination", "started_at": "...", "ended_at": "..."}]

    # Status
    status: Mapped[str] = mapped_column(String(20), default=CropPlanStatus.DRAFT.value)

    # Cost tracking
    estimated_total_cost: Mapped[float | None] = mapped_column(Float)
    actual_total_cost: Mapped[float | None] = mapped_column(Float)

    # Weather snapshot at creation
    weather_data_snapshot: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", backref="crop_plans")
    farm: Mapped["FarmProfile"] = relationship("FarmProfile", backref="crop_plans")
    template: Mapped["CropCalendarTemplate | None"] = relationship(
        "CropCalendarTemplate", backref="plans"
    )
    activities: Mapped[list["PlannedActivity"]] = relationship(
        "PlannedActivity", back_populates="crop_plan", cascade="all, delete-orphan"
    )
    input_requirements: Mapped[list["InputRequirement"]] = relationship(
        "InputRequirement", back_populates="crop_plan", cascade="all, delete-orphan"
    )
    irrigation_schedules: Mapped[list["IrrigationSchedule"]] = relationship(
        "IrrigationSchedule", back_populates="crop_plan", cascade="all, delete-orphan"
    )


# =============================================================================
# Planned Activity Model
# =============================================================================


class PlannedActivity(Base):
    """Scheduled activities within a crop plan."""

    __tablename__ = "planned_activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_plans.id", ondelete="CASCADE"), index=True
    )

    # Activity identification
    activity_type: Mapped[str] = mapped_column(String(50))  # ActivityType enum value
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    # Growth stage context
    growth_stage: Mapped[str | None] = mapped_column(String(100))

    # Scheduling
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    scheduled_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_hours: Mapped[float | None] = mapped_column(Float)

    # Flexible timing window
    earliest_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latest_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Weather dependency
    is_weather_dependent: Mapped[bool] = mapped_column(Boolean, default=False)
    weather_conditions_required: Mapped[dict | None] = mapped_column(JSONBCompatible)
    # Format: {"no_rain_hours_before": 24, "min_temp_celsius": 15, "max_wind_kmh": 20}

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default=ActivityStatus.SCHEDULED.value)

    # Completion details
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_notes: Mapped[str | None] = mapped_column(Text)
    completion_photos: Mapped[list | None] = mapped_column(JSONBCompatible)  # List of photo URLs

    # GPS verification for field activities
    gps_latitude: Mapped[float | None] = mapped_column(Float)
    gps_longitude: Mapped[float | None] = mapped_column(Float)

    # Inputs used during activity
    inputs_used: Mapped[dict | None] = mapped_column(JSONBCompatible)
    # Format: [{"input_id": "...", "name": "...", "quantity": 50, "unit": "kg"}]

    # Cost tracking
    estimated_cost: Mapped[float | None] = mapped_column(Float)
    actual_cost: Mapped[float | None] = mapped_column(Float)

    # Priority and reminders
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1 = highest
    reminder_days_before: Mapped[int] = mapped_column(Integer, default=1)
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    crop_plan: Mapped["CropPlan"] = relationship("CropPlan", back_populates="activities")


# =============================================================================
# Input Requirement Model
# =============================================================================


class InputRequirement(Base):
    """Planned input needs (seeds, fertilizers, pesticides)."""

    __tablename__ = "input_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_plans.id", ondelete="CASCADE"), index=True
    )

    # Input identification
    category: Mapped[str] = mapped_column(String(50))  # InputCategory enum value
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str | None] = mapped_column(String(100))

    # Certification (for seeds)
    is_certified: Mapped[bool | None] = mapped_column(Boolean)
    certification_number: Mapped[str | None] = mapped_column(String(100))

    # QR code verification
    qr_code_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    qr_code_data: Mapped[dict | None] = mapped_column(JSONBCompatible)
    qr_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Quantity
    quantity_required: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))  # kg, liters, bags, etc.
    quantity_per_acre: Mapped[float | None] = mapped_column(Float)

    # Application details
    application_stage: Mapped[str | None] = mapped_column(String(100))  # Growth stage
    application_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    application_method: Mapped[str | None] = mapped_column(String(100))

    # Cost
    unit_price: Mapped[float | None] = mapped_column(Float)
    total_estimated_cost: Mapped[float | None] = mapped_column(Float)
    actual_cost: Mapped[float | None] = mapped_column(Float)

    # Procurement
    procurement_status: Mapped[str] = mapped_column(
        String(20), default=ProcurementStatus.PLANNED.value
    )
    supplier_name: Mapped[str | None] = mapped_column(String(200))
    purchase_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    purchase_location: Mapped[str | None] = mapped_column(String(200))

    # Usage tracking
    quantity_used: Mapped[float | None] = mapped_column(Float)
    quantity_remaining: Mapped[float | None] = mapped_column(Float)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    crop_plan: Mapped["CropPlan"] = relationship("CropPlan", back_populates="input_requirements")


# =============================================================================
# Irrigation Schedule Model
# =============================================================================


class IrrigationSchedule(Base):
    """Irrigation planning and tracking."""

    __tablename__ = "irrigation_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_plans.id", ondelete="CASCADE"), index=True
    )

    # Method
    method: Mapped[str] = mapped_column(String(50))  # IrrigationMethod enum value

    # Schedule
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    scheduled_duration_minutes: Mapped[int | None] = mapped_column(Integer)

    # Water amount
    water_amount_liters: Mapped[float | None] = mapped_column(Float)
    water_amount_mm: Mapped[float | None] = mapped_column(Float)  # Depth equivalent

    # Status
    status: Mapped[str] = mapped_column(String(20), default=IrrigationStatus.SCHEDULED.value)

    # Completion
    actual_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    actual_water_used_liters: Mapped[float | None] = mapped_column(Float)

    # Soil moisture readings
    soil_moisture_before: Mapped[float | None] = mapped_column(Float)  # Percentage
    soil_moisture_after: Mapped[float | None] = mapped_column(Float)

    # Weather context
    rainfall_mm_last_24h: Mapped[float | None] = mapped_column(Float)
    temperature_celsius: Mapped[float | None] = mapped_column(Float)
    evapotranspiration_mm: Mapped[float | None] = mapped_column(Float)

    # Deficit irrigation support
    is_deficit_irrigation: Mapped[bool] = mapped_column(Boolean, default=False)
    deficit_percentage: Mapped[float | None] = mapped_column(Float)

    # Growth stage context
    growth_stage: Mapped[str | None] = mapped_column(String(100))

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    crop_plan: Mapped["CropPlan"] = relationship("CropPlan", back_populates="irrigation_schedules")


# =============================================================================
# Crop Plan Alert Model
# =============================================================================


class CropPlanAlert(Base):
    """Alert tracking for notifications."""

    __tablename__ = "crop_plan_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE"), index=True
    )
    crop_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_plans.id", ondelete="CASCADE"), index=True
    )
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("planned_activities.id", ondelete="CASCADE")
    )

    # Alert type and content
    alert_type: Mapped[str] = mapped_column(String(50))  # AlertType enum value
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default=AlertSeverity.INFO.value)

    # Additional data
    data: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Delivery channels
    channels: Mapped[list] = mapped_column(JSONBCompatible, default=list)  # push, sms, in_app

    # Scheduling
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Status tracking
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", backref="crop_plan_alerts")
    crop_plan: Mapped["CropPlan | None"] = relationship("CropPlan", backref="alerts")
    activity: Mapped["PlannedActivity | None"] = relationship("PlannedActivity", backref="alerts")
