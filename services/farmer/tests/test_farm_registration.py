"""Tests for farm registration workflow."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.farmer import Farmer, FarmProfile


@pytest.fixture
def sample_farmer_id():
    """Generate a sample farmer ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_farm_id():
    """Generate a sample farm ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_location():
    """Sample location data for Nairobi."""
    return {
        "latitude": -1.286389,
        "longitude": 36.817223,
    }


@pytest.fixture
def sample_boundary():
    """Sample GeoJSON polygon boundary."""
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


class TestFarmRegistrationStart:
    """Tests for starting farm registration."""

    @pytest.mark.asyncio
    async def test_start_registration(self, client: AsyncClient, db_session, sample_location):
        """Test starting a new farm registration."""
        # Create a farmer first
        farmer = Farmer(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            phone_number="+254712345678",
            national_id="12345678",
        )
        db_session.add(farmer)
        await db_session.commit()
        await db_session.refresh(farmer)

        # Start registration
        response = await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(farmer.id),
                "name": "Test Farm",
                "latitude": sample_location["latitude"],
                "longitude": sample_location["longitude"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "started"
        assert data["current_step"] == "location"
        assert "farm_id" in data

    @pytest.mark.asyncio
    async def test_start_registration_invalid_farmer(self, client: AsyncClient, sample_location):
        """Test starting registration with invalid farmer."""
        response = await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(uuid.uuid4()),
                "name": "Test Farm",
                "latitude": sample_location["latitude"],
                "longitude": sample_location["longitude"],
            },
        )
        assert response.status_code == 400


class TestFarmRegistrationStatus:
    """Tests for registration status."""

    @pytest.mark.asyncio
    async def test_get_registration_status(self, client: AsyncClient, db_session, sample_location):
        """Test getting registration status."""
        # Create farmer and farm
        farmer = Farmer(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="Jane",
            last_name="Doe",
            phone_number="+254712345679",
            national_id="12345679",
        )
        db_session.add(farmer)
        await db_session.commit()
        await db_session.refresh(farmer)

        farm = FarmProfile(
            farmer_id=farmer.id,
            name="Status Test Farm",
            latitude=sample_location["latitude"],
            longitude=sample_location["longitude"],
            registration_step="location",
        )
        db_session.add(farm)
        await db_session.commit()
        await db_session.refresh(farm)

        response = await client.get(f"/api/v1/farm-registration/{farm.id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["farm_id"] == str(farm.id)
        assert data["current_step"] == "location"
        assert "steps" in data

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, client: AsyncClient):
        """Test getting status for non-existent farm."""
        response = await client.get(f"/api/v1/farm-registration/{uuid.uuid4()}/status")
        assert response.status_code == 404


class TestFarmRegistrationBoundary:
    """Tests for boundary operations."""

    @pytest.mark.asyncio
    async def test_set_boundary(self, client: AsyncClient, db_session, sample_location, sample_boundary):
        """Test setting farm boundary."""
        # Create farmer and farm
        farmer = Farmer(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="Bob",
            last_name="Smith",
            phone_number="+254712345680",
            national_id="12345680",
        )
        db_session.add(farmer)
        await db_session.commit()
        await db_session.refresh(farmer)

        farm = FarmProfile(
            farmer_id=farmer.id,
            name="Boundary Test Farm",
            latitude=sample_location["latitude"],
            longitude=sample_location["longitude"],
            registration_step="location",
        )
        db_session.add(farm)
        await db_session.commit()
        await db_session.refresh(farm)

        response = await client.patch(
            f"/api/v1/farm-registration/{farm.id}/boundary",
            json={"boundary_geojson": sample_boundary},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert "area" in data["message"].lower() or "boundary" in data["message"].lower()


class TestFarmRegistrationLandDetails:
    """Tests for land details operations."""

    @pytest.mark.asyncio
    async def test_update_land_details(self, client: AsyncClient, db_session, sample_location):
        """Test updating land details."""
        # Create farmer and farm
        farmer = Farmer(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="Alice",
            last_name="Johnson",
            phone_number="+254712345681",
            national_id="12345681",
        )
        db_session.add(farmer)
        await db_session.commit()
        await db_session.refresh(farmer)

        farm = FarmProfile(
            farmer_id=farmer.id,
            name="Land Details Test Farm",
            latitude=sample_location["latitude"],
            longitude=sample_location["longitude"],
            registration_step="boundary",
        )
        db_session.add(farm)
        await db_session.commit()
        await db_session.refresh(farm)

        response = await client.patch(
            f"/api/v1/farm-registration/{farm.id}/land-details",
            json={
                "total_acreage": 5.5,
                "cultivable_acreage": 4.0,
                "ownership_type": "owned",
                "land_reference_number": "LR12345",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"


class TestFarmDocuments:
    """Tests for farm documents."""

    @pytest.mark.asyncio
    async def test_add_document(self, client: AsyncClient, db_session, sample_location):
        """Test adding a document to farm."""
        # Create farmer and farm
        farmer = Farmer(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="Doc",
            last_name="Test",
            phone_number="+254712345682",
            national_id="12345682",
        )
        db_session.add(farmer)
        await db_session.commit()
        await db_session.refresh(farmer)

        farm = FarmProfile(
            farmer_id=farmer.id,
            name="Document Test Farm",
            latitude=sample_location["latitude"],
            longitude=sample_location["longitude"],
        )
        db_session.add(farm)
        await db_session.commit()
        await db_session.refresh(farm)

        response = await client.post(
            f"/api/v1/farm-registration/{farm.id}/documents",
            json={
                "document_type": "land_title",
                "document_number": "TITLE-001",
                "file_url": "https://storage.example.com/docs/title.pdf",
                "file_name": "land_title.pdf",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["document_type"] == "land_title"
        assert data["file_name"] == "land_title.pdf"

    @pytest.mark.asyncio
    async def test_list_documents(self, client: AsyncClient, db_session, sample_location):
        """Test listing farm documents."""
        # Create farmer and farm
        farmer = Farmer(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="List",
            last_name="Docs",
            phone_number="+254712345683",
            national_id="12345683",
        )
        db_session.add(farmer)
        await db_session.commit()
        await db_session.refresh(farmer)

        farm = FarmProfile(
            farmer_id=farmer.id,
            name="List Docs Farm",
            latitude=sample_location["latitude"],
            longitude=sample_location["longitude"],
        )
        db_session.add(farm)
        await db_session.commit()
        await db_session.refresh(farm)

        response = await client.get(f"/api/v1/farm-registration/{farm.id}/documents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestFarmAssets:
    """Tests for farm assets."""

    @pytest.mark.asyncio
    async def test_add_asset(self, client: AsyncClient, db_session, sample_location):
        """Test adding an asset to farm."""
        # Create farmer and farm
        farmer = Farmer(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="Asset",
            last_name="Test",
            phone_number="+254712345684",
            national_id="12345684",
        )
        db_session.add(farmer)
        await db_session.commit()
        await db_session.refresh(farmer)

        farm = FarmProfile(
            farmer_id=farmer.id,
            name="Asset Test Farm",
            latitude=sample_location["latitude"],
            longitude=sample_location["longitude"],
        )
        db_session.add(farm)
        await db_session.commit()
        await db_session.refresh(farm)

        response = await client.post(
            f"/api/v1/farm-registration/{farm.id}/assets",
            json={
                "asset_type": "equipment",
                "name": "Tractor",
                "description": "John Deere 5050D",
                "quantity": 1,
                "estimated_value": 1500000.00,
                "condition": "good",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["asset_type"] == "equipment"
        assert data["name"] == "Tractor"


class TestCropRecords:
    """Tests for crop records."""

    @pytest.mark.asyncio
    async def test_add_crop_record(self, client: AsyncClient, db_session, sample_location):
        """Test adding a crop record."""
        # Create farmer and farm
        farmer = Farmer(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="Crop",
            last_name="Test",
            phone_number="+254712345685",
            national_id="12345685",
        )
        db_session.add(farmer)
        await db_session.commit()
        await db_session.refresh(farmer)

        farm = FarmProfile(
            farmer_id=farmer.id,
            name="Crop Test Farm",
            latitude=sample_location["latitude"],
            longitude=sample_location["longitude"],
        )
        db_session.add(farm)
        await db_session.commit()
        await db_session.refresh(farm)

        response = await client.post(
            f"/api/v1/farm-registration/{farm.id}/crops",
            json={
                "crop_name": "Maize",
                "variety": "H614",
                "season": "long_rains",
                "year": 2024,
                "planted_acreage": 2.5,
                "expected_yield_kg": 3000,
                "is_current": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["crop_name"] == "Maize"
        assert data["is_current"] is True


class TestCompleteRegistration:
    """Tests for completing registration."""

    @pytest.mark.asyncio
    async def test_complete_registration(self, client: AsyncClient, db_session, sample_location):
        """Test completing farm registration."""
        # Create farmer and farm with required fields
        farmer = Farmer(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="Complete",
            last_name="Test",
            phone_number="+254712345686",
            national_id="12345686",
        )
        db_session.add(farmer)
        await db_session.commit()
        await db_session.refresh(farmer)

        farm = FarmProfile(
            farmer_id=farmer.id,
            name="Complete Test Farm",
            latitude=sample_location["latitude"],
            longitude=sample_location["longitude"],
            total_acreage=5.0,
            ownership_type="owned",
            registration_step="crop_history",
        )
        db_session.add(farm)
        await db_session.commit()
        await db_session.refresh(farm)

        response = await client.post(f"/api/v1/farm-registration/{farm.id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["registration_complete"] is True
        assert data["current_step"] == "complete"

    @pytest.mark.asyncio
    async def test_complete_registration_missing_fields(self, client: AsyncClient, db_session, sample_location):
        """Test completing registration with missing required fields."""
        # Create farmer and farm without required fields
        farmer = Farmer(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="Incomplete",
            last_name="Test",
            phone_number="+254712345687",
            national_id="12345687",
        )
        db_session.add(farmer)
        await db_session.commit()
        await db_session.refresh(farmer)

        farm = FarmProfile(
            farmer_id=farmer.id,
            name="Incomplete Test Farm",
            latitude=sample_location["latitude"],
            longitude=sample_location["longitude"],
            # Missing total_acreage and ownership_type
        )
        db_session.add(farm)
        await db_session.commit()
        await db_session.refresh(farm)

        response = await client.post(f"/api/v1/farm-registration/{farm.id}/complete")
        assert response.status_code == 400
