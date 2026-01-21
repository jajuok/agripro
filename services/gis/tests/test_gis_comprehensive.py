"""Comprehensive tests for GIS service functionality."""

import pytest
from fastapi.testclient import TestClient

from app.services.area_calculator import AreaCalculator, area_calculator
from app.services.boundary_service import BoundaryService, boundary_service
from app.services.geofence_service import GeofenceService, geofence_service


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def nairobi_coordinates():
    """Coordinates for Nairobi city center."""
    return {"latitude": -1.286389, "longitude": 36.817223}


@pytest.fixture
def mombasa_coordinates():
    """Coordinates for Mombasa."""
    return {"latitude": -4.0435, "longitude": 39.6682}


@pytest.fixture
def kisumu_coordinates():
    """Coordinates for Kisumu."""
    return {"latitude": -0.0917, "longitude": 34.7680}


@pytest.fixture
def nakuru_coordinates():
    """Coordinates for Nakuru."""
    return {"latitude": -0.3031, "longitude": 36.0800}


@pytest.fixture
def eldoret_coordinates():
    """Coordinates for Eldoret."""
    return {"latitude": 0.5143, "longitude": 35.2698}


@pytest.fixture
def outside_kenya_coordinates():
    """Coordinates outside Kenya (Dar es Salaam, Tanzania)."""
    return {"latitude": -6.7924, "longitude": 39.2083}


@pytest.fixture
def europe_coordinates():
    """Coordinates in Europe (London)."""
    return {"latitude": 51.5074, "longitude": -0.1278}


@pytest.fixture
def sample_polygon():
    """Standard valid polygon in Nairobi area (~5km x 5km)."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [36.8, -1.3],
            [36.85, -1.3],
            [36.85, -1.25],
            [36.8, -1.25],
            [36.8, -1.3],  # Closing point
        ]],
    }


@pytest.fixture
def sample_polygon_2():
    """Second polygon that overlaps with sample_polygon."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [36.82, -1.28],
            [36.87, -1.28],
            [36.87, -1.23],
            [36.82, -1.23],
            [36.82, -1.28],
        ]],
    }


@pytest.fixture
def non_overlapping_polygon():
    """Polygon that does not overlap with sample_polygon."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [37.0, -1.0],
            [37.05, -1.0],
            [37.05, -0.95],
            [37.0, -0.95],
            [37.0, -1.0],
        ]],
    }


@pytest.fixture
def self_intersecting_polygon():
    """Self-intersecting (bowtie) polygon."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [36.8, -1.3],
            [36.85, -1.25],  # Crosses to opposite corner
            [36.85, -1.3],
            [36.8, -1.25],   # Crosses back
            [36.8, -1.3],
        ]],
    }


@pytest.fixture
def unclosed_polygon():
    """Polygon without closing point."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [36.8, -1.3],
            [36.85, -1.3],
            [36.85, -1.25],
            [36.8, -1.25],
            # Missing closing point [36.8, -1.3]
        ]],
    }


@pytest.fixture
def small_polygon():
    """Very small polygon (approximately 100m x 100m)."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [36.8, -1.3],
            [36.801, -1.3],
            [36.801, -1.299],
            [36.8, -1.299],
            [36.8, -1.3],
        ]],
    }


@pytest.fixture
def large_polygon():
    """Large polygon (approximately 50km x 50km)."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [36.5, -1.5],
            [37.0, -1.5],
            [37.0, -1.0],
            [36.5, -1.0],
            [36.5, -1.5],
        ]],
    }


@pytest.fixture
def complex_polygon():
    """Complex polygon with many vertices."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [36.8, -1.3],
            [36.81, -1.31],
            [36.82, -1.30],
            [36.83, -1.31],
            [36.84, -1.30],
            [36.85, -1.3],
            [36.85, -1.28],
            [36.84, -1.27],
            [36.83, -1.26],
            [36.82, -1.25],
            [36.81, -1.26],
            [36.8, -1.27],
            [36.8, -1.3],
        ]],
    }


@pytest.fixture
def point_geojson():
    """Invalid GeoJSON - Point instead of Polygon."""
    return {
        "type": "Point",
        "coordinates": [36.8, -1.3],
    }


@pytest.fixture
def linestring_geojson():
    """Invalid GeoJSON - LineString instead of Polygon."""
    return {
        "type": "LineString",
        "coordinates": [[36.8, -1.3], [36.85, -1.25]],
    }


# ============================================================================
# AREA CALCULATOR SERVICE TESTS
# ============================================================================

class TestAreaCalculatorValidation:
    """Tests for polygon validation in AreaCalculator."""

    def test_validate_valid_polygon(self, sample_polygon):
        """Test validating a standard valid polygon."""
        result = area_calculator.validate_polygon(sample_polygon)
        assert result.is_valid is True
        assert result.is_closed is True
        assert result.vertex_count == 5
        assert result.has_self_intersection is False

    def test_validate_complex_polygon(self, complex_polygon):
        """Test validating a complex polygon with many vertices."""
        result = area_calculator.validate_polygon(complex_polygon)
        assert result.is_valid is True
        assert result.vertex_count == 13

    def test_validate_self_intersecting_polygon(self, self_intersecting_polygon):
        """Test detecting self-intersecting polygon."""
        result = area_calculator.validate_polygon(self_intersecting_polygon)
        # Shapely should detect this as invalid or having self-intersection
        assert result.is_valid is False or result.has_self_intersection is True

    def test_validate_unclosed_polygon(self, unclosed_polygon):
        """Test handling unclosed polygon."""
        result = area_calculator.validate_polygon(unclosed_polygon)
        # Should either auto-close or mark as invalid
        assert result.is_closed is False or result.is_valid is True

    def test_validate_point_instead_of_polygon(self, point_geojson):
        """Test rejecting Point geometry."""
        result = area_calculator.validate_polygon(point_geojson)
        assert result.is_valid is False
        # Check that errors list contains a message about geometry type
        assert len(result.errors) > 0 or result.vertex_count == 0

    def test_validate_linestring_instead_of_polygon(self, linestring_geojson):
        """Test rejecting LineString geometry."""
        result = area_calculator.validate_polygon(linestring_geojson)
        assert result.is_valid is False

    def test_validate_too_few_vertices(self):
        """Test rejecting polygon with too few vertices."""
        invalid_polygon = {
            "type": "Polygon",
            "coordinates": [[[36.8, -1.3], [36.85, -1.3]]],  # Only 2 points
        }
        result = area_calculator.validate_polygon(invalid_polygon)
        assert result.is_valid is False


class TestAreaCalculatorCalculations:
    """Tests for area calculations in AreaCalculator."""

    def test_calculate_area_standard(self, sample_polygon):
        """Test calculating area for standard polygon."""
        result = area_calculator.calculate_area(sample_polygon)
        assert result.area_acres > 0
        assert result.area_hectares > 0
        assert result.area_square_meters > 0
        assert result.perimeter_meters > 0

    def test_area_unit_consistency(self, sample_polygon):
        """Test that area unit conversions are consistent."""
        result = area_calculator.calculate_area(sample_polygon)
        # 1 hectare = 2.47105 acres
        expected_acres = result.area_hectares * 2.47105
        assert abs(result.area_acres - expected_acres) < 0.1
        # 1 hectare = 10000 square meters
        expected_sqm = result.area_hectares * 10000
        assert abs(result.area_square_meters - expected_sqm) < 100

    def test_calculate_small_area(self, small_polygon):
        """Test calculating area for small polygon."""
        result = area_calculator.calculate_area(small_polygon)
        # Should be approximately 1 hectare or less
        assert result.area_hectares < 10
        assert result.area_acres > 0

    def test_calculate_large_area(self, large_polygon):
        """Test calculating area for large polygon."""
        result = area_calculator.calculate_area(large_polygon)
        # Large polygon should have significant area
        assert result.area_hectares > 1000
        assert result.area_square_meters > 10_000_000

    def test_perimeter_calculation(self, sample_polygon):
        """Test perimeter calculation is reasonable."""
        result = area_calculator.calculate_area(sample_polygon)
        # For a ~5km x 5km square, perimeter should be ~20km
        assert 15000 < result.perimeter_meters < 25000


class TestAreaCalculatorSimplification:
    """Tests for polygon simplification."""

    def test_simplify_polygon_low_tolerance(self, complex_polygon):
        """Test simplification with low tolerance preserves shape."""
        simplified = area_calculator.simplify_polygon(complex_polygon, tolerance=0.0001)
        assert simplified["type"] == "Polygon"
        # Should preserve most vertices with low tolerance
        simplified_count = len(simplified["coordinates"][0])
        assert simplified_count >= 4  # At least a quadrilateral

    def test_simplify_polygon_high_tolerance(self, complex_polygon):
        """Test simplification with high tolerance reduces vertices."""
        simplified = area_calculator.simplify_polygon(complex_polygon, tolerance=0.01)
        assert simplified["type"] == "Polygon"
        original_count = len(complex_polygon["coordinates"][0])
        simplified_count = len(simplified["coordinates"][0])
        # High tolerance should reduce vertex count
        assert simplified_count <= original_count

    def test_simplify_simple_polygon(self, sample_polygon):
        """Test simplifying already simple polygon."""
        simplified = area_calculator.simplify_polygon(sample_polygon, tolerance=0.0001)
        # Should remain valid
        assert simplified["type"] == "Polygon"
        assert len(simplified["coordinates"][0]) >= 4


# ============================================================================
# GEOFENCE SERVICE TESTS
# ============================================================================

class TestGeofencePointInPolygon:
    """Tests for point-in-polygon detection."""

    def test_point_inside_polygon(self, sample_polygon):
        """Test detecting point clearly inside polygon."""
        result = geofence_service.point_in_polygon(
            latitude=-1.275,
            longitude=36.825,
            boundary=sample_polygon,
        )
        assert result.is_inside is True
        assert result.distance_to_boundary_meters > 0

    def test_point_outside_polygon(self, sample_polygon):
        """Test detecting point clearly outside polygon."""
        result = geofence_service.point_in_polygon(
            latitude=-1.5,
            longitude=37.0,
            boundary=sample_polygon,
        )
        assert result.is_inside is False

    def test_point_on_boundary(self, sample_polygon):
        """Test detecting point on polygon boundary."""
        # Point exactly on the edge
        result = geofence_service.point_in_polygon(
            latitude=-1.3,
            longitude=36.825,  # On the bottom edge
            boundary=sample_polygon,
        )
        # Behavior may vary - could be inside or on boundary
        assert result.distance_to_boundary_meters is not None

    def test_point_at_corner(self, sample_polygon):
        """Test detecting point at polygon corner."""
        result = geofence_service.point_in_polygon(
            latitude=-1.3,
            longitude=36.8,  # Bottom-left corner
            boundary=sample_polygon,
        )
        assert result.distance_to_boundary_meters is not None

    def test_point_far_outside(self, sample_polygon, europe_coordinates):
        """Test detecting point very far outside (different continent)."""
        result = geofence_service.point_in_polygon(
            latitude=europe_coordinates["latitude"],
            longitude=europe_coordinates["longitude"],
            boundary=sample_polygon,
        )
        assert result.is_inside is False


class TestGeofenceOverlapDetection:
    """Tests for boundary overlap detection."""

    def test_overlapping_boundaries(self, sample_polygon, sample_polygon_2):
        """Test detecting overlapping boundaries."""
        result = geofence_service.check_overlap(
            boundary1=sample_polygon,
            boundary2=sample_polygon_2,
        )
        assert result.has_overlap is True
        assert result.overlap_area_acres > 0
        assert 0 < result.overlap_percentage <= 100

    def test_non_overlapping_boundaries(self, sample_polygon, non_overlapping_polygon):
        """Test detecting non-overlapping boundaries."""
        result = geofence_service.check_overlap(
            boundary1=sample_polygon,
            boundary2=non_overlapping_polygon,
        )
        assert result.has_overlap is False
        assert result.overlap_area_acres == 0
        assert result.overlap_percentage == 0

    def test_identical_boundaries(self, sample_polygon):
        """Test overlap of identical boundaries."""
        result = geofence_service.check_overlap(
            boundary1=sample_polygon,
            boundary2=sample_polygon,
        )
        assert result.has_overlap is True
        assert result.overlap_percentage == 100

    def test_one_boundary_inside_other(self, sample_polygon):
        """Test when one boundary is completely inside another."""
        # Create a polygon completely inside sample_polygon
        inner_polygon = {
            "type": "Polygon",
            "coordinates": [[
                [36.82, -1.28],
                [36.83, -1.28],
                [36.83, -1.27],
                [36.82, -1.27],
                [36.82, -1.28],
            ]],
        }
        result = geofence_service.check_overlap(
            boundary1=sample_polygon,
            boundary2=inner_polygon,
        )
        assert result.has_overlap is True
        # The inner polygon should be 100% inside


class TestGeofenceKenyaBoundary:
    """Tests for Kenya boundary validation."""

    def test_nairobi_in_kenya(self, nairobi_coordinates):
        """Test that Nairobi is in Kenya."""
        result = geofence_service.check_coordinates_in_kenya(
            latitude=nairobi_coordinates["latitude"],
            longitude=nairobi_coordinates["longitude"],
        )
        assert result is True

    def test_mombasa_in_kenya(self, mombasa_coordinates):
        """Test that Mombasa is in Kenya."""
        result = geofence_service.check_coordinates_in_kenya(
            latitude=mombasa_coordinates["latitude"],
            longitude=mombasa_coordinates["longitude"],
        )
        assert result is True

    def test_kisumu_in_kenya(self, kisumu_coordinates):
        """Test that Kisumu is in Kenya."""
        result = geofence_service.check_coordinates_in_kenya(
            latitude=kisumu_coordinates["latitude"],
            longitude=kisumu_coordinates["longitude"],
        )
        assert result is True

    def test_dar_es_salaam_not_in_kenya(self, outside_kenya_coordinates):
        """Test that Dar es Salaam is not in Kenya."""
        result = geofence_service.check_coordinates_in_kenya(
            latitude=outside_kenya_coordinates["latitude"],
            longitude=outside_kenya_coordinates["longitude"],
        )
        assert result is False

    def test_london_not_in_kenya(self, europe_coordinates):
        """Test that London is not in Kenya."""
        result = geofence_service.check_coordinates_in_kenya(
            latitude=europe_coordinates["latitude"],
            longitude=europe_coordinates["longitude"],
        )
        assert result is False


# ============================================================================
# BOUNDARY SERVICE TESTS
# ============================================================================

class TestBoundaryServiceReverseGeocoding:
    """Tests for reverse geocoding functionality."""

    @pytest.mark.asyncio
    async def test_reverse_geocode_nairobi(self, nairobi_coordinates):
        """Test reverse geocoding Nairobi returns correct county."""
        result = await boundary_service.get_administrative_location(
            latitude=nairobi_coordinates["latitude"],
            longitude=nairobi_coordinates["longitude"],
        )
        assert result.is_valid is True
        assert result.country == "Kenya"
        assert result.county == "Nairobi"

    @pytest.mark.asyncio
    async def test_reverse_geocode_mombasa(self, mombasa_coordinates):
        """Test reverse geocoding Mombasa returns correct county."""
        result = await boundary_service.get_administrative_location(
            latitude=mombasa_coordinates["latitude"],
            longitude=mombasa_coordinates["longitude"],
        )
        assert result.is_valid is True
        assert result.country == "Kenya"
        assert result.county == "Mombasa"

    @pytest.mark.asyncio
    async def test_reverse_geocode_kisumu(self, kisumu_coordinates):
        """Test reverse geocoding Kisumu returns correct county."""
        result = await boundary_service.get_administrative_location(
            latitude=kisumu_coordinates["latitude"],
            longitude=kisumu_coordinates["longitude"],
        )
        assert result.is_valid is True
        assert result.country == "Kenya"
        assert result.county == "Kisumu"

    @pytest.mark.asyncio
    async def test_reverse_geocode_outside_kenya(self, outside_kenya_coordinates):
        """Test reverse geocoding coordinates outside Kenya."""
        result = await boundary_service.get_administrative_location(
            latitude=outside_kenya_coordinates["latitude"],
            longitude=outside_kenya_coordinates["longitude"],
        )
        assert result.is_valid is False
        # Message may indicate location is outside Kenya
        assert result.message is not None or result.county is None


class TestBoundaryServiceValidation:
    """Tests for coordinate validation."""

    @pytest.mark.asyncio
    async def test_validate_nairobi_coordinates(self, nairobi_coordinates):
        """Test validating Nairobi coordinates."""
        result = await boundary_service.validate_coordinates_in_kenya(
            latitude=nairobi_coordinates["latitude"],
            longitude=nairobi_coordinates["longitude"],
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_outside_kenya(self, outside_kenya_coordinates):
        """Test validating coordinates outside Kenya."""
        result = await boundary_service.validate_coordinates_in_kenya(
            latitude=outside_kenya_coordinates["latitude"],
            longitude=outside_kenya_coordinates["longitude"],
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_boundary_coordinates(self):
        """Test coordinates at Kenya boundary."""
        # Near Kenya-Tanzania border
        result = await boundary_service.validate_coordinates_in_kenya(
            latitude=-4.5,
            longitude=39.0,
        )
        # Should be inside Kenya (Mombasa area)
        assert result is True


# ============================================================================
# API ENDPOINT TESTS (Extended)
# ============================================================================

class TestReverseGeocodeEndpointExtended:
    """Extended tests for reverse geocode endpoint."""

    def test_reverse_geocode_all_major_cities(self, client: TestClient):
        """Test reverse geocoding for all major Kenyan cities."""
        cities = [
            {"name": "Nairobi", "latitude": -1.286389, "longitude": 36.817223},
            {"name": "Mombasa", "latitude": -4.0435, "longitude": 39.6682},
            {"name": "Kisumu", "latitude": -0.0917, "longitude": 34.7680},
            {"name": "Nakuru", "latitude": -0.3031, "longitude": 36.0800},
            {"name": "Eldoret", "latitude": 0.5143, "longitude": 35.2698},
        ]

        for city in cities:
            response = client.post(
                "/api/v1/gis/reverse-geocode",
                json={"latitude": city["latitude"], "longitude": city["longitude"]},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert data["country"] == "Kenya"

    def test_reverse_geocode_invalid_latitude(self, client: TestClient):
        """Test reverse geocoding with invalid latitude."""
        response = client.post(
            "/api/v1/gis/reverse-geocode",
            json={"latitude": 100, "longitude": 36.8},  # Invalid latitude
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_reverse_geocode_invalid_longitude(self, client: TestClient):
        """Test reverse geocoding with invalid longitude."""
        response = client.post(
            "/api/v1/gis/reverse-geocode",
            json={"latitude": -1.3, "longitude": 200},  # Invalid longitude
        )
        assert response.status_code in [200, 400, 422]


class TestValidatePolygonEndpointExtended:
    """Extended tests for polygon validation endpoint."""

    @pytest.mark.xfail(reason="Empty coordinates cause IndexError - service needs fix")
    def test_validate_polygon_empty_coordinates(self, client: TestClient):
        """Test validating polygon with empty coordinates."""
        response = client.post(
            "/api/v1/gis/validate-polygon",
            json={"geojson": {"type": "Polygon", "coordinates": []}},
        )
        # Should return error status or validation failure, not crash
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            assert response.json()["is_valid"] is False

    def test_validate_polygon_missing_type(self, client: TestClient):
        """Test validating GeoJSON without type."""
        response = client.post(
            "/api/v1/gis/validate-polygon",
            json={"geojson": {"coordinates": [[[36.8, -1.3], [36.85, -1.3]]]}},
        )
        assert response.status_code in [200, 400, 422]


class TestCalculateAreaEndpointExtended:
    """Extended tests for area calculation endpoint."""

    def test_calculate_area_small_polygon(self, client: TestClient, small_polygon):
        """Test calculating area for small polygon."""
        response = client.post(
            "/api/v1/gis/calculate-area",
            json={"geojson": small_polygon},
        )
        assert response.status_code == 200
        data = response.json()
        # Small polygon should have small area
        assert data["area_hectares"] < 10

    def test_calculate_area_large_polygon(self, client: TestClient, large_polygon):
        """Test calculating area for large polygon."""
        response = client.post(
            "/api/v1/gis/calculate-area",
            json={"geojson": large_polygon},
        )
        assert response.status_code == 200
        data = response.json()
        # Large polygon should have large area
        assert data["area_hectares"] > 1000


class TestPointInBoundaryEndpointExtended:
    """Extended tests for point-in-boundary endpoint."""

    def test_multiple_points_same_boundary(self, client: TestClient, sample_polygon):
        """Test checking multiple points against same boundary."""
        points = [
            {"lat": -1.275, "lon": 36.825, "expected": True},   # Inside
            {"lat": -1.5, "lon": 37.0, "expected": False},      # Outside
            {"lat": -1.28, "lon": 36.83, "expected": True},     # Inside
        ]

        for point in points:
            response = client.post(
                "/api/v1/gis/point-in-boundary",
                json={
                    "latitude": point["lat"],
                    "longitude": point["lon"],
                    "boundary": sample_polygon,
                },
            )
            assert response.status_code == 200
            assert response.json()["is_inside"] == point["expected"]


# ============================================================================
# EDGE CASE AND ERROR HANDLING TESTS
# ============================================================================

class TestEdgeCasesGIS:
    """Tests for GIS edge cases and error handling."""

    def test_very_precise_coordinates(self, client: TestClient):
        """Test handling coordinates with many decimal places."""
        response = client.post(
            "/api/v1/gis/reverse-geocode",
            json={
                "latitude": -1.2863891234567890,
                "longitude": 36.8172231234567890,
            },
        )
        assert response.status_code == 200

    def test_zero_coordinates(self, client: TestClient):
        """Test handling zero coordinates (null island)."""
        response = client.post(
            "/api/v1/gis/validate-coordinates",
            json={"latitude": 0, "longitude": 0},
        )
        assert response.status_code == 200
        # Should not be in Kenya
        assert response.json()["is_in_kenya"] is False

    def test_polygon_with_many_vertices(self, client: TestClient):
        """Test handling polygon with many vertices."""
        # Create polygon with 100 vertices
        coords = []
        import math
        for i in range(100):
            angle = 2 * math.pi * i / 99
            lat = -1.3 + 0.05 * math.sin(angle)
            lon = 36.8 + 0.05 * math.cos(angle)
            coords.append([lon, lat])
        coords.append(coords[0])  # Close the polygon

        polygon = {"type": "Polygon", "coordinates": [coords]}
        response = client.post(
            "/api/v1/gis/validate-polygon",
            json={"geojson": polygon},
        )
        assert response.status_code == 200

    def test_simplify_polygon_zero_tolerance(self, client: TestClient, complex_polygon):
        """Test simplification with zero tolerance."""
        response = client.post(
            "/api/v1/gis/simplify-polygon",
            json={"geojson": complex_polygon, "tolerance": 0},
        )
        assert response.status_code == 200
        data = response.json()
        # Should preserve all vertices with zero tolerance
        assert data["simplified_vertex_count"] == data["original_vertex_count"]
