"""Unit tests for GIS services."""

import pytest

from app.services.area_calculator import AreaCalculator, area_calculator
from app.services.boundary_service import BoundaryService, boundary_service
from app.services.geofence_service import GeofenceService, geofence_service


class TestAreaCalculator:
    """Tests for AreaCalculator service."""

    def test_validate_valid_polygon(self, sample_polygon):
        """Test validating a valid polygon."""
        result = area_calculator.validate_polygon(sample_polygon)
        assert result.is_valid is True
        assert result.vertex_count == 5  # Including closing point
        assert result.is_closed is True

    def test_validate_self_intersecting_polygon(self, self_intersecting_polygon):
        """Test detecting self-intersecting polygon."""
        result = area_calculator.validate_polygon(self_intersecting_polygon)
        # Shapely should detect this as invalid
        assert result.is_valid is False or result.has_self_intersections is True

    def test_calculate_area(self, sample_polygon):
        """Test area calculation."""
        result = area_calculator.calculate_area(sample_polygon)
        # Area should be positive
        assert result.area_acres > 0
        assert result.area_hectares > 0
        assert result.area_square_meters > 0
        # Verify unit conversions are consistent
        assert abs(result.area_hectares * 2.47105 - result.area_acres) < 0.1

    def test_calculate_perimeter(self, sample_polygon):
        """Test perimeter calculation."""
        result = area_calculator.calculate_area(sample_polygon)
        assert result.perimeter_meters > 0
        # Rough check: perimeter should be reasonable for a ~5km x 5km area
        assert 10000 < result.perimeter_meters < 50000

    def test_simplify_polygon(self, sample_polygon):
        """Test polygon simplification."""
        # With very low tolerance, should keep most vertices
        simplified = area_calculator.simplify_polygon(sample_polygon, tolerance=0.0001)
        assert simplified["type"] == "Polygon"
        assert len(simplified["coordinates"][0]) >= 4  # At least 3 points + closing

    def test_invalid_geojson_type(self):
        """Test handling invalid GeoJSON type."""
        invalid = {"type": "Point", "coordinates": [36.8, -1.3]}
        result = area_calculator.validate_polygon(invalid)
        assert result.is_valid is False


class TestGeofenceService:
    """Tests for GeofenceService."""

    def test_point_inside_polygon(self, sample_polygon):
        """Test detecting point inside polygon."""
        # Point at center of sample polygon
        result = geofence_service.point_in_polygon(
            latitude=-1.275,
            longitude=36.825,
            boundary=sample_polygon,
        )
        assert result.is_inside is True
        assert result.distance_to_boundary_meters is not None
        assert result.distance_to_boundary_meters > 0

    def test_point_outside_polygon(self, sample_polygon):
        """Test detecting point outside polygon."""
        # Point outside the polygon
        result = geofence_service.point_in_polygon(
            latitude=-1.5,
            longitude=37.0,
            boundary=sample_polygon,
        )
        assert result.is_inside is False

    def test_check_overlap_overlapping(self, sample_polygon, sample_polygon_2):
        """Test detecting overlapping polygons."""
        result = geofence_service.check_overlap(
            boundary1=sample_polygon,
            boundary2=sample_polygon_2,
        )
        assert result.has_overlap is True
        assert result.overlap_area_acres > 0
        assert result.overlap_percentage > 0

    def test_check_overlap_non_overlapping(self, sample_polygon, non_overlapping_polygon):
        """Test detecting non-overlapping polygons."""
        result = geofence_service.check_overlap(
            boundary1=sample_polygon,
            boundary2=non_overlapping_polygon,
        )
        assert result.has_overlap is False
        assert result.overlap_area_acres == 0
        assert result.overlap_percentage == 0

    def test_check_coordinates_in_kenya(self, nairobi_coordinates, outside_kenya_coordinates):
        """Test Kenya boundary check."""
        # Nairobi should be in Kenya
        assert geofence_service.check_coordinates_in_kenya(
            latitude=nairobi_coordinates["latitude"],
            longitude=nairobi_coordinates["longitude"],
        ) is True

        # Outside Kenya
        assert geofence_service.check_coordinates_in_kenya(
            latitude=outside_kenya_coordinates["latitude"],
            longitude=outside_kenya_coordinates["longitude"],
        ) is False


class TestBoundaryService:
    """Tests for BoundaryService."""

    @pytest.mark.asyncio
    async def test_get_administrative_location_nairobi(self, nairobi_coordinates):
        """Test reverse geocoding for Nairobi coordinates."""
        result = await boundary_service.get_administrative_location(
            latitude=nairobi_coordinates["latitude"],
            longitude=nairobi_coordinates["longitude"],
        )
        assert result.is_valid is True
        assert result.country == "Kenya"
        assert result.county == "Nairobi"

    @pytest.mark.asyncio
    async def test_get_administrative_location_outside_kenya(self, outside_kenya_coordinates):
        """Test reverse geocoding for coordinates outside Kenya."""
        result = await boundary_service.get_administrative_location(
            latitude=outside_kenya_coordinates["latitude"],
            longitude=outside_kenya_coordinates["longitude"],
        )
        assert result.is_valid is False
        assert "outside Kenya" in result.message

    @pytest.mark.asyncio
    async def test_validate_coordinates_in_kenya(self, nairobi_coordinates, outside_kenya_coordinates):
        """Test coordinate validation."""
        # Nairobi
        assert await boundary_service.validate_coordinates_in_kenya(
            latitude=nairobi_coordinates["latitude"],
            longitude=nairobi_coordinates["longitude"],
        ) is True

        # Outside Kenya
        assert await boundary_service.validate_coordinates_in_kenya(
            latitude=outside_kenya_coordinates["latitude"],
            longitude=outside_kenya_coordinates["longitude"],
        ) is False
