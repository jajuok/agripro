"""Comprehensive tests for Farmer API endpoints.

Tests cover:
- Farmer CRUD operations
- Get farmer by user_id endpoint
- Pagination and filtering
- Error handling and edge cases
"""

import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer


class TestFarmerCreation:
    """Tests for farmer creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_farmer_success(self, client: AsyncClient):
        """Test successful farmer creation with all required fields."""
        farmer_data = {
            "user_id": str(uuid.uuid4()),
            "tenant_id": str(uuid.uuid4()),
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+254700000000",
        }

        response = await client.post("/api/v1/farmers", json=farmer_data)

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["phone_number"] == "+254700000000"
        assert "id" in data
        assert data["kyc_status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_farmer_with_all_fields(self, client: AsyncClient):
        """Test farmer creation with all optional fields."""
        farmer_data = {
            "user_id": str(uuid.uuid4()),
            "tenant_id": str(uuid.uuid4()),
            "first_name": "Jane",
            "last_name": "Smith",
            "phone_number": "+254700000001",
            "email": "jane.smith@example.com",
            "national_id": "12345678",
            "county": "Nairobi",
            "sub_county": "Westlands",
            "ward": "Parklands",
            "village": "Parklands Estate",
            "gender": "female",
            "address": "123 Main Street",
        }

        response = await client.post("/api/v1/farmers", json=farmer_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "jane.smith@example.com"
        assert data["national_id"] == "12345678"
        assert data["county"] == "Nairobi"
        assert data["sub_county"] == "Westlands"

    @pytest.mark.asyncio
    async def test_create_farmer_missing_required_fields(self, client: AsyncClient):
        """Test farmer creation fails without required fields."""
        farmer_data = {
            "first_name": "John",
            # Missing user_id, tenant_id, last_name, phone_number
        }

        response = await client.post("/api/v1/farmers", json=farmer_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_farmer_invalid_uuid(self, client: AsyncClient):
        """Test farmer creation fails with invalid UUID."""
        farmer_data = {
            "user_id": "not-a-uuid",
            "tenant_id": str(uuid.uuid4()),
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+254700000000",
        }

        response = await client.post("/api/v1/farmers", json=farmer_data)

        assert response.status_code == 422


class TestFarmerRetrieval:
    """Tests for farmer retrieval endpoints."""

    @pytest.mark.asyncio
    async def test_get_farmer_by_id(self, client: AsyncClient, test_farmer: Farmer):
        """Test getting farmer by ID."""
        response = await client.get(f"/api/v1/farmers/{test_farmer.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_farmer.id)
        assert data["first_name"] == test_farmer.first_name

    @pytest.mark.asyncio
    async def test_get_farmer_not_found(self, client: AsyncClient):
        """Test getting non-existent farmer returns 404."""
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/farmers/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Farmer not found"

    @pytest.mark.asyncio
    async def test_get_farmer_invalid_uuid(self, client: AsyncClient):
        """Test getting farmer with invalid UUID format."""
        response = await client.get("/api/v1/farmers/invalid-uuid")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_farmer_by_user_id(self, client: AsyncClient, test_farmer: Farmer):
        """Test getting farmer by auth user ID."""
        response = await client.get(f"/api/v1/farmers/by-user/{test_farmer.user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_farmer.id)
        assert data["user_id"] == str(test_farmer.user_id)

    @pytest.mark.asyncio
    async def test_get_farmer_by_user_id_not_found(self, client: AsyncClient):
        """Test getting farmer by non-existent user ID returns 404."""
        fake_user_id = uuid.uuid4()
        response = await client.get(f"/api/v1/farmers/by-user/{fake_user_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Farmer not found"


class TestFarmerUpdate:
    """Tests for farmer update endpoint."""

    @pytest.mark.asyncio
    async def test_update_farmer_partial(self, client: AsyncClient, test_farmer: Farmer):
        """Test partial update of farmer."""
        update_data = {
            "first_name": "Updated",
        }

        response = await client.patch(
            f"/api/v1/farmers/{test_farmer.id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        # Unchanged fields should remain
        assert data["last_name"] == test_farmer.last_name

    @pytest.mark.asyncio
    async def test_update_farmer_all_fields(self, client: AsyncClient, test_farmer: Farmer):
        """Test updating all editable farmer fields."""
        update_data = {
            "first_name": "New First",
            "last_name": "New Last",
            "phone_number": "+254799999999",
            "email": "new.email@example.com",
            "county": "Mombasa",
            "sub_county": "Nyali",
            "ward": "Frere Town",
            "village": "Frere Estate",
            "address": "456 New Address",
            "gender": "male",
        }

        response = await client.patch(
            f"/api/v1/farmers/{test_farmer.id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "New First"
        assert data["last_name"] == "New Last"
        assert data["email"] == "new.email@example.com"

    @pytest.mark.asyncio
    async def test_update_farmer_not_found(self, client: AsyncClient):
        """Test updating non-existent farmer returns 404."""
        fake_id = uuid.uuid4()
        update_data = {"first_name": "Test"}

        response = await client.patch(f"/api/v1/farmers/{fake_id}", json=update_data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_farmer_empty_body(self, client: AsyncClient, test_farmer: Farmer):
        """Test update with empty body succeeds but changes nothing."""
        response = await client.patch(
            f"/api/v1/farmers/{test_farmer.id}",
            json={}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == test_farmer.first_name


class TestFarmerListing:
    """Tests for farmer listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_farmers_empty(self, client: AsyncClient):
        """Test listing farmers when none exist."""
        response = await client.get("/api/v1/farmers")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_farmers_with_data(
        self, client: AsyncClient, test_farmer: Farmer, test_farmer_with_bank: Farmer
    ):
        """Test listing farmers with existing data."""
        response = await client.get("/api/v1/farmers")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_farmers_pagination(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test farmer listing with pagination."""
        # Create 25 farmers
        for i in range(25):
            farmer = Farmer(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                tenant_id=uuid.uuid4(),
                first_name=f"Farmer{i}",
                last_name="Test",
                phone_number=f"+2547000000{i:02d}",
            )
            db_session.add(farmer)
        await db_session.commit()

        # Test page 1
        response = await client.get("/api/v1/farmers?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 10

        # Test page 3
        response = await client.get("/api/v1/farmers?page=3&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 3

    @pytest.mark.asyncio
    async def test_list_farmers_filter_by_kyc_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering farmers by KYC status."""
        # Create farmers with different KYC statuses
        for i, status in enumerate(["pending", "verified", "pending", "rejected"]):
            farmer = Farmer(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                tenant_id=uuid.uuid4(),
                first_name=f"Farmer{i}",
                last_name="Test",
                phone_number=f"+2547000001{i:02d}",
                kyc_status=status,
            )
            db_session.add(farmer)
        await db_session.commit()

        # Filter pending
        response = await client.get("/api/v1/farmers?kyc_status=pending")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(f["kyc_status"] == "pending" for f in data["items"])

        # Filter verified
        response = await client.get("/api/v1/farmers?kyc_status=verified")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_farmers_invalid_pagination(self, client: AsyncClient):
        """Test invalid pagination parameters."""
        # Page 0 should fail
        response = await client.get("/api/v1/farmers?page=0")
        assert response.status_code == 422

        # Negative page should fail
        response = await client.get("/api/v1/farmers?page=-1")
        assert response.status_code == 422

        # Page size > 100 should fail
        response = await client.get("/api/v1/farmers?page_size=101")
        assert response.status_code == 422


class TestFarmerWithBankDetails:
    """Tests for farmers with bank details (bank details stored but not returned in basic response)."""

    @pytest.mark.asyncio
    async def test_get_farmer_with_bank_details(
        self, client: AsyncClient, test_farmer_with_bank: Farmer
    ):
        """Test retrieval of farmer with bank details (basic fields returned)."""
        response = await client.get(f"/api/v1/farmers/{test_farmer_with_bank.id}")

        assert response.status_code == 200
        data = response.json()
        # Bank details are stored but not included in basic response schema
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"

    @pytest.mark.asyncio
    async def test_update_farmer_bank_details(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test updating farmer's bank details (update succeeds, not returned in response)."""
        update_data = {
            "bank_name": "Equity",
            "bank_account": "9876543210",
        }

        response = await client.patch(
            f"/api/v1/farmers/{test_farmer.id}",
            json=update_data
        )

        assert response.status_code == 200
        # Update succeeds but bank details not in response schema


class TestFarmerIdempotency:
    """Tests for idempotent operations."""

    @pytest.mark.asyncio
    async def test_multiple_gets_same_result(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test that multiple GET requests return consistent data."""
        response1 = await client.get(f"/api/v1/farmers/{test_farmer.id}")
        response2 = await client.get(f"/api/v1/farmers/{test_farmer.id}")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()

    @pytest.mark.asyncio
    async def test_update_idempotency(
        self, client: AsyncClient, test_farmer: Farmer
    ):
        """Test that same update applied twice yields same result."""
        update_data = {"first_name": "Idempotent"}

        response1 = await client.patch(
            f"/api/v1/farmers/{test_farmer.id}",
            json=update_data
        )
        response2 = await client.patch(
            f"/api/v1/farmers/{test_farmer.id}",
            json=update_data
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["first_name"] == response2.json()["first_name"]
