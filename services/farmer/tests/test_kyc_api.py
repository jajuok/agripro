"""Tests for KYC API endpoints."""

import uuid
from io import BytesIO

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer, KYCApplication
from app.services.kyc_workflow_service import KYCStep


@pytest.mark.asyncio
class TestKYCAPIEndpoints:
    """Test cases for KYC API endpoints."""

    async def test_start_kyc_application(
        self, client: AsyncClient, test_farmer: Farmer
    ) -> None:
        """Test starting a KYC application via API."""
        response = await client.post(
            f"/api/v1/kyc/{test_farmer.id}/start",
            json={
                "required_documents": ["national_id"],
                "required_biometrics": ["fingerprint_right_index"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["farmer_id"] == str(test_farmer.id)
        assert data["current_step"] == "personal_info"
        assert data["overall_status"] == "pending"

    async def test_start_kyc_application_default_requirements(
        self, client: AsyncClient, test_farmer: Farmer
    ) -> None:
        """Test starting a KYC application with default requirements."""
        response = await client.post(f"/api/v1/kyc/{test_farmer.id}/start")

        assert response.status_code == 200
        data = response.json()
        assert data["farmer_id"] == str(test_farmer.id)
        # Default requirements should be applied
        assert "national_id" in data["required_documents"]

    async def test_get_kyc_status(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ) -> None:
        """Test getting KYC status via API."""
        # First start KYC
        kyc_app = KYCApplication(
            farmer_id=test_farmer.id,
            current_step="personal_info",
            personal_info_complete=False,
            documents_complete=False,
            biometrics_complete=False,
            bank_info_complete=False,
            required_documents={"national_id": False},
            required_biometrics=["fingerprint_right_index"],
        )
        db_session.add(kyc_app)
        await db_session.commit()

        response = await client.get(f"/api/v1/kyc/{test_farmer.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["farmer_id"] == str(test_farmer.id)
        assert data["current_step"] == "personal_info"

    async def test_get_kyc_status_not_found(self, client: AsyncClient) -> None:
        """Test getting KYC status for non-existent farmer."""
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/kyc/{fake_id}/status")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_complete_kyc_step(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ) -> None:
        """Test completing a KYC step via API."""
        # Start KYC first
        kyc_app = KYCApplication(
            farmer_id=test_farmer.id,
            current_step="personal_info",
            personal_info_complete=False,
            documents_complete=False,
            biometrics_complete=False,
            bank_info_complete=False,
        )
        db_session.add(kyc_app)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/kyc/{test_farmer.id}/step/complete",
            json={
                "step": "personal_info",
                "data": {"verified": True},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["personal_info_complete"] is True
        assert data["current_step"] == "documents"

    async def test_complete_kyc_step_invalid_order(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ) -> None:
        """Test completing a KYC step out of order."""
        # Start KYC first
        kyc_app = KYCApplication(
            farmer_id=test_farmer.id,
            current_step="personal_info",
            personal_info_complete=False,
            documents_complete=False,
            biometrics_complete=False,
            bank_info_complete=False,
        )
        db_session.add(kyc_app)
        await db_session.commit()

        # Try to complete documents step before personal_info
        response = await client.post(
            f"/api/v1/kyc/{test_farmer.id}/step/complete",
            json={"step": "documents"},
        )

        assert response.status_code == 400

    async def test_submit_for_review(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ) -> None:
        """Test submitting KYC for review via API."""
        # Create KYC with all steps completed
        kyc_app = KYCApplication(
            farmer_id=test_farmer.id,
            current_step="bank_info",
            personal_info_complete=True,
            documents_complete=True,
            biometrics_complete=True,
            bank_info_complete=True,
            required_documents={},
            submitted_documents={},
            required_biometrics=[],
            captured_biometrics=[],
        )
        db_session.add(kyc_app)
        await db_session.commit()

        response = await client.post(f"/api/v1/kyc/{test_farmer.id}/submit")

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] in ["in_review", "approved"]

    async def test_review_kyc_approve(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ) -> None:
        """Test approving a KYC application via API."""
        # Create KYC in review state
        kyc_app = KYCApplication(
            farmer_id=test_farmer.id,
            current_step="review",
            personal_info_complete=True,
            documents_complete=True,
            biometrics_complete=True,
            bank_info_complete=True,
        )
        db_session.add(kyc_app)
        await db_session.commit()

        reviewer_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/kyc/{test_farmer.id}/review",
            json={
                "action": "approve",
                "reviewer_id": str(reviewer_id),
                "notes": "All documents verified",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "approved"

    async def test_review_kyc_reject(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ) -> None:
        """Test rejecting a KYC application via API."""
        # Create KYC in review state
        kyc_app = KYCApplication(
            farmer_id=test_farmer.id,
            current_step="review",
            personal_info_complete=True,
            documents_complete=True,
            biometrics_complete=True,
            bank_info_complete=True,
        )
        db_session.add(kyc_app)
        await db_session.commit()

        reviewer_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/kyc/{test_farmer.id}/review",
            json={
                "action": "reject",
                "reviewer_id": str(reviewer_id),
                "rejection_reason": "Invalid documents",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "rejected"

    async def test_upload_document(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ) -> None:
        """Test uploading a document via API."""
        # Create KYC application
        kyc_app = KYCApplication(
            farmer_id=test_farmer.id,
            current_step="documents",
            personal_info_complete=True,
            documents_complete=False,
            biometrics_complete=False,
            bank_info_complete=False,
            required_documents={"national_id": False},
        )
        db_session.add(kyc_app)
        await db_session.commit()

        # Create a fake image file
        fake_image = BytesIO(b"fake image data")

        response = await client.post(
            f"/api/v1/kyc/{test_farmer.id}/documents",
            files={"file": ("test_id.jpg", fake_image, "image/jpeg")},
            data={
                "document_type": "national_id",
                "document_number": "12345678",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["document_type"] == "national_id"
        assert data["document_id"] is not None

    async def test_get_review_queue(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ) -> None:
        """Test getting the review queue via API."""
        from app.models.farmer import KYCReviewQueue

        # Add entry to review queue
        queue_entry = KYCReviewQueue(
            farmer_id=test_farmer.id,
            priority=3,
            reason="Manual review required",
            status="pending",
        )
        db_session.add(queue_entry)
        await db_session.commit()

        response = await client.get("/api/v1/kyc/review-queue")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_assign_review(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ) -> None:
        """Test assigning a review via API."""
        from app.models.farmer import KYCReviewQueue

        # Add entry to review queue
        queue_entry = KYCReviewQueue(
            farmer_id=test_farmer.id,
            priority=3,
            reason="Manual review required",
            status="pending",
        )
        db_session.add(queue_entry)
        await db_session.commit()

        reviewer_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/kyc/{test_farmer.id}/review/assign",
            json={"reviewer_id": str(reviewer_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assigned"] is True
        assert data["reviewer_id"] == str(reviewer_id)

    async def test_run_external_verifications(
        self, client: AsyncClient, test_farmer: Farmer
    ) -> None:
        """Test running external verifications via API."""
        response = await client.post(f"/api/v1/kyc/{test_farmer.id}/verify/external")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least sanctions check (doesn't require national_id)
        assert len(data) >= 1

    async def test_get_verification_status(
        self, client: AsyncClient, test_farmer: Farmer, db_session: AsyncSession
    ) -> None:
        """Test getting verification status via API."""
        from app.models.farmer import ExternalVerification

        # Add a verification record
        verification = ExternalVerification(
            farmer_id=test_farmer.id,
            verification_type="id_iprs",
            provider="IPRS",
            status="success",
            is_verified=True,
        )
        db_session.add(verification)
        await db_session.commit()

        response = await client.get(f"/api/v1/kyc/{test_farmer.id}/verify/status")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
