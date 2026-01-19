"""Tests for external verification service."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import ExternalVerification, Farmer
from app.services.external_verification_service import (
    ExternalVerificationService,
    VerificationType,
)


@pytest.mark.asyncio
class TestExternalVerificationService:
    """Test cases for external verification service."""

    async def test_verify_national_id_kenya_success(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test successful Kenyan National ID verification."""
        service = ExternalVerificationService(db_session)

        result = await service.verify_national_id_kenya(
            farmer_id=test_farmer.id,
            national_id="12345678",  # Valid format (7+ chars)
            first_name="John",
            last_name="Doe",
        )

        assert result.success is True
        assert result.is_verified is True
        assert result.match_score is not None
        assert result.match_score > 0.9

    async def test_verify_national_id_kenya_invalid_format(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test Kenyan National ID verification with invalid format."""
        service = ExternalVerificationService(db_session)

        result = await service.verify_national_id_kenya(
            farmer_id=test_farmer.id,
            national_id="123",  # Too short
            first_name="John",
            last_name="Doe",
        )

        assert result.success is True
        assert result.is_verified is False

    async def test_verify_credit_bureau(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test credit bureau verification."""
        service = ExternalVerificationService(db_session)

        result = await service.verify_credit_bureau(
            farmer_id=test_farmer.id,
            national_id="12345678",
            bureau="TransUnion",
        )

        assert result.success is True
        assert result.is_verified is True
        assert "credit_score" in result.data
        assert "credit_score_band" in result.data

    async def test_check_sanctions_clear(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test sanctions screening with clear result."""
        service = ExternalVerificationService(db_session)

        result = await service.check_sanctions(
            farmer_id=test_farmer.id,
            full_name="John Doe",
            national_id="12345678",
        )

        assert result.success is True
        # is_verified means NO sanctions hits (clear)
        assert result.is_verified is True
        assert result.data.get("has_hits") is False

    async def test_verify_bank_account(
        self, db_session: AsyncSession, test_farmer_with_bank: Farmer
    ) -> None:
        """Test bank account verification."""
        service = ExternalVerificationService(db_session)

        result = await service.verify_bank_account(
            farmer_id=test_farmer_with_bank.id,
            bank_code="KCB",
            account_number="1234567890",
            account_name="Jane Smith",
        )

        assert result.success is True
        assert result.is_verified is True
        assert result.data.get("account_exists") is True
        assert result.data.get("name_match") is True

    async def test_run_all_verifications(
        self, db_session: AsyncSession, test_farmer_with_bank: Farmer
    ) -> None:
        """Test running all verifications for a farmer."""
        service = ExternalVerificationService(db_session)

        results = await service.run_all_verifications(test_farmer_with_bank.id)

        # Should have ID verification, credit check, sanctions check, and bank verification
        assert "id_verification" in results
        assert "credit_check" in results
        assert "sanctions_check" in results
        assert "bank_verification" in results

        # All should succeed
        for name, result in results.items():
            assert result.success is True, f"{name} verification failed"

    async def test_run_all_verifications_farmer_not_found(
        self, db_session: AsyncSession
    ) -> None:
        """Test running verifications for non-existent farmer."""
        service = ExternalVerificationService(db_session)

        with pytest.raises(ValueError, match="Farmer not found"):
            await service.run_all_verifications(uuid.uuid4())

    async def test_get_verification_status(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test getting verification status."""
        service = ExternalVerificationService(db_session)

        # Run a verification first
        await service.verify_national_id_kenya(
            farmer_id=test_farmer.id,
            national_id="12345678",
            first_name="John",
            last_name="Doe",
        )
        await db_session.commit()

        # Get status
        statuses = await service.get_verification_status(test_farmer.id)

        assert len(statuses) >= 1
        id_verification = next(
            (s for s in statuses if s["type"] == VerificationType.ID_IPRS.value), None
        )
        assert id_verification is not None
        assert id_verification["status"] in ["success", "failed"]

    async def test_verification_record_created(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test that verification records are created in database."""
        service = ExternalVerificationService(db_session)

        # Run verification
        await service.verify_national_id_kenya(
            farmer_id=test_farmer.id,
            national_id="12345678",
            first_name="John",
            last_name="Doe",
        )
        await db_session.commit()

        # Check database record
        from sqlalchemy import select

        result = await db_session.execute(
            select(ExternalVerification).where(
                ExternalVerification.farmer_id == test_farmer.id,
                ExternalVerification.verification_type == VerificationType.ID_IPRS.value,
            )
        )
        verification = result.scalar_one_or_none()

        assert verification is not None
        assert verification.status == "success"
        assert verification.is_verified is True
        assert verification.completed_at is not None

    async def test_verification_reuses_existing_record(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test that re-running verification updates existing record."""
        service = ExternalVerificationService(db_session)

        # Run verification twice
        await service.verify_national_id_kenya(
            farmer_id=test_farmer.id,
            national_id="12345678",
            first_name="John",
            last_name="Doe",
        )
        await db_session.commit()

        await service.verify_national_id_kenya(
            farmer_id=test_farmer.id,
            national_id="12345678",
            first_name="John",
            last_name="Doe",
        )
        await db_session.commit()

        # Should only have one record
        from sqlalchemy import select

        result = await db_session.execute(
            select(ExternalVerification).where(
                ExternalVerification.farmer_id == test_farmer.id,
                ExternalVerification.verification_type == VerificationType.ID_IPRS.value,
            )
        )
        verifications = result.scalars().all()

        assert len(verifications) == 1
