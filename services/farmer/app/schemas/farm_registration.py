"""Farm registration workflow schemas."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class FarmRegistrationStep(str, Enum):
    """Farm registration workflow steps."""

    LOCATION = "location"
    BOUNDARY = "boundary"
    LAND_DETAILS = "land_details"
    DOCUMENTS = "documents"
    SOIL_WATER = "soil_water"
    ASSETS = "assets"
    CROP_HISTORY = "crop_history"
    REVIEW = "review"
    COMPLETE = "complete"


# Location step schemas
class LocationInput(BaseModel):
    """Input for location step."""

    name: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: float | None = Field(None, ge=0)
    address_description: str | None = None


class LocationUpdate(BaseModel):
    """Update location details."""

    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    altitude: float | None = Field(None, ge=0)
    county: str | None = None
    sub_county: str | None = None
    ward: str | None = None
    village: str | None = None
    address_description: str | None = None


# Boundary step schemas
class BoundaryInput(BaseModel):
    """Input for boundary step."""

    boundary_geojson: dict[str, Any] = Field(..., description="GeoJSON polygon of farm boundary")


# Land details step schemas
class LandDetailsInput(BaseModel):
    """Input for land details step."""

    total_acreage: float = Field(..., gt=0)
    cultivable_acreage: float | None = Field(None, gt=0)
    ownership_type: str = Field(..., description="owned, leased, communal, inherited")
    land_reference_number: str | None = None
    plot_id_source: str | None = Field(None, description="Source of plot ID (e.g., 'national_land_registry')")


# Soil and water step schemas
class SoilWaterInput(BaseModel):
    """Input for soil and water profile step."""

    soil_type: str | None = None
    soil_ph: float | None = Field(None, ge=0, le=14)
    water_source: str | None = None
    irrigation_type: str | None = None
    has_irrigation: bool = False
    annual_rainfall_mm: float | None = None


# Farm document schemas
class FarmDocumentCreate(BaseModel):
    """Create farm document."""

    document_type: str = Field(..., description="land_title, lease_agreement, survey_map, etc.")
    document_number: str | None = None
    file_url: str
    file_name: str
    file_size: int | None = None
    mime_type: str | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None


class FarmDocumentResponse(BaseModel):
    """Farm document response."""

    id: UUID
    farm_id: UUID
    document_type: str
    document_number: str | None
    file_url: str
    file_name: str
    is_verified: bool
    verification_status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# Farm asset schemas
class FarmAssetCreate(BaseModel):
    """Create farm asset."""

    asset_type: str = Field(..., description="equipment, infrastructure, vehicle, storage")
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    quantity: int = Field(1, ge=1)
    estimated_value: float | None = None
    acquisition_date: datetime | None = None
    condition: str | None = Field(None, description="excellent, good, fair, poor")


class FarmAssetResponse(BaseModel):
    """Farm asset response."""

    id: UUID
    farm_id: UUID
    asset_type: str
    name: str
    description: str | None
    quantity: int
    estimated_value: float | None
    condition: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# Crop record schemas
class CropRecordCreate(BaseModel):
    """Create crop record."""

    crop_name: str = Field(..., min_length=1, max_length=100)
    variety: str | None = None
    season: str = Field(..., description="long_rains, short_rains, irrigated")
    year: int = Field(..., ge=2000, le=2100)
    planted_acreage: float = Field(..., gt=0)
    expected_yield_kg: float | None = Field(None, ge=0)
    actual_yield_kg: float | None = Field(None, ge=0)
    planting_date: datetime | None = None
    harvest_date: datetime | None = None
    is_current: bool = False


class CropRecordUpdate(BaseModel):
    """Update crop record."""

    actual_yield_kg: float | None = Field(None, ge=0)
    harvest_date: datetime | None = None
    notes: str | None = None


class CropRecordResponse(BaseModel):
    """Crop record response."""

    id: UUID
    farm_id: UUID
    crop_name: str
    variety: str | None
    season: str
    year: int
    planted_acreage: float
    expected_yield_kg: float | None
    actual_yield_kg: float | None
    is_current: bool
    planting_date: datetime | None
    harvest_date: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# Soil test report schemas
class SoilTestReportCreate(BaseModel):
    """Create soil test report."""

    test_date: datetime
    tested_by: str | None = None
    lab_name: str | None = None
    ph_level: float | None = Field(None, ge=0, le=14)
    nitrogen_ppm: float | None = Field(None, ge=0)
    phosphorus_ppm: float | None = Field(None, ge=0)
    potassium_ppm: float | None = Field(None, ge=0)
    organic_matter_percent: float | None = Field(None, ge=0, le=100)
    texture: str | None = None
    recommendations: str | None = None
    report_file_url: str | None = None


class SoilTestReportResponse(BaseModel):
    """Soil test report response."""

    id: UUID
    farm_id: UUID
    test_date: datetime
    tested_by: str | None
    lab_name: str | None
    ph_level: float | None
    nitrogen_ppm: float | None
    phosphorus_ppm: float | None
    potassium_ppm: float | None
    organic_matter_percent: float | None
    texture: str | None
    recommendations: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# Field visit schemas
class FieldVisitCreate(BaseModel):
    """Create field visit."""

    visit_date: datetime
    visitor_id: UUID
    visitor_name: str
    purpose: str = Field(..., description="verification, inspection, extension, follow_up")
    findings: str | None = None
    recommendations: str | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    photos: list[str] | None = None


class FieldVisitResponse(BaseModel):
    """Field visit response."""

    id: UUID
    farm_id: UUID
    visit_date: datetime
    visitor_name: str
    purpose: str
    verification_status: str
    findings: str | None
    recommendations: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# Registration workflow schemas
class RegistrationStartInput(BaseModel):
    """Input to start farm registration."""

    farmer_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class FarmRegistrationStatus(BaseModel):
    """Current status of farm registration workflow."""

    farm_id: UUID
    farmer_id: UUID
    farm_name: str
    current_step: str
    registration_complete: bool
    progress_percentage: int

    # Step status
    steps: dict[str, dict[str, Any]]

    # Location info
    county: str | None
    sub_county: str | None
    ward: str | None

    # Calculated values
    boundary_area_acres: float | None
    boundary_validated: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime | None


class FarmRegistrationResponse(BaseModel):
    """Response for farm registration operations."""

    farm_id: UUID
    status: str
    message: str
    current_step: str
    next_step: str | None
