"""API integration tests for GIS service."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health endpoints."""

    def test_root_health(self, client: TestClient):
        """Test root health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "gis"

    def test_api_health(self, client: TestClient):
        """Test API health check."""
        response = client.get("/api/v1/gis/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestReverseGeocodeEndpoint:
    """Tests for reverse geocode endpoint."""

    def test_reverse_geocode_nairobi(self, client: TestClient, nairobi_coordinates):
        """Test reverse geocoding Nairobi coordinates."""
        response = client.post(
            "/api/v1/gis/reverse-geocode",
            json=nairobi_coordinates,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["country"] == "Kenya"
        assert data["county"] == "Nairobi"

    def test_reverse_geocode_outside_kenya(self, client: TestClient, outside_kenya_coordinates):
        """Test reverse geocoding coordinates outside Kenya."""
        response = client.post(
            "/api/v1/gis/reverse-geocode",
            json=outside_kenya_coordinates,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False


class TestValidateCoordinatesEndpoint:
    """Tests for validate coordinates endpoint."""

    def test_validate_coordinates_in_kenya(self, client: TestClient, nairobi_coordinates):
        """Test validating coordinates in Kenya."""
        response = client.post(
            "/api/v1/gis/validate-coordinates",
            json=nairobi_coordinates,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_in_kenya"] is True

    def test_validate_coordinates_outside_kenya(self, client: TestClient, outside_kenya_coordinates):
        """Test validating coordinates outside Kenya."""
        response = client.post(
            "/api/v1/gis/validate-coordinates",
            json=outside_kenya_coordinates,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_in_kenya"] is False


class TestValidatePolygonEndpoint:
    """Tests for polygon validation endpoint."""

    def test_validate_valid_polygon(self, client: TestClient, sample_polygon):
        """Test validating a valid polygon."""
        response = client.post(
            "/api/v1/gis/validate-polygon",
            json={"geojson": sample_polygon},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["is_closed"] is True

    def test_validate_self_intersecting_polygon(self, client: TestClient, self_intersecting_polygon):
        """Test validating a self-intersecting polygon."""
        response = client.post(
            "/api/v1/gis/validate-polygon",
            json={"geojson": self_intersecting_polygon},
        )
        assert response.status_code == 200
        data = response.json()
        # Should be marked as invalid or have self-intersections flagged
        assert data["is_valid"] is False or data["has_self_intersections"] is True


class TestCalculateAreaEndpoint:
    """Tests for area calculation endpoint."""

    def test_calculate_area(self, client: TestClient, sample_polygon):
        """Test calculating polygon area."""
        response = client.post(
            "/api/v1/gis/calculate-area",
            json={"geojson": sample_polygon},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["area_acres"] > 0
        assert data["area_hectares"] > 0
        assert data["area_square_meters"] > 0
        assert data["perimeter_meters"] > 0


class TestPointInBoundaryEndpoint:
    """Tests for point in boundary endpoint."""

    def test_point_inside(self, client: TestClient, sample_polygon):
        """Test point inside boundary."""
        response = client.post(
            "/api/v1/gis/point-in-boundary",
            json={
                "latitude": -1.275,
                "longitude": 36.825,
                "boundary": sample_polygon,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_inside"] is True
        assert data["distance_to_boundary_meters"] > 0

    def test_point_outside(self, client: TestClient, sample_polygon):
        """Test point outside boundary."""
        response = client.post(
            "/api/v1/gis/point-in-boundary",
            json={
                "latitude": -1.5,
                "longitude": 37.0,
                "boundary": sample_polygon,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_inside"] is False


class TestCheckOverlapEndpoint:
    """Tests for boundary overlap endpoint."""

    def test_overlapping_boundaries(self, client: TestClient, sample_polygon, sample_polygon_2):
        """Test detecting overlapping boundaries."""
        response = client.post(
            "/api/v1/gis/check-overlap",
            json={
                "boundary1": sample_polygon,
                "boundary2": sample_polygon_2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_overlap"] is True
        assert data["overlap_area_acres"] > 0
        assert data["overlap_percentage"] > 0

    def test_non_overlapping_boundaries(self, client: TestClient, sample_polygon, non_overlapping_polygon):
        """Test detecting non-overlapping boundaries."""
        response = client.post(
            "/api/v1/gis/check-overlap",
            json={
                "boundary1": sample_polygon,
                "boundary2": non_overlapping_polygon,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_overlap"] is False


class TestSimplifyPolygonEndpoint:
    """Tests for polygon simplification endpoint."""

    def test_simplify_polygon(self, client: TestClient, sample_polygon):
        """Test polygon simplification."""
        response = client.post(
            "/api/v1/gis/simplify-polygon",
            json={
                "geojson": sample_polygon,
                "tolerance": 0.001,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "simplified_geojson" in data
        assert data["original_vertex_count"] > 0
        assert data["simplified_vertex_count"] > 0
