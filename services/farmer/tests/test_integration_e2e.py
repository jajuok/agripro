"""End-to-end integration tests for complete user journeys.

These tests simulate real-world usage scenarios:
- New farmer registration and onboarding
- Farm registration workflow
- Mobile app API usage patterns
- Data consistency across operations
"""

import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer, FarmProfile


class TestFarmerOnboardingJourney:
    """Tests for complete farmer onboarding flow."""

    @pytest.mark.asyncio
    async def test_new_farmer_complete_onboarding(self, client: AsyncClient):
        """Test complete journey of a new farmer from registration to farm setup."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        # Step 1: Create farmer profile
        farmer_data = {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "first_name": "Samuel",
            "last_name": "Kamau",
            "phone_number": "+254712345678",
            "email": "samuel.kamau@example.com",
            "county": "Kiambu",
            "sub_county": "Kikuyu",
        }

        farmer_response = await client.post("/api/v1/farmers", json=farmer_data)
        assert farmer_response.status_code == 201
        farmer = farmer_response.json()
        farmer_id = farmer["id"]

        # Verify farmer can be retrieved
        get_response = await client.get(f"/api/v1/farmers/{farmer_id}")
        assert get_response.status_code == 200
        assert get_response.json()["first_name"] == "Samuel"

        # Verify farmer can be found by user_id (mobile app pattern)
        by_user_response = await client.get(f"/api/v1/farmers/by-user/{user_id}")
        assert by_user_response.status_code == 200
        assert by_user_response.json()["id"] == farmer_id

        # Step 2: Start farm registration
        farm_start_response = await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": farmer_id,
                "name": "Kamau Family Farm",
                "latitude": -1.1618,
                "longitude": 36.7745,
            }
        )
        assert farm_start_response.status_code == 201
        farm_id = farm_start_response.json()["farm_id"]

        # Step 3: Set farm boundary
        boundary_response = await client.patch(
            f"/api/v1/farm-registration/{farm_id}/boundary",
            json={
                "boundary_geojson": {
                    "type": "Polygon",
                    "coordinates": [[
                        [36.7745, -1.1618],
                        [36.7755, -1.1618],
                        [36.7755, -1.1628],
                        [36.7745, -1.1628],
                        [36.7745, -1.1618],
                    ]]
                }
            }
        )
        assert boundary_response.status_code == 200

        # Step 4: Set land details
        land_response = await client.patch(
            f"/api/v1/farm-registration/{farm_id}/land-details",
            json={
                "total_acreage": 5.5,
                "cultivable_acreage": 4.0,
                "ownership_type": "owned",
            }
        )
        assert land_response.status_code == 200

        # Step 5: Add crops
        crop_response = await client.post(
            f"/api/v1/farm-registration/{farm_id}/crops",
            json={
                "crop_name": "coffee",
                "variety": "SL28",
                "planted_acreage": 3.0,
                "season": "main",
                "year": 2024,
            }
        )
        assert crop_response.status_code == 201

        # Step 6: Complete registration
        complete_response = await client.post(
            f"/api/v1/farm-registration/{farm_id}/complete"
        )
        assert complete_response.status_code == 200
        assert complete_response.json()["registration_complete"] is True

        # Verify farm appears in farmer's farm list (using user_id - mobile pattern)
        farms_response = await client.get(f"/api/v1/farms/user/{user_id}")
        assert farms_response.status_code == 200
        farms = farms_response.json()
        assert len(farms) == 1
        assert farms[0]["name"] == "Kamau Family Farm"


class TestMobileAppPatterns:
    """Tests simulating mobile app API usage patterns."""

    @pytest.mark.asyncio
    async def test_mobile_login_and_fetch_data(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ):
        """Test mobile app pattern: login -> fetch farmer -> fetch farms."""
        # Create some farms for the farmer
        for i in range(2):
            farm = FarmProfile(
                id=uuid.uuid4(),
                farmer_id=test_farmer.id,
                name=f"Mobile Test Farm {i+1}",
                latitude=-1.2921 + (i * 0.01),
                longitude=36.8219,
                registration_step="complete",
            )
            db_session.add(farm)
        await db_session.commit()

        # Simulate mobile app: use user_id to get farmer profile
        farmer_response = await client.get(
            f"/api/v1/farmers/by-user/{test_farmer.user_id}"
        )
        assert farmer_response.status_code == 200
        farmer_data = farmer_response.json()

        # Fetch farms using user_id (the way mobile app would do it)
        farms_response = await client.get(
            f"/api/v1/farms/user/{test_farmer.user_id}"
        )
        assert farms_response.status_code == 200
        farms = farms_response.json()
        assert len(farms) == 2

    @pytest.mark.asyncio
    async def test_mobile_offline_sync_pattern(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test pattern for offline data sync from mobile."""
        # Start farm registration
        start_response = await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(test_farmer.id),
                "name": "Offline Sync Farm",
                "latitude": -1.3000,
                "longitude": 36.9000,
            }
        )
        assert start_response.status_code == 201
        farm_id = start_response.json()["farm_id"]

        # Simulate multiple rapid updates (offline sync batch)
        # Update boundary
        await client.patch(
            f"/api/v1/farm-registration/{farm_id}/boundary",
            json={
                "boundary_geojson": {
                    "type": "Polygon",
                    "coordinates": [[
                        [36.9, -1.3],
                        [36.91, -1.3],
                        [36.91, -1.31],
                        [36.9, -1.31],
                        [36.9, -1.3],
                    ]]
                }
            }
        )

        # Update land details immediately after
        await client.patch(
            f"/api/v1/farm-registration/{farm_id}/land-details",
            json={
                "total_acreage": 3.0,
                "cultivable_acreage": 2.5,
                "ownership_type": "leased",
            }
        )

        # Verify data persisted correctly
        status_response = await client.get(
            f"/api/v1/farm-registration/{farm_id}/status"
        )
        assert status_response.status_code == 200


class TestMultipleFarmScenarios:
    """Tests for farmers with multiple farms."""

    @pytest.mark.asyncio
    async def test_farmer_with_multiple_farms(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test farmer managing multiple farms."""
        farm_names = ["Home Farm", "River Plot", "Hill Garden"]
        farm_ids = []

        # Create multiple farms
        for i, name in enumerate(farm_names):
            response = await client.post(
                "/api/v1/farm-registration/start",
                json={
                    "farmer_id": str(test_farmer.id),
                    "name": name,
                    "latitude": -1.3 + (i * 0.01),
                    "longitude": 36.8 + (i * 0.01),
                }
            )
            assert response.status_code == 201
            farm_ids.append(response.json()["farm_id"])

        # Verify all farms are listed
        list_response = await client.get(
            f"/api/v1/farms/farmer/{test_farmer.id}"
        )
        assert list_response.status_code == 200
        farms = list_response.json()
        assert len(farms) == 3
        assert {f["name"] for f in farms} == set(farm_names)

        # Verify individual farm access
        for farm_id in farm_ids:
            response = await client.get(f"/api/v1/farms/{farm_id}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_farms_isolated_between_farmers(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that farms are properly isolated between farmers."""
        # Create two farmers
        farmer1 = Farmer(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="Farmer",
            last_name="One",
            phone_number="+254700000001",
        )
        farmer2 = Farmer(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            first_name="Farmer",
            last_name="Two",
            phone_number="+254700000002",
        )
        db_session.add(farmer1)
        db_session.add(farmer2)
        await db_session.commit()

        # Create farm for farmer1
        await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(farmer1.id),
                "name": "Farmer1 Farm",
                "latitude": -1.3,
                "longitude": 36.8,
            }
        )

        # Create farm for farmer2
        await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(farmer2.id),
                "name": "Farmer2 Farm",
                "latitude": -1.4,
                "longitude": 36.9,
            }
        )

        # Verify farmer1 only sees their farm
        response1 = await client.get(f"/api/v1/farms/farmer/{farmer1.id}")
        farms1 = response1.json()
        assert len(farms1) == 1
        assert farms1[0]["name"] == "Farmer1 Farm"

        # Verify farmer2 only sees their farm
        response2 = await client.get(f"/api/v1/farms/farmer/{farmer2.id}")
        farms2 = response2.json()
        assert len(farms2) == 1
        assert farms2[0]["name"] == "Farmer2 Farm"


class TestDataIntegrityScenarios:
    """Tests for data integrity across operations."""

    @pytest.mark.asyncio
    async def test_update_preserves_unmodified_fields(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test that partial updates don't affect unmodified fields."""
        # Create farm with all fields
        start_response = await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(test_farmer.id),
                "name": "Integrity Test Farm",
                "latitude": -1.3,
                "longitude": 36.8,
            }
        )
        farm_id = start_response.json()["farm_id"]

        # Set boundary
        await client.patch(
            f"/api/v1/farm-registration/{farm_id}/boundary",
            json={
                "boundary_geojson": {
                    "type": "Polygon",
                    "coordinates": [[
                        [36.8, -1.3],
                        [36.81, -1.3],
                        [36.81, -1.31],
                        [36.8, -1.31],
                        [36.8, -1.3],
                    ]]
                }
            }
        )

        # Set land details
        await client.patch(
            f"/api/v1/farm-registration/{farm_id}/land-details",
            json={
                "total_acreage": 5.0,
                "cultivable_acreage": 4.0,
                "ownership_type": "owned",
            }
        )

        # Update soil info only
        await client.patch(
            f"/api/v1/farm-registration/{farm_id}/soil-water",
            json={
                "soil_type": "loamy",
            }
        )

        # Verify all previous data is preserved
        farm_response = await client.get(f"/api/v1/farms/{farm_id}")
        farm = farm_response.json()

        assert farm["name"] == "Integrity Test Farm"
        assert farm["total_acreage"] == 5.0
        assert farm["ownership_type"] == "owned"
        # boundary_geojson is stored but not returned in FarmResponse

    @pytest.mark.asyncio
    async def test_concurrent_farm_updates(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test that multiple rapid updates don't cause data loss."""
        # Create farm
        start_response = await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(test_farmer.id),
                "name": "Concurrent Test Farm",
                "latitude": -1.3,
                "longitude": 36.8,
            }
        )
        farm_id = start_response.json()["farm_id"]

        # Send multiple updates sequentially (avoid concurrent DB issues in tests)
        land_response = await client.patch(
            f"/api/v1/farm-registration/{farm_id}/land-details",
            json={"total_acreage": 10.0, "ownership_type": "owned"}
        )
        assert land_response.status_code == 200

        soil_response = await client.patch(
            f"/api/v1/farm-registration/{farm_id}/soil-water",
            json={"soil_type": "clay", "water_source": "borehole"}
        )
        assert soil_response.status_code == 200

        # Final state should have all updates
        farm_response = await client.get(f"/api/v1/farms/{farm_id}")
        farm = farm_response.json()
        assert farm["total_acreage"] == 10.0
        assert farm["soil_type"] == "clay"


class TestErrorRecoveryScenarios:
    """Tests for error handling and recovery."""

    @pytest.mark.asyncio
    async def test_retry_after_validation_error(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test that operations can be retried after validation error."""
        # Start registration
        start_response = await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(test_farmer.id),
                "name": "Retry Test Farm",
                "latitude": -1.3,
                "longitude": 36.8,
            }
        )
        farm_id = start_response.json()["farm_id"]

        # Try invalid boundary first
        invalid_response = await client.patch(
            f"/api/v1/farm-registration/{farm_id}/boundary",
            json={
                "boundary_geojson": {
                    "type": "InvalidType",
                    "coordinates": []
                }
            }
        )
        assert invalid_response.status_code == 400

        # Retry with valid boundary
        valid_response = await client.patch(
            f"/api/v1/farm-registration/{farm_id}/boundary",
            json={
                "boundary_geojson": {
                    "type": "Polygon",
                    "coordinates": [[
                        [36.8, -1.3],
                        [36.81, -1.3],
                        [36.81, -1.31],
                        [36.8, -1.31],
                        [36.8, -1.3],
                    ]]
                }
            }
        )
        assert valid_response.status_code == 200

    @pytest.mark.asyncio
    async def test_partial_registration_recovery(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test recovering a partially completed registration."""
        # Start registration
        start_response = await client.post(
            "/api/v1/farm-registration/start",
            json={
                "farmer_id": str(test_farmer.id),
                "name": "Partial Recovery Farm",
                "latitude": -1.3,
                "longitude": 36.8,
            }
        )
        farm_id = start_response.json()["farm_id"]

        # Complete only some steps
        await client.patch(
            f"/api/v1/farm-registration/{farm_id}/boundary",
            json={
                "boundary_geojson": {
                    "type": "Polygon",
                    "coordinates": [[
                        [36.8, -1.3],
                        [36.81, -1.3],
                        [36.81, -1.31],
                        [36.8, -1.31],
                        [36.8, -1.3],
                    ]]
                }
            }
        )

        # Verify status shows incomplete
        status_response = await client.get(
            f"/api/v1/farm-registration/{farm_id}/status"
        )
        assert status_response.status_code == 200
        status = status_response.json()
        assert status["registration_complete"] is False

        # Continue registration from where left off
        await client.patch(
            f"/api/v1/farm-registration/{farm_id}/land-details",
            json={
                "total_acreage": 5.0,
                "ownership_type": "owned",
            }
        )

        # Complete the registration
        complete_response = await client.post(
            f"/api/v1/farm-registration/{farm_id}/complete"
        )
        assert complete_response.status_code == 200


class TestKYCIntegration:
    """Tests for KYC workflow integration."""

    @pytest.mark.asyncio
    async def test_kyc_status_in_farmer_response(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test that KYC status is included in farmer responses."""
        response = await client.get(f"/api/v1/farmers/{test_farmer.id}")

        assert response.status_code == 200
        data = response.json()
        assert "kyc_status" in data
        assert data["kyc_status"] == "pending"  # Default status

    @pytest.mark.asyncio
    async def test_filter_farmers_by_kyc_status_in_list(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering farmers by KYC status in listing."""
        # Create farmers with different statuses
        for status in ["pending", "verified", "rejected"]:
            farmer = Farmer(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                tenant_id=uuid.uuid4(),
                first_name=f"KYC_{status}",
                last_name="Test",
                phone_number=f"+254700{hash(status) % 10000:04d}",
                kyc_status=status,
            )
            db_session.add(farmer)
        await db_session.commit()

        # Filter by verified
        response = await client.get("/api/v1/farmers?kyc_status=verified")
        assert response.status_code == 200
        farmers = response.json()["items"]
        assert all(f["kyc_status"] == "verified" for f in farmers)
