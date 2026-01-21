"""Geofencing service for point-in-polygon and overlap detection."""

from typing import Any

from pyproj import Geod
from shapely.geometry import Point, Polygon, shape
from shapely.ops import nearest_points

from app.schemas.geo import OverlapResult, PointInBoundaryResult
from app.services.area_calculator import SQMETERS_TO_ACRES

# WGS84 ellipsoid for distance calculations
GEOD = Geod(ellps="WGS84")


class GeofenceService:
    """Service for geofencing operations."""

    def point_in_polygon(
        self,
        latitude: float,
        longitude: float,
        boundary: dict[str, Any],
    ) -> PointInBoundaryResult:
        """Check if a point is within a boundary polygon.

        Args:
            latitude: Point latitude
            longitude: Point longitude
            boundary: GeoJSON polygon boundary

        Returns:
            PointInBoundaryResult with inside status and distance
        """
        try:
            point = Point(longitude, latitude)  # Note: (lon, lat) order for Shapely
            polygon = shape(boundary)

            is_inside = polygon.contains(point)

            # Calculate distance to boundary
            distance_meters = self._calculate_distance_to_boundary(point, polygon)

            return PointInBoundaryResult(
                is_inside=is_inside,
                distance_to_boundary_meters=distance_meters,
            )
        except Exception as e:
            return PointInBoundaryResult(
                is_inside=False,
                distance_to_boundary_meters=None,
            )

    def check_overlap(
        self,
        boundary1: dict[str, Any],
        boundary2: dict[str, Any],
    ) -> OverlapResult:
        """Check if two boundaries overlap.

        Args:
            boundary1: First GeoJSON polygon
            boundary2: Second GeoJSON polygon

        Returns:
            OverlapResult with overlap details
        """
        try:
            poly1 = shape(boundary1)
            poly2 = shape(boundary2)

            # Check for intersection
            if not poly1.intersects(poly2):
                return OverlapResult(
                    has_overlap=False,
                    overlap_area_acres=0.0,
                    overlap_percentage=0.0,
                )

            # Calculate intersection
            intersection = poly1.intersection(poly2)

            if intersection.is_empty:
                return OverlapResult(
                    has_overlap=False,
                    overlap_area_acres=0.0,
                    overlap_percentage=0.0,
                )

            # Calculate areas using geodetic calculations
            from app.services.area_calculator import area_calculator

            # Get overlap area
            from shapely.geometry import mapping

            intersection_geojson = dict(mapping(intersection))
            overlap_result = area_calculator.calculate_area(intersection_geojson, validate=False)
            overlap_area_acres = overlap_result.area_acres

            # Get boundary1 area for percentage calculation
            poly1_result = area_calculator.calculate_area(boundary1, validate=False)
            poly1_area_acres = poly1_result.area_acres

            overlap_percentage = (overlap_area_acres / poly1_area_acres * 100) if poly1_area_acres > 0 else 0

            return OverlapResult(
                has_overlap=True,
                overlap_area_acres=overlap_area_acres,
                overlap_percentage=round(overlap_percentage, 2),
            )
        except Exception as e:
            return OverlapResult(
                has_overlap=False,
                overlap_area_acres=0.0,
                overlap_percentage=0.0,
            )

    def _calculate_distance_to_boundary(self, point: Point, polygon: Polygon) -> float:
        """Calculate geodetic distance from point to nearest boundary edge.

        Args:
            point: Shapely Point
            polygon: Shapely Polygon

        Returns:
            Distance in meters
        """
        # Get nearest point on boundary
        boundary = polygon.exterior
        nearest_pt = nearest_points(point, boundary)[1]

        # Calculate geodetic distance
        _, _, distance = GEOD.inv(
            point.x, point.y,  # lon1, lat1
            nearest_pt.x, nearest_pt.y,  # lon2, lat2
        )

        return abs(distance)

    def check_coordinates_in_kenya(
        self,
        latitude: float,
        longitude: float,
    ) -> bool:
        """Check if coordinates are within Kenya's approximate bounding box.

        This is a quick check before more detailed boundary lookup.

        Args:
            latitude: Point latitude
            longitude: Point longitude

        Returns:
            True if coordinates are roughly within Kenya
        """
        # Kenya approximate bounding box
        # Latitude: -4.7 to 5.0
        # Longitude: 33.9 to 41.9
        return (
            -4.7 <= latitude <= 5.0
            and 33.9 <= longitude <= 41.9
        )


# Singleton instance
geofence_service = GeofenceService()
