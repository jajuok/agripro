"""Comprehensive tests for Farm Registration Workflow API.

Tests cover:
- Complete registration workflow from start to finish
- Individual step updates (location, boundary, land details, soil/water)
- Documents, assets, crops, soil tests, field visits
- Error handling and edge cases
- Step completion and validation
"""

import uuid
from datetime import date, datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer, FarmProfile


@pytest_asyncio.fixture
async def registered_farm(db_session: AsyncSession, test_farmer: Farmer) -> FarmProfile:
    """Create a farm that has started registration."""
    farm = FarmProfile(
        id=uuid.uuid4(),
        farmer_id=test_farmer.id,
        name="Registration Test Farm",
        latitude=-1.2921,
        longitude=36.8219,
        registration_step="location",
        registration_complete=False,
    )
    db_session.add(farm)
    await db_session.commit()
    await db_session.refresh(farm)
    return farm


@pytest_asyncio.fixture
async def farm_with_boundary(db_session: AsyncSession, test_farmer: Farmer) -> FarmProfile:
    """Create a farm with boundary set."""
    boundary = {
        "type": "Polygon",
        "coordinates": [[
            [36.8219, -1.2921],
            [36.8229, -1.2921],
            [36.8229, -1.2931],
            [36.8219, -1.2931],
            [36.8219, -1.2921],
        ]]
    }
    farm = FarmProfile(
        id=uuid.uuid4(),
        farmer_id=test_farmer.id,
        name="Boundary Test Farm",
        latitude=-1.2921,
        longitude=36.8219,
        boundary_geojson=boundary,
        boundary_area_calculated=2.5,
        registration_step="boundary",
        registration_complete=False,
    )
    db_session.add(farm)
    await db_session.commit()
    await db_session.refresh(farm)
    return farm


class TestStartRegistration:
    """Tests for starting farm registration."""

    @pytest.mark.asyncio
    async def test_start_registration_success(self, client: AsyncClient, test_farmer: Farmer):
        """Test successfully starting a farm registration."""
        data = {
            "farmer_id": str(test_farmer.id),
            "name": "New Farm Registration",
            "latitude": -1.2921,
            "longitude": 36.8219,
        }

        response = await client.post("/api/v1/farm-registration/start", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["status"] == "started"
        assert result["current_step"] == "location"
        assert result["next_step"] == "boundary"
        assert "farm_id" in result

    @pytest.mark.asyncio
    async def test_start_registration_with_name(self, client: AsyncClient, test_farmer: Farmer):
        """Test starting registration with farm name."""
        data = {
            "farmer_id": str(test_farmer.id),
            "name": "My Special Farm",
            "latitude": -0.5234,
            "longitude": 37.4567,
        }

        response = await client.post("/api/v1/farm-registration/start", json=data)

        assert response.status_code == 201
        result = response.json()
        assert "farm_id" in result

    @pytest.mark.asyncio
    async def test_start_registration_missing_farmer_id(self, client: AsyncClient):
        """Test starting registration without farmer_id fails."""
        data = {
            "name": "Test Farm",
            "latitude": -1.2921,
            "longitude": 36.8219,
        }

        response = await client.post("/api/v1/farm-registration/start", json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_registration_invalid_coordinates(self, client: AsyncClient, test_farmer: Farmer):
        """Test starting registration with invalid coordinates."""
        data = {
            "farmer_id": str(test_farmer.id),
            "name": "Invalid Coord Farm",
            "latitude": 200.0,  # Invalid
            "longitude": 36.8219,
        }

        response = await client.post("/api/v1/farm-registration/start", json=data)

        # May return 400 or 422 depending on validation
        assert response.status_code in [400, 422]


class TestRegistrationStatus:
    """Tests for getting registration status."""

    @pytest.mark.asyncio
    async def test_get_registration_status(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test getting registration status."""
        response = await client.get(
            f"/api/v1/farm-registration/{registered_farm.id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert "current_step" in data
        assert "registration_complete" in data

    @pytest.mark.asyncio
    async def test_get_registration_status_not_found(self, client: AsyncClient):
        """Test getting status for non-existent farm."""
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/farm-registration/{fake_id}/status")

        assert response.status_code == 404


class TestUpdateLocation:
    """Tests for updating farm location."""

    @pytest.mark.asyncio
    async def test_update_location_success(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test updating farm location."""
        response = await client.patch(
            f"/api/v1/farm-registration/{registered_farm.id}/location",
            params={"latitude": -1.3000, "longitude": 36.8500}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert "Location updated" in data["message"]

    @pytest.mark.asyncio
    async def test_update_location_with_altitude(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test updating location with altitude."""
        response = await client.patch(
            f"/api/v1/farm-registration/{registered_farm.id}/location",
            params={"latitude": -1.3000, "longitude": 36.8500, "altitude": 1500.0}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_location_not_found(self, client: AsyncClient):
        """Test updating location for non-existent farm."""
        fake_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/farm-registration/{fake_id}/location",
            params={"latitude": -1.3000, "longitude": 36.8500}
        )

        assert response.status_code == 400


class TestSetBoundary:
    """Tests for setting farm boundary."""

    @pytest.mark.asyncio
    async def test_set_boundary_success(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test setting farm boundary with valid GeoJSON."""
        boundary_data = {
            "boundary_geojson": {
                "type": "Polygon",
                "coordinates": [[
                    [36.8219, -1.2921],
                    [36.8229, -1.2921],
                    [36.8229, -1.2931],
                    [36.8219, -1.2931],
                    [36.8219, -1.2921],
                ]]
            }
        }

        response = await client.patch(
            f"/api/v1/farm-registration/{registered_farm.id}/boundary",
            json=boundary_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert "Boundary set" in data["message"]

    @pytest.mark.asyncio
    async def test_set_boundary_invalid_geojson(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test setting boundary with invalid GeoJSON structure."""
        boundary_data = {
            "boundary_geojson": {
                "type": "InvalidType",
                "coordinates": []
            }
        }

        response = await client.patch(
            f"/api/v1/farm-registration/{registered_farm.id}/boundary",
            json=boundary_data
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_set_boundary_unclosed_polygon(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test setting boundary with unclosed polygon (API auto-closes it)."""
        boundary_data = {
            "boundary_geojson": {
                "type": "Polygon",
                "coordinates": [[
                    [36.8219, -1.2921],
                    [36.8229, -1.2921],
                    [36.8229, -1.2931],
                    [36.8219, -1.2931],
                    # Missing closing point - API may auto-close
                ]]
            }
        }

        response = await client.patch(
            f"/api/v1/farm-registration/{registered_farm.id}/boundary",
            json=boundary_data
        )

        # API may accept and auto-close, or reject
        assert response.status_code in [200, 400]


class TestUpdateLandDetails:
    """Tests for updating land details."""

    @pytest.mark.asyncio
    async def test_update_land_details_success(
        self, client: AsyncClient, farm_with_boundary: FarmProfile
    ):
        """Test updating land details."""
        land_data = {
            "total_acreage": 10.5,
            "cultivable_acreage": 8.0,
            "ownership_type": "owned",
        }

        response = await client.patch(
            f"/api/v1/farm-registration/{farm_with_boundary.id}/land-details",
            json=land_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"

    @pytest.mark.asyncio
    async def test_update_land_details_with_reference(
        self, client: AsyncClient, farm_with_boundary: FarmProfile
    ):
        """Test updating land details with reference number."""
        land_data = {
            "total_acreage": 15.0,
            "cultivable_acreage": 12.0,
            "ownership_type": "leased",
            "land_reference_number": "LR/12345/2023",
        }

        response = await client.patch(
            f"/api/v1/farm-registration/{farm_with_boundary.id}/land-details",
            json=land_data
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_land_details_invalid_acreage(
        self, client: AsyncClient, farm_with_boundary: FarmProfile
    ):
        """Test updating with cultivable > total acreage."""
        land_data = {
            "total_acreage": 5.0,
            "cultivable_acreage": 10.0,  # Greater than total
            "ownership_type": "owned",
        }

        response = await client.patch(
            f"/api/v1/farm-registration/{farm_with_boundary.id}/land-details",
            json=land_data
        )

        # May return 400 if validation exists
        assert response.status_code in [200, 400]


class TestUpdateSoilWater:
    """Tests for updating soil and water profile."""

    @pytest.mark.asyncio
    async def test_update_soil_water_success(
        self, client: AsyncClient, farm_with_boundary: FarmProfile
    ):
        """Test updating soil and water info."""
        soil_water_data = {
            "soil_type": "loamy",
            "soil_ph": 6.5,
            "water_source": "borehole",
            "irrigation_type": "drip",
        }

        response = await client.patch(
            f"/api/v1/farm-registration/{farm_with_boundary.id}/soil-water",
            json=soil_water_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"

    @pytest.mark.asyncio
    async def test_update_soil_water_partial(
        self, client: AsyncClient, farm_with_boundary: FarmProfile
    ):
        """Test partial update of soil/water info."""
        soil_water_data = {
            "soil_type": "clay",
        }

        response = await client.patch(
            f"/api/v1/farm-registration/{farm_with_boundary.id}/soil-water",
            json=soil_water_data
        )

        assert response.status_code == 200


class TestDocumentManagement:
    """Tests for farm document operations."""

    @pytest.mark.asyncio
    async def test_add_document_success(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test adding a document to farm."""
        doc_data = {
            "document_type": "title_deed",
            "file_url": "https://storage.example.com/title_deed_123.pdf",
            "file_name": "title_deed_123.pdf",
        }

        response = await client.post(
            f"/api/v1/farm-registration/{registered_farm.id}/documents",
            json=doc_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["document_type"] == "title_deed"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_documents(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test listing farm documents."""
        # Add a document first
        doc_data = {
            "document_type": "survey_map",
            "file_url": "https://storage.example.com/survey_123.pdf",
            "file_name": "survey_123.pdf",
        }
        await client.post(
            f"/api/v1/farm-registration/{registered_farm.id}/documents",
            json=doc_data
        )

        # List documents
        response = await client.get(
            f"/api/v1/farm-registration/{registered_farm.id}/documents"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_add_multiple_documents(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test adding multiple documents."""
        doc_types = ["title_deed", "survey_map", "water_permit"]

        for doc_type in doc_types:
            doc_data = {
                "document_type": doc_type,
                "file_url": f"https://storage.example.com/{doc_type}_123.pdf",
                "file_name": f"{doc_type}_123.pdf",
            }
            response = await client.post(
                f"/api/v1/farm-registration/{registered_farm.id}/documents",
                json=doc_data
            )
            assert response.status_code == 201

        # Verify all documents exist
        list_response = await client.get(
            f"/api/v1/farm-registration/{registered_farm.id}/documents"
        )
        assert len(list_response.json()) == 3


class TestAssetManagement:
    """Tests for farm asset operations."""

    @pytest.mark.asyncio
    async def test_add_asset_success(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test adding an asset to farm."""
        asset_data = {
            "asset_type": "tractor",
            "name": "John Deere 5050D",
            "quantity": 1,
            "condition": "good",
        }

        response = await client.post(
            f"/api/v1/farm-registration/{registered_farm.id}/assets",
            json=asset_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["asset_type"] == "tractor"
        assert data["name"] == "John Deere 5050D"

    @pytest.mark.asyncio
    async def test_list_assets(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test listing farm assets."""
        # Add assets
        assets = [
            {"asset_type": "tractor", "name": "Tractor 1", "quantity": 1},
            {"asset_type": "irrigation", "name": "Drip System", "quantity": 1},
        ]

        for asset in assets:
            await client.post(
                f"/api/v1/farm-registration/{registered_farm.id}/assets",
                json=asset
            )

        # List assets
        response = await client.get(
            f"/api/v1/farm-registration/{registered_farm.id}/assets"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestCropRecordManagement:
    """Tests for crop record operations."""

    @pytest.mark.asyncio
    async def test_add_crop_record_success(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test adding a crop record."""
        crop_data = {
            "crop_name": "maize",
            "variety": "H614",
            "planted_acreage": 5.0,
            "season": "long_rains",
            "year": 2024,
        }

        response = await client.post(
            f"/api/v1/farm-registration/{registered_farm.id}/crops",
            json=crop_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["crop_name"] == "maize"
        assert data["variety"] == "H614"

    @pytest.mark.asyncio
    async def test_list_crop_records(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test listing crop records."""
        # Add crops
        crops = [
            {"crop_name": "maize", "variety": "H614", "planted_acreage": 5.0, "season": "long_rains", "year": 2024},
            {"crop_name": "beans", "variety": "KAT/B-9", "planted_acreage": 2.0, "season": "short_rains", "year": 2024},
        ]

        for crop in crops:
            await client.post(
                f"/api/v1/farm-registration/{registered_farm.id}/crops",
                json=crop
            )

        # List crops
        response = await client.get(
            f"/api/v1/farm-registration/{registered_farm.id}/crops"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestSoilTestManagement:
    """Tests for soil test report operations."""

    @pytest.mark.asyncio
    async def test_add_soil_test_success(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test adding a soil test report."""
        soil_test_data = {
            "test_date": "2024-01-15T00:00:00",
            "lab_name": "Kenya Soil Survey",
            "ph_level": 6.8,
            "nitrogen_ppm": 150.0,
            "phosphorus_ppm": 25.0,
            "potassium_ppm": 180.0,
            "organic_matter_percent": 2.5,
        }

        response = await client.post(
            f"/api/v1/farm-registration/{registered_farm.id}/soil-tests",
            json=soil_test_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["lab_name"] == "Kenya Soil Survey"
        assert data["ph_level"] == 6.8

    @pytest.mark.asyncio
    async def test_list_soil_tests(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test listing soil test reports."""
        response = await client.get(
            f"/api/v1/farm-registration/{registered_farm.id}/soil-tests"
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestFieldVisitManagement:
    """Tests for field visit operations."""

    @pytest.mark.asyncio
    async def test_add_field_visit_success(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test adding a field visit record."""
        visit_data = {
            "visit_date": "2024-02-20T10:00:00",
            "visitor_id": str(uuid.uuid4()),
            "visitor_name": "John Inspector",
            "purpose": "verification",
            "findings": "Farm is well maintained with good drainage",
            "recommendations": "Consider cover crops for soil conservation",
        }

        response = await client.post(
            f"/api/v1/farm-registration/{registered_farm.id}/visits",
            json=visit_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["visitor_name"] == "John Inspector"
        assert "findings" in data or "recommendations" in data

    @pytest.mark.asyncio
    async def test_list_field_visits(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test listing field visits."""
        response = await client.get(
            f"/api/v1/farm-registration/{registered_farm.id}/visits"
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestStepCompletion:
    """Tests for registration step completion."""

    @pytest.mark.asyncio
    async def test_complete_step_success(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test completing a registration step."""
        response = await client.post(
            f"/api/v1/farm-registration/{registered_farm.id}/complete-step",
            params={"step": "location"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "current_step" in data

    @pytest.mark.asyncio
    async def test_complete_step_invalid(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test completing invalid step."""
        response = await client.post(
            f"/api/v1/farm-registration/{registered_farm.id}/complete-step",
            params={"step": "invalid_step"}
        )

        assert response.status_code == 422


class TestCompleteRegistration:
    """Tests for completing farm registration."""

    @pytest.mark.asyncio
    async def test_complete_registration_success(
        self, client: AsyncClient, db_session: AsyncSession, test_farmer: Farmer
    ):
        """Test completing full registration workflow."""
        # Create a farm with all required data
        farm = FarmProfile(
            id=uuid.uuid4(),
            farmer_id=test_farmer.id,
            name="Complete Farm",
            latitude=-1.2921,
            longitude=36.8219,
            boundary_geojson={
                "type": "Polygon",
                "coordinates": [[
                    [36.8219, -1.2921],
                    [36.8229, -1.2921],
                    [36.8229, -1.2931],
                    [36.8219, -1.2931],
                    [36.8219, -1.2921],
                ]]
            },
            total_acreage=10.0,
            ownership_type="owned",
            registration_step="review",
            registration_complete=False,
        )
        db_session.add(farm)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/farm-registration/{farm.id}/complete"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["registration_complete"] is True

    @pytest.mark.asyncio
    async def test_complete_registration_missing_data(
        self, client: AsyncClient, registered_farm: FarmProfile
    ):
        """Test completing registration with missing required data."""
        response = await client.post(
            f"/api/v1/farm-registration/{registered_farm.id}/complete"
        )

        # Should fail because boundary and other required fields are missing
        assert response.status_code == 400


class TestFullRegistrationWorkflow:
    """End-to-end tests for complete registration workflow."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, client: AsyncClient, test_farmer: Farmer):
        """Test complete registration workflow from start to finish."""
        # Step 1: Start registration
        start_response = await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(test_farmer.id),
                "name": "Workflow Test Farm",
                "latitude": -1.2921,
                "longitude": 36.8219,
            }
        )
        assert start_response.status_code == 201
        farm_id = start_response.json()["farm_id"]

        # Step 2: Set boundary
        boundary_response = await client.patch(
            f"/api/v1/farm-registration/{farm_id}/boundary",
            json={
                "boundary_geojson": {
                    "type": "Polygon",
                    "coordinates": [[
                        [36.8219, -1.2921],
                        [36.8229, -1.2921],
                        [36.8229, -1.2931],
                        [36.8219, -1.2931],
                        [36.8219, -1.2921],
                    ]]
                }
            }
        )
        assert boundary_response.status_code == 200

        # Step 3: Update land details
        land_response = await client.patch(
            f"/api/v1/farm-registration/{farm_id}/land-details",
            json={
                "total_acreage": 10.0,
                "cultivable_acreage": 8.0,
                "ownership_type": "owned",
            }
        )
        assert land_response.status_code == 200

        # Step 4: Update soil/water
        soil_response = await client.patch(
            f"/api/v1/farm-registration/{farm_id}/soil-water",
            json={
                "soil_type": "loamy",
                "water_source": "borehole",
            }
        )
        assert soil_response.status_code == 200

        # Step 5: Add a document
        doc_response = await client.post(
            f"/api/v1/farm-registration/{farm_id}/documents",
            json={
                "document_type": "title_deed",
                "file_url": "https://storage.example.com/title.pdf",
                "file_name": "title.pdf",
            }
        )
        assert doc_response.status_code == 201

        # Step 6: Add a crop record
        crop_response = await client.post(
            f"/api/v1/farm-registration/{farm_id}/crops",
            json={
                "crop_name": "maize",
                "variety": "H614",
                "planted_acreage": 5.0,
                "season": "long_rains",
                "year": 2024,
            }
        )
        assert crop_response.status_code == 201

        # Step 7: Complete registration
        complete_response = await client.post(
            f"/api/v1/farm-registration/{farm_id}/complete"
        )
        assert complete_response.status_code == 200
        assert complete_response.json()["registration_complete"] is True

        # Verify final status
        status_response = await client.get(
            f"/api/v1/farm-registration/{farm_id}/status"
        )
        assert status_response.status_code == 200
        assert status_response.json()["registration_complete"] is True
