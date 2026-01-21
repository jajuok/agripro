"""GIS schemas."""

from app.schemas.geo import (
    AdminLocation,
    AreaCalculationResult,
    BoundaryPairInput,
    CoordinatesInput,
    GeoJSONInput,
    OverlapResult,
    PointInBoundaryInput,
    PointInBoundaryResult,
    PolygonValidationResult,
    SimplifiedPolygonResult,
    SimplifyPolygonInput,
)

__all__ = [
    "AdminLocation",
    "AreaCalculationResult",
    "BoundaryPairInput",
    "CoordinatesInput",
    "GeoJSONInput",
    "OverlapResult",
    "PointInBoundaryInput",
    "PointInBoundaryResult",
    "PolygonValidationResult",
    "SimplifiedPolygonResult",
    "SimplifyPolygonInput",
]
