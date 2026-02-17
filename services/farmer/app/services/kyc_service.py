"""KYC verification service."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.farmer import BiometricData, Farmer, KYCStatus
from app.schemas.kyc import KYCReviewRequest, KYCStatusResponse


class KYCService:
    """Service for KYC operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_kyc_status(self, farmer_id: UUID) -> KYCStatusResponse | None:
        """Get KYC status for a farmer."""
        result = await self.db.execute(
            select(Farmer)
            .options(selectinload(Farmer.documents), selectinload(Farmer.biometrics))
            .where(Farmer.id == farmer_id)
        )
        farmer = result.scalar_one_or_none()
        if not farmer:
            return None

        docs_verified = sum(1 for d in farmer.documents if d.is_verified)
        biometrics_captured = any(b.is_verified for b in farmer.biometrics)

        missing = self._check_missing_requirements(farmer)

        return KYCStatusResponse(
            farmer_id=farmer.id,
            status=farmer.kyc_status,
            verified_at=farmer.kyc_verified_at,
            documents_submitted=len(farmer.documents),
            documents_verified=docs_verified,
            biometrics_captured=biometrics_captured,
            missing_requirements=missing,
        )

    async def submit_for_review(self, farmer_id: UUID) -> KYCStatusResponse:
        """Submit farmer for KYC review."""
        result = await self.db.execute(
            select(Farmer)
            .options(selectinload(Farmer.documents), selectinload(Farmer.biometrics))
            .where(Farmer.id == farmer_id)
        )
        farmer = result.scalar_one_or_none()
        if not farmer:
            raise ValueError("Farmer not found")

        farmer.kyc_status = KYCStatus.IN_REVIEW.value
        return await self.get_kyc_status(farmer_id)  # type: ignore

    async def review_kyc(self, farmer_id: UUID, review: KYCReviewRequest) -> KYCStatusResponse:
        """Review and approve/reject KYC."""
        result = await self.db.execute(select(Farmer).where(Farmer.id == farmer_id))
        farmer = result.scalar_one_or_none()
        if not farmer:
            raise ValueError("Farmer not found")

        if review.action == "approve":
            farmer.kyc_status = KYCStatus.APPROVED.value
            farmer.kyc_verified_at = datetime.now(UTC)
            farmer.kyc_verified_by = review.reviewer_id
        elif review.action == "reject":
            farmer.kyc_status = KYCStatus.REJECTED.value

        return await self.get_kyc_status(farmer_id)  # type: ignore

    async def verify_biometric(self, farmer_id: UUID, biometric_type: str) -> bool:
        """Verify biometric data."""
        result = await self.db.execute(
            select(BiometricData).where(
                BiometricData.farmer_id == farmer_id,
                BiometricData.biometric_type == biometric_type,
            )
        )
        biometric = result.scalar_one_or_none()
        if not biometric:
            return False

        # TODO: Integrate with biometric verification service
        biometric.is_verified = True
        return True

    def _check_missing_requirements(self, farmer: Farmer) -> list[str]:
        """Check for missing KYC requirements."""
        missing = []

        if not farmer.national_id:
            missing.append("national_id")

        doc_types = {d.document_type for d in farmer.documents}
        if "national_id" not in doc_types:
            missing.append("national_id_document")

        if not any(b.biometric_type == "fingerprint" for b in farmer.biometrics):
            missing.append("fingerprint_biometric")

        return missing
