"""Farm profile schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FarmCreate(BaseModel):
    """Farm creation schema."""
    farmer_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    latitude: float | None = None
    longitude: float | None = None
    total_acreage: float | None = None
    cultivable_acreage: float | None = None
    ownership_type: str | None = None
    soil_type: str | None = None
    water_source: str | None = None
    irrigation_type: str | None = None


class FarmUpdate(BaseModel):
    """Farm update schema."""
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    total_acreage: float | None = None
    cultivable_acreage: float | None = None
    soil_type: str | None = None
    soil_ph: float | None = None
    water_source: str | None = None
    irrigation_type: str | None = None


class FarmResponse(BaseModel):
    """Farm response schema."""
    id: UUID
    farmer_id: UUID
    plot_id: str | None
    name: str
    latitude: float | None
    longitude: float | None
    total_acreage: float | None
    cultivable_acreage: float | None
    ownership_type: str | None
    soil_type: str | None
    water_source: str | None
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}
