"""GIS API endpoints."""

from fastapi import APIRouter, HTTPException, status

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
from app.services.area_calculator import area_calculator
from app.services.boundary_service import boundary_service
from app.services.geofence_service import geofence_service


router = APIRouter()


@router.post("/reverse-geocode", response_model=AdminLocation)
async def reverse_geocode(coords: CoordinatesInput) -> AdminLocation:
    """Get administrative location from coordinates.

    Reverse geocodes latitude/longitude to county, sub-county, and ward.
    """
    return await boundary_service.get_administrative_location(
        latitude=coords.latitude,
        longitude=coords.longitude,
    )


@router.post("/validate-coordinates", response_model=dict)
async def validate_coordinates(coords: CoordinatesInput) -> dict:
    """Validate that coordinates are within Kenya.

    Returns whether the coordinates fall within Kenya's boundaries.
    """
    is_valid = await boundary_service.validate_coordinates_in_kenya(
        latitude=coords.latitude,
        longitude=coords.longitude,
    )
    return {
        "latitude": coords.latitude,
        "longitude": coords.longitude,
        "is_in_kenya": is_valid,
    }


@router.post("/validate-polygon", response_model=PolygonValidationResult)
async def validate_polygon(data: GeoJSONInput) -> PolygonValidationResult:
    """Validate a GeoJSON polygon geometry.

    Checks for valid structure, closed rings, self-intersections, etc.
    """
    return area_calculator.validate_polygon(data.geojson)


@router.post("/calculate-area", response_model=AreaCalculationResult)
async def calculate_area(data: GeoJSONInput) -> AreaCalculationResult:
    """Calculate area from a GeoJSON polygon.

    Returns area in acres, hectares, and square meters using geodetic calculations.
    """
    return area_calculator.calculate_area(data.geojson)


@router.post("/point-in-boundary", response_model=PointInBoundaryResult)
async def check_point_in_boundary(data: PointInBoundaryInput) -> PointInBoundaryResult:
    """Check if a point is within a boundary polygon.

    Also returns the distance to the nearest boundary edge.
    """
    return geofence_service.point_in_polygon(
        latitude=data.latitude,
        longitude=data.longitude,
        boundary=data.boundary,
    )


@router.post("/check-overlap", response_model=OverlapResult)
async def check_boundary_overlap(data: BoundaryPairInput) -> OverlapResult:
    """Check if two boundary polygons overlap.

    Returns overlap status, area, and percentage.
    """
    return geofence_service.check_overlap(
        boundary1=data.boundary1,
        boundary2=data.boundary2,
    )


@router.post("/simplify-polygon", response_model=SimplifiedPolygonResult)
async def simplify_polygon(data: SimplifyPolygonInput) -> SimplifiedPolygonResult:
    """Simplify a polygon to reduce vertex count.

    Useful for large polygons that need to be stored efficiently.
    """
    original_validation = area_calculator.validate_polygon(data.geojson)
    original_count = original_validation.vertex_count

    simplified = area_calculator.simplify_polygon(data.geojson, tolerance=data.tolerance)

    simplified_validation = area_calculator.validate_polygon(simplified)
    simplified_count = simplified_validation.vertex_count

    reduction = ((original_count - simplified_count) / original_count * 100) if original_count > 0 else 0

    return SimplifiedPolygonResult(
        simplified_geojson=simplified,
        original_vertex_count=original_count,
        simplified_vertex_count=simplified_count,
        reduction_percentage=round(reduction, 2),
    )


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "gis"}
