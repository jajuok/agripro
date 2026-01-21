"""GIS schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Any


class CoordinatesInput(BaseModel):
    """Input for coordinate-based operations."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")


class AdminLocation(BaseModel):
    """Administrative location information."""

    country: str = "Kenya"
    county: str | None = None
    sub_county: str | None = None
    ward: str | None = None
    is_valid: bool = True
    message: str | None = None


class GeoJSONInput(BaseModel):
    """GeoJSON polygon input."""

    geojson: dict[str, Any] = Field(..., description="GeoJSON geometry object")


class PolygonValidationResult(BaseModel):
    """Result of polygon validation."""

    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    vertex_count: int = 0
    is_closed: bool = False
    has_self_intersection: bool = False


class AreaCalculationResult(BaseModel):
    """Result of area calculation."""

    area_acres: float
    area_hectares: float
    area_square_meters: float
    perimeter_meters: float
    is_valid: bool = True
    message: str | None = None


class PointInBoundaryInput(BaseModel):
    """Input for point-in-boundary check."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    boundary: dict[str, Any] = Field(..., description="GeoJSON polygon boundary")


class PointInBoundaryResult(BaseModel):
    """Result of point-in-boundary check."""

    is_inside: bool
    distance_to_boundary_meters: float | None = None


class BoundaryPairInput(BaseModel):
    """Input for boundary overlap check."""

    boundary1: dict[str, Any]
    boundary2: dict[str, Any]


class OverlapResult(BaseModel):
    """Result of boundary overlap check."""

    has_overlap: bool
    overlap_area_acres: float = 0.0
    overlap_percentage: float = 0.0  # Percentage of boundary1 that overlaps


class SimplifyPolygonInput(BaseModel):
    """Input for polygon simplification."""

    geojson: dict[str, Any]
    tolerance: float = Field(default=0.0001, description="Simplification tolerance in degrees")


class SimplifiedPolygonResult(BaseModel):
    """Result of polygon simplification."""

    simplified_geojson: dict[str, Any]
    original_vertex_count: int
    simplified_vertex_count: int
    reduction_percentage: float
