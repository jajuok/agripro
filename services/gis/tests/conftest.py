"""Test configuration and fixtures for GIS service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


# Sample GeoJSON polygons for testing
@pytest.fixture
def sample_polygon() -> dict:
    """A simple valid polygon in Nairobi area."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [36.8, -1.3],
            [36.85, -1.3],
            [36.85, -1.25],
            [36.8, -1.25],
            [36.8, -1.3],
        ]],
    }


@pytest.fixture
def sample_polygon_2() -> dict:
    """Another polygon that overlaps with sample_polygon."""
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
def non_overlapping_polygon() -> dict:
    """A polygon that doesn't overlap with sample_polygon."""
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
def self_intersecting_polygon() -> dict:
    """A self-intersecting (bowtie) polygon."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [36.8, -1.3],
            [36.85, -1.25],
            [36.85, -1.3],
            [36.8, -1.25],
            [36.8, -1.3],
        ]],
    }


@pytest.fixture
def nairobi_coordinates() -> dict:
    """Coordinates in Nairobi."""
    return {"latitude": -1.286389, "longitude": 36.817223}


@pytest.fixture
def mombasa_coordinates() -> dict:
    """Coordinates in Mombasa."""
    return {"latitude": -4.0435, "longitude": 39.6682}


@pytest.fixture
def outside_kenya_coordinates() -> dict:
    """Coordinates outside Kenya."""
    return {"latitude": 0.0, "longitude": 0.0}
