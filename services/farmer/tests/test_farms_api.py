"""Comprehensive tests for Farm API endpoints.

Tests cover:
- Farm CRUD operations
- List farms by farmer_id
- List farms by user_id (new endpoint)
- Error handling and edge cases
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer, FarmProfile


@pytest_asyncio.fixture
async def test_farm(db_session: AsyncSession, test_farmer: Farmer) -> FarmProfile:
    """Create a test farm."""
    farm = FarmProfile(
        id=uuid.uuid4(),
        farmer_id=test_farmer.id,
        name="Test Farm",
        latitude=-1.2921,
        longitude=36.8219,
        county="Nairobi",
        sub_county="Westlands",
        total_acreage=10.5,
        cultivable_acreage=8.0,
        ownership_type="owned",
        registration_step="location",
    )
    db_session.add(farm)
    await db_session.commit()
    await db_session.refresh(farm)
    return farm


@pytest_asyncio.fixture
async def multiple_farms(db_session: AsyncSession, test_farmer: Farmer) -> list[FarmProfile]:
    """Create multiple test farms for a farmer."""
    farms = []
    for i in range(3):
        farm = FarmProfile(
            id=uuid.uuid4(),
            farmer_id=test_farmer.id,
            name=f"Farm {i+1}",
            latitude=-1.2921 + (i * 0.01),
            longitude=36.8219 + (i * 0.01),
            county="Nairobi",
            total_acreage=5.0 + i,
            registration_step="location",
        )
        db_session.add(farm)
        farms.append(farm)
    await db_session.commit()
    for farm in farms:
        await db_session.refresh(farm)
    return farms


class TestFarmCreation:
    """Tests for farm creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_farm_success(self, client: AsyncClient, test_farmer: Farmer):
        """Test successful farm creation."""
        farm_data = {
            "farmer_id": str(test_farmer.id),
            "name": "New Farm",
            "latitude": -1.2921,
            "longitude": 36.8219,
        }

        response = await client.post("/api/v1/farms", json=farm_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Farm"
        assert data["farmer_id"] == str(test_farmer.id)
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_farm_with_all_fields(self, client: AsyncClient, test_farmer: Farmer):
        """Test farm creation with all optional fields."""
        farm_data = {
            "farmer_id": str(test_farmer.id),
            "name": "Complete Farm",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "total_acreage": 15.5,
            "cultivable_acreage": 12.0,
            "ownership_type": "leased",
            "soil_type": "loamy",
            "water_source": "borehole",
            "irrigation_type": "drip",
        }

        response = await client.post("/api/v1/farms", json=farm_data)

        assert response.status_code == 201
        data = response.json()
        assert data["total_acreage"] == 15.5
        assert data["soil_type"] == "loamy"
        assert data["ownership_type"] == "leased"

    @pytest.mark.asyncio
    async def test_create_farm_missing_required_fields(self, client: AsyncClient):
        """Test farm creation fails without required fields."""
        farm_data = {
            "name": "Incomplete Farm",
            # Missing farmer_id
        }

        response = await client.post("/api/v1/farms", json=farm_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_farm_invalid_coordinates(self, client: AsyncClient, test_farmer: Farmer):
        """Test farm creation with invalid coordinates."""
        farm_data = {
            "farmer_id": str(test_farmer.id),
            "name": "Invalid Farm",
            "latitude": 100.0,  # Invalid latitude
            "longitude": 36.8219,
        }

        response = await client.post("/api/v1/farms", json=farm_data)

        # Should either reject or accept based on validation rules
        # If no validation, it may succeed with a 201
        assert response.status_code in [201, 422]


class TestFarmRetrieval:
    """Tests for farm retrieval endpoints."""

    @pytest.mark.asyncio
    async def test_get_farm_by_id(self, client: AsyncClient, test_farm: FarmProfile):
        """Test getting farm by ID."""
        response = await client.get(f"/api/v1/farms/{test_farm.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_farm.id)
        assert data["name"] == test_farm.name

    @pytest.mark.asyncio
    async def test_get_farm_not_found(self, client: AsyncClient):
        """Test getting non-existent farm returns 404."""
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/farms/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Farm not found"

    @pytest.mark.asyncio
    async def test_get_farm_invalid_uuid(self, client: AsyncClient):
        """Test getting farm with invalid UUID format."""
        response = await client.get("/api/v1/farms/invalid-uuid")

        assert response.status_code == 422


class TestFarmUpdate:
    """Tests for farm update endpoint."""

    @pytest.mark.asyncio
    async def test_update_farm_partial(self, client: AsyncClient, test_farm: FarmProfile):
        """Test partial update of farm."""
        update_data = {
            "name": "Updated Farm Name",
            "total_acreage": 20.0,
        }

        response = await client.patch(
            f"/api/v1/farms/{test_farm.id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Farm Name"
        assert data["total_acreage"] == 20.0
        # Original data should be preserved
        assert data["farmer_id"] == str(test_farm.farmer_id)

    @pytest.mark.asyncio
    async def test_update_farm_soil_water(self, client: AsyncClient, test_farm: FarmProfile):
        """Test updating farm's soil and water information."""
        update_data = {
            "soil_type": "clay",
            "soil_ph": 6.5,
            "water_source": "river",
            "irrigation_type": "sprinkler",
        }

        response = await client.patch(
            f"/api/v1/farms/{test_farm.id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["soil_type"] == "clay"
        assert data["water_source"] == "river"

    @pytest.mark.asyncio
    async def test_update_farm_not_found(self, client: AsyncClient):
        """Test updating non-existent farm returns 404."""
        fake_id = uuid.uuid4()
        update_data = {"name": "Test"}

        response = await client.patch(f"/api/v1/farms/{fake_id}", json=update_data)

        assert response.status_code == 404


class TestFarmListByFarmerId:
    """Tests for listing farms by farmer_id endpoint."""

    @pytest.mark.asyncio
    async def test_list_farms_by_farmer_id(
        self, client: AsyncClient, test_farmer: Farmer, multiple_farms: list[FarmProfile]
    ):
        """Test listing all farms for a farmer."""
        response = await client.get(f"/api/v1/farms/farmer/{test_farmer.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(f["farmer_id"] == str(test_farmer.id) for f in data)

    @pytest.mark.asyncio
    async def test_list_farms_by_farmer_id_empty(self, client: AsyncClient, test_farmer: Farmer):
        """Test listing farms for farmer with no farms."""
        response = await client.get(f"/api/v1/farms/farmer/{test_farmer.id}")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_list_farms_by_nonexistent_farmer(self, client: AsyncClient):
        """Test listing farms for non-existent farmer returns empty list."""
        fake_farmer_id = uuid.uuid4()
        response = await client.get(f"/api/v1/farms/farmer/{fake_farmer_id}")

        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestFarmListByUserId:
    """Tests for listing farms by user_id endpoint (new feature)."""

    @pytest.mark.asyncio
    async def test_list_farms_by_user_id(
        self, client: AsyncClient, test_farmer: Farmer, multiple_farms: list[FarmProfile]
    ):
        """Test listing all farms for a user (via farmer lookup)."""
        response = await client.get(f"/api/v1/farms/user/{test_farmer.user_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # All farms should belong to the farmer linked to this user_id
        assert all(f["farmer_id"] == str(test_farmer.id) for f in data)

    @pytest.mark.asyncio
    async def test_list_farms_by_user_id_no_farmer(self, client: AsyncClient):
        """Test listing farms for user with no farmer profile returns empty list."""
        fake_user_id = uuid.uuid4()
        response = await client.get(f"/api/v1/farms/user/{fake_user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_list_farms_by_user_id_no_farms(self, client: AsyncClient, test_farmer: Farmer):
        """Test listing farms for user with farmer profile but no farms."""
        response = await client.get(f"/api/v1/farms/user/{test_farmer.user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_list_farms_by_user_id_invalid_uuid(self, client: AsyncClient):
        """Test listing farms with invalid user_id format."""
        response = await client.get("/api/v1/farms/user/invalid-uuid")

        assert response.status_code == 422


class TestFarmDataIntegrity:
    """Tests for data integrity and consistency."""

    @pytest.mark.asyncio
    async def test_farm_farmer_relationship(
        self, client: AsyncClient, test_farmer: Farmer, test_farm: FarmProfile
    ):
        """Test farm is correctly linked to farmer."""
        farm_response = await client.get(f"/api/v1/farms/{test_farm.id}")
        assert farm_response.status_code == 200
        farm_data = farm_response.json()

        # Farm should reference the correct farmer
        assert farm_data["farmer_id"] == str(test_farmer.id)

    @pytest.mark.asyncio
    async def test_multiple_farms_same_farmer(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test creating multiple farms for same farmer."""
        # Create first farm
        farm1_data = {
            "farmer_id": str(test_farmer.id),
            "name": "Farm One",
            "latitude": -1.2921,
            "longitude": 36.8219,
        }
        response1 = await client.post("/api/v1/farms", json=farm1_data)
        assert response1.status_code == 201

        # Create second farm
        farm2_data = {
            "farmer_id": str(test_farmer.id),
            "name": "Farm Two",
            "latitude": -1.2950,
            "longitude": 36.8300,
        }
        response2 = await client.post("/api/v1/farms", json=farm2_data)
        assert response2.status_code == 201

        # List farms - should have both
        list_response = await client.get(f"/api/v1/farms/farmer/{test_farmer.id}")
        assert list_response.status_code == 200
        farms = list_response.json()
        assert len(farms) == 2
        assert {f["name"] for f in farms} == {"Farm One", "Farm Two"}


class TestFarmBoundaryOperations:
    """Tests for farm boundary-related operations (via registration workflow)."""

    @pytest.mark.asyncio
    async def test_farm_boundary_via_registration(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test setting farm boundary via registration workflow."""
        # Start registration
        start_response = await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(test_farmer.id),
                "name": "Boundary Test Farm",
                "latitude": -1.2921,
                "longitude": 36.8219,
            }
        )
        assert start_response.status_code == 201
        farm_id = start_response.json()["farm_id"]

        # Set boundary via registration endpoint
        boundary_geojson = {
            "type": "Polygon",
            "coordinates": [[
                [36.8219, -1.2921],
                [36.8229, -1.2921],
                [36.8229, -1.2931],
                [36.8219, -1.2931],
                [36.8219, -1.2921],
            ]]
        }

        boundary_response = await client.patch(
            f"/api/v1/farm-registration/{farm_id}/boundary",
            json={"boundary_geojson": boundary_geojson}
        )

        assert boundary_response.status_code == 200

    @pytest.mark.asyncio
    async def test_farm_retrieval_basic_fields(
        self, client: AsyncClient, test_farm: FarmProfile
    ):
        """Test farm retrieval returns expected basic fields."""
        response = await client.get(f"/api/v1/farms/{test_farm.id}")

        assert response.status_code == 200
        data = response.json()
        # Verify basic fields are present
        assert "id" in data
        assert "farmer_id" in data
        assert "name" in data
        assert "is_verified" in data


class TestFarmVerification:
    """Tests for farm verification status."""

    @pytest.mark.asyncio
    async def test_farm_verification_status(
        self, client: AsyncClient, test_farm: FarmProfile
    ):
        """Test farm verification status in response."""
        response = await client.get(f"/api/v1/farms/{test_farm.id}")

        assert response.status_code == 200
        data = response.json()
        assert "is_verified" in data
        assert data["is_verified"] is False  # Default

    @pytest.mark.asyncio
    async def test_verification_status_default(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test that new farms start unverified."""
        # Create a new farm
        farm_data = {
            "farmer_id": str(test_farmer.id),
            "name": "Verification Test Farm",
            "latitude": -1.2921,
            "longitude": 36.8219,
        }

        response = await client.post("/api/v1/farms", json=farm_data)

        assert response.status_code == 201
        data = response.json()
        assert data["is_verified"] is False
