"""External verification service for ID, credit, and sanctions checks."""

import asyncio
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import ExternalVerification, Farmer


class VerificationType(str, Enum):
    """Types of external verification."""

    ID_IPRS = "id_iprs"  # Kenya IPRS
    ID_NIN = "id_nin"  # Uganda NIN
    ID_NIDA = "id_nida"  # Tanzania NIDA
    CREDIT_BUREAU = "credit_bureau"
    SANCTIONS = "sanctions"
    PEP = "pep"  # Politically Exposed Persons
    BANK_ACCOUNT = "bank_account"


class VerificationResult(BaseModel):
    """Result of an external verification."""

    success: bool
    is_verified: bool
    match_score: float | None = None
    data: dict[str, Any] = {}
    error: str | None = None


class ExternalVerificationService:
    """Service for external verification integrations.

    Integrates with:
    - IPRS (Kenya Integrated Population Registration System)
    - NIN (Uganda National Identification Number)
    - Credit Reference Bureaus (TransUnion, Metropol, CreditInfo)
    - Sanctions screening (WorldCheck, Refinitiv)
    - PEP lists
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def verify_national_id_kenya(
        self,
        farmer_id: UUID,
        national_id: str,
        first_name: str,
        last_name: str,
        date_of_birth: str | None = None,
    ) -> VerificationResult:
        """Verify Kenyan National ID against IPRS.

        Args:
            farmer_id: The farmer's UUID
            national_id: Kenya National ID number
            first_name: First name to match
            last_name: Last name to match
            date_of_birth: Date of birth (optional, for enhanced match)

        Returns:
            VerificationResult with match status
        """
        verification = await self._get_or_create_verification(
            farmer_id=farmer_id,
            verification_type=VerificationType.ID_IPRS,
            provider="IPRS",
        )

        try:
            # In production, integrate with actual IPRS API
            # This is a simulation of the verification process

            # Example IPRS integration would look like:
            # response = await self.http_client.post(
            #     settings.iprs_api_url,
            #     json={
            #         "id_number": national_id,
            #         "first_name": first_name,
            #         "last_name": last_name,
            #     },
            #     headers={"Authorization": f"Bearer {settings.iprs_api_key}"},
            # )

            # Simulate verification (replace with actual API call)
            verification_data = await self._simulate_iprs_verification(
                national_id, first_name, last_name
            )

            # Update verification record
            verification.status = "success" if verification_data["match"] else "failed"
            verification.is_verified = verification_data["match"]
            verification.match_score = verification_data.get("match_score")
            verification.response_data = verification_data
            verification.completed_at = datetime.now(UTC)

            return VerificationResult(
                success=True,
                is_verified=verification_data["match"],
                match_score=verification_data.get("match_score"),
                data=verification_data,
            )

        except Exception as e:
            verification.status = "error"
            verification.error_message = str(e)
            verification.completed_at = datetime.now(UTC)

            return VerificationResult(
                success=False,
                is_verified=False,
                error=str(e),
            )

    async def verify_credit_bureau(
        self,
        farmer_id: UUID,
        national_id: str,
        bureau: str = "TransUnion",
    ) -> VerificationResult:
        """Check credit history from credit reference bureau.

        Args:
            farmer_id: The farmer's UUID
            national_id: National ID for lookup
            bureau: Which bureau to use (TransUnion, Metropol, CreditInfo)

        Returns:
            VerificationResult with credit data
        """
        verification = await self._get_or_create_verification(
            farmer_id=farmer_id,
            verification_type=VerificationType.CREDIT_BUREAU,
            provider=bureau,
        )

        try:
            # Simulate credit bureau check
            credit_data = await self._simulate_credit_check(national_id, bureau)

            verification.status = "success"
            verification.is_verified = True  # Credit check completed
            verification.response_data = credit_data
            verification.completed_at = datetime.now(UTC)

            return VerificationResult(
                success=True,
                is_verified=True,
                data=credit_data,
            )

        except Exception as e:
            verification.status = "error"
            verification.error_message = str(e)
            verification.completed_at = datetime.now(UTC)

            return VerificationResult(
                success=False,
                is_verified=False,
                error=str(e),
            )

    async def check_sanctions(
        self,
        farmer_id: UUID,
        full_name: str,
        national_id: str | None = None,
        date_of_birth: str | None = None,
    ) -> VerificationResult:
        """Screen against sanctions and PEP lists.

        Args:
            farmer_id: The farmer's UUID
            full_name: Full name to screen
            national_id: Optional national ID
            date_of_birth: Optional DOB for enhanced matching

        Returns:
            VerificationResult with screening results
        """
        verification = await self._get_or_create_verification(
            farmer_id=farmer_id,
            verification_type=VerificationType.SANCTIONS,
            provider="WorldCheck",
        )

        try:
            # Simulate sanctions screening
            screening_data = await self._simulate_sanctions_screening(
                full_name, national_id, date_of_birth
            )

            # is_verified means NO sanctions hits (clear)
            is_clear = not screening_data.get("has_hits", False)

            verification.status = "success"
            verification.is_verified = is_clear
            verification.match_score = screening_data.get("match_score", 0.0)
            verification.response_data = screening_data
            verification.completed_at = datetime.now(UTC)

            return VerificationResult(
                success=True,
                is_verified=is_clear,
                match_score=screening_data.get("match_score"),
                data=screening_data,
            )

        except Exception as e:
            verification.status = "error"
            verification.error_message = str(e)
            verification.completed_at = datetime.now(UTC)

            return VerificationResult(
                success=False,
                is_verified=False,
                error=str(e),
            )

    async def verify_bank_account(
        self,
        farmer_id: UUID,
        bank_code: str,
        account_number: str,
        account_name: str,
    ) -> VerificationResult:
        """Verify bank account ownership.

        Uses micro-deposit verification or bank API where available.
        """
        verification = await self._get_or_create_verification(
            farmer_id=farmer_id,
            verification_type=VerificationType.BANK_ACCOUNT,
            provider="BankVerify",
        )

        try:
            # Simulate bank account verification
            bank_data = await self._simulate_bank_verification(
                bank_code, account_number, account_name
            )

            verification.status = "success"
            verification.is_verified = bank_data.get("name_match", False)
            verification.match_score = bank_data.get("match_score")
            verification.response_data = bank_data
            verification.completed_at = datetime.now(UTC)

            return VerificationResult(
                success=True,
                is_verified=bank_data.get("name_match", False),
                match_score=bank_data.get("match_score"),
                data=bank_data,
            )

        except Exception as e:
            verification.status = "error"
            verification.error_message = str(e)
            verification.completed_at = datetime.now(UTC)

            return VerificationResult(
                success=False,
                is_verified=False,
                error=str(e),
            )

    async def run_all_verifications(
        self,
        farmer_id: UUID,
    ) -> dict[str, VerificationResult]:
        """Run all applicable verifications for a farmer.

        Returns dict mapping verification type to result.
        """
        # Get farmer details
        result = await self.db.execute(select(Farmer).where(Farmer.id == farmer_id))
        farmer = result.scalar_one_or_none()
        if not farmer:
            raise ValueError("Farmer not found")

        results: dict[str, VerificationResult] = {}

        # Run verifications in parallel
        tasks = []

        # ID verification
        if farmer.national_id:
            tasks.append(
                (
                    "id_verification",
                    self.verify_national_id_kenya(
                        farmer_id=farmer_id,
                        national_id=farmer.national_id,
                        first_name=farmer.first_name,
                        last_name=farmer.last_name,
                    ),
                )
            )

        # Credit check
        if farmer.national_id:
            tasks.append(
                (
                    "credit_check",
                    self.verify_credit_bureau(
                        farmer_id=farmer_id,
                        national_id=farmer.national_id,
                    ),
                )
            )

        # Sanctions screening
        tasks.append(
            (
                "sanctions_check",
                self.check_sanctions(
                    farmer_id=farmer_id,
                    full_name=f"{farmer.first_name} {farmer.last_name}",
                    national_id=farmer.national_id,
                ),
            )
        )

        # Bank account verification
        if farmer.bank_account and farmer.bank_name:
            tasks.append(
                (
                    "bank_verification",
                    self.verify_bank_account(
                        farmer_id=farmer_id,
                        bank_code=farmer.bank_name,
                        account_number=farmer.bank_account,
                        account_name=f"{farmer.first_name} {farmer.last_name}",
                    ),
                )
            )

        # Execute all tasks
        for name, task in tasks:
            results[name] = await task

        return results

    async def get_verification_status(self, farmer_id: UUID) -> list[dict[str, Any]]:
        """Get status of all verifications for a farmer."""
        result = await self.db.execute(
            select(ExternalVerification).where(ExternalVerification.farmer_id == farmer_id)
        )
        verifications = result.scalars().all()

        return [
            {
                "id": str(v.id),
                "type": v.verification_type,
                "provider": v.provider,
                "status": v.status,
                "is_verified": v.is_verified,
                "match_score": v.match_score,
                "requested_at": v.requested_at.isoformat() if v.requested_at else None,
                "completed_at": v.completed_at.isoformat() if v.completed_at else None,
                "error": v.error_message,
            }
            for v in verifications
        ]

    # Private helper methods

    async def _get_or_create_verification(
        self,
        farmer_id: UUID,
        verification_type: VerificationType,
        provider: str,
    ) -> ExternalVerification:
        """Get existing or create new verification record."""
        result = await self.db.execute(
            select(ExternalVerification).where(
                ExternalVerification.farmer_id == farmer_id,
                ExternalVerification.verification_type == verification_type.value,
            )
        )
        verification = result.scalar_one_or_none()

        if not verification:
            verification = ExternalVerification(
                farmer_id=farmer_id,
                verification_type=verification_type.value,
                provider=provider,
                status="pending",
            )
            self.db.add(verification)
            await self.db.flush()

        return verification

    # Simulation methods (replace with actual API integrations)

    async def _simulate_iprs_verification(
        self,
        national_id: str,
        first_name: str,
        last_name: str,
    ) -> dict[str, Any]:
        """Simulate IPRS verification response."""
        # In production, this would call the actual IPRS API
        await asyncio.sleep(0.5)  # Simulate API latency

        # Simulate successful verification for valid-looking IDs
        if len(national_id) >= 7:
            return {
                "match": True,
                "match_score": 0.95,
                "id_number": national_id,
                "name_match": True,
                "id_status": "valid",
                "photo_available": True,
            }
        return {
            "match": False,
            "match_score": 0.0,
            "error": "Invalid ID format",
        }

    async def _simulate_credit_check(
        self,
        national_id: str,
        bureau: str,
    ) -> dict[str, Any]:
        """Simulate credit bureau response."""
        await asyncio.sleep(0.5)

        return {
            "bureau": bureau,
            "credit_score": 650,
            "credit_score_band": "Good",
            "active_accounts": 2,
            "closed_accounts": 1,
            "total_debt": 50000,
            "monthly_payment": 5000,
            "delinquent_accounts": 0,
            "defaults": 0,
            "inquiry_count_6m": 3,
            "credit_utilization": 0.35,
            "account_age_months": 48,
        }

    async def _simulate_sanctions_screening(
        self,
        full_name: str,
        national_id: str | None,
        date_of_birth: str | None,
    ) -> dict[str, Any]:
        """Simulate sanctions screening response."""
        await asyncio.sleep(0.3)

        # Simulate clear screening for most cases
        return {
            "has_hits": False,
            "match_score": 0.0,
            "lists_checked": [
                "UN Sanctions",
                "OFAC SDN",
                "EU Sanctions",
                "UK HMT",
                "Local PEP List",
            ],
            "potential_matches": [],
            "screening_date": datetime.now(UTC).isoformat(),
        }

    async def _simulate_bank_verification(
        self,
        bank_code: str,
        account_number: str,
        account_name: str,
    ) -> dict[str, Any]:
        """Simulate bank account verification response."""
        await asyncio.sleep(0.3)

        return {
            "bank_code": bank_code,
            "account_exists": True,
            "account_active": True,
            "name_match": True,
            "match_score": 0.92,
            "account_type": "savings",
        }

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()
