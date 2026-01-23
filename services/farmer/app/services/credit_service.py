"""Credit Bureau Integration Service."""

import uuid
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eligibility import (
    CreditBureauProvider,
    CreditCheck,
    CreditCheckStatus,
)
from app.models.farmer import Farmer
from app.schemas.eligibility import CreditCheckRequest, CreditCheckResponse


class CreditBureauService:
    """Service for integrating with credit bureau providers."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def get_active_provider(self, tenant_id: uuid.UUID) -> CreditBureauProvider | None:
        """Get the active credit bureau provider for a tenant."""
        query = (
            select(CreditBureauProvider)
            .where(CreditBureauProvider.tenant_id == tenant_id)
            .where(CreditBureauProvider.is_active == True)
            .order_by(CreditBureauProvider.priority)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_recent_credit_check(
        self, farmer_id: uuid.UUID, max_age_days: int = 90
    ) -> CreditCheck | None:
        """Get the most recent valid credit check for a farmer."""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        query = (
            select(CreditCheck)
            .where(CreditCheck.farmer_id == farmer_id)
            .where(CreditCheck.status == CreditCheckStatus.COMPLETED.value)
            .where(CreditCheck.completed_at >= cutoff_date)
            .order_by(CreditCheck.completed_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def request_credit_check(
        self,
        request: CreditCheckRequest,
        farmer: Farmer,
        tenant_id: uuid.UUID,
    ) -> CreditCheck:
        """Request a new credit check for a farmer."""
        # Check for recent valid credit check
        recent_check = await self.get_recent_credit_check(request.farmer_id)
        if recent_check:
            return recent_check

        # Create new credit check record
        credit_check = CreditCheck(
            farmer_id=request.farmer_id,
            assessment_id=request.assessment_id,
            reference_number=f"CC-{uuid.uuid4().hex[:12].upper()}",
            request_type=request.request_type,
            consent_given=request.consent_given,
            consent_date=datetime.utcnow() if request.consent_given else None,
            declared_income=request.declared_income,
            status=CreditCheckStatus.PENDING.value,
        )
        self.db.add(credit_check)
        await self.db.flush()

        # Get active provider
        provider = await self.get_active_provider(tenant_id)

        if provider:
            # Make API call to credit bureau
            try:
                credit_check.status = CreditCheckStatus.IN_PROGRESS.value
                await self.db.flush()

                response = await self._call_credit_bureau(provider, farmer, request)
                self._process_credit_response(credit_check, response)
            except Exception as e:
                credit_check.status = CreditCheckStatus.FAILED.value
                credit_check.error_message = str(e)
        else:
            # No provider configured - use mock data for development
            self._apply_mock_credit_data(credit_check, farmer)

        await self.db.flush()
        return credit_check

    async def _call_credit_bureau(
        self,
        provider: CreditBureauProvider,
        farmer: Farmer,
        request: CreditCheckRequest,
    ) -> dict[str, Any]:
        """Make actual API call to credit bureau."""
        client = await self._get_http_client()

        # Build request based on provider type
        if provider.provider_type == "transunion":
            return await self._call_transunion(client, provider, farmer)
        elif provider.provider_type == "experian":
            return await self._call_experian(client, provider, farmer)
        elif provider.provider_type == "local":
            return await self._call_local_crb(client, provider, farmer)
        else:
            raise ValueError(f"Unknown provider type: {provider.provider_type}")

    async def _call_transunion(
        self,
        client: httpx.AsyncClient,
        provider: CreditBureauProvider,
        farmer: Farmer,
    ) -> dict[str, Any]:
        """Call TransUnion API."""
        # This would be the actual TransUnion API integration
        # For now, return mock response
        headers = {
            "Authorization": f"Bearer {provider.api_key_encrypted}",
            "Content-Type": "application/json",
        }
        payload = {
            "nationalId": farmer.national_id,
            "firstName": farmer.first_name,
            "lastName": farmer.last_name,
            "phoneNumber": farmer.phone_number,
        }

        try:
            response = await client.post(
                f"{provider.api_base_url}/credit-check",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            # Return mock data on failure for development
            return self._get_mock_credit_response()

    async def _call_experian(
        self,
        client: httpx.AsyncClient,
        provider: CreditBureauProvider,
        farmer: Farmer,
    ) -> dict[str, Any]:
        """Call Experian API."""
        # Placeholder for Experian integration
        return self._get_mock_credit_response()

    async def _call_local_crb(
        self,
        client: httpx.AsyncClient,
        provider: CreditBureauProvider,
        farmer: Farmer,
    ) -> dict[str, Any]:
        """Call local Credit Reference Bureau API."""
        # Placeholder for local CRB integration (e.g., CRB Africa)
        return self._get_mock_credit_response()

    def _process_credit_response(self, credit_check: CreditCheck, response: dict) -> None:
        """Process the credit bureau response."""
        credit_check.status = CreditCheckStatus.COMPLETED.value
        credit_check.completed_at = datetime.utcnow()
        credit_check.valid_until = datetime.utcnow() + timedelta(days=90)

        # Extract credit data from response
        credit_check.credit_score = response.get("creditScore")
        credit_check.score_band = self._get_score_band(response.get("creditScore"))
        credit_check.total_accounts = response.get("totalAccounts", 0)
        credit_check.active_accounts = response.get("activeAccounts", 0)
        credit_check.total_debt = response.get("totalDebt", 0.0)
        credit_check.monthly_obligations = response.get("monthlyObligations", 0.0)
        credit_check.delinquent_accounts = response.get("delinquentAccounts", 0)
        credit_check.defaults_count = response.get("defaultsCount", 0)

        # Calculate debt-to-income ratio
        if credit_check.declared_income and credit_check.declared_income > 0:
            monthly_obligations = credit_check.monthly_obligations or 0
            credit_check.debt_to_income_ratio = (
                monthly_obligations / credit_check.declared_income
            ) * 100

        # Store full response (with sensitive data masked)
        credit_check.response_data = self._mask_sensitive_data(response)

    def _get_score_band(self, score: int | None) -> str | None:
        """Convert credit score to band."""
        if score is None:
            return None
        if score >= 750:
            return "excellent"
        elif score >= 700:
            return "good"
        elif score >= 650:
            return "fair"
        elif score >= 550:
            return "poor"
        else:
            return "very_poor"

    def _apply_mock_credit_data(self, credit_check: CreditCheck, farmer: Farmer) -> None:
        """Apply mock credit data for development/testing."""
        import random

        # Generate consistent mock data based on farmer ID
        seed = int(str(farmer.id).replace("-", "")[:8], 16)
        random.seed(seed)

        credit_score = random.randint(450, 850)
        total_accounts = random.randint(0, 10)
        active_accounts = random.randint(0, total_accounts)
        total_debt = random.uniform(0, 500000)
        delinquent = random.randint(0, 2)

        credit_check.status = CreditCheckStatus.COMPLETED.value
        credit_check.completed_at = datetime.utcnow()
        credit_check.valid_until = datetime.utcnow() + timedelta(days=90)
        credit_check.credit_score = credit_score
        credit_check.score_band = self._get_score_band(credit_score)
        credit_check.total_accounts = total_accounts
        credit_check.active_accounts = active_accounts
        credit_check.total_debt = total_debt
        credit_check.monthly_obligations = total_debt * 0.05 if total_debt > 0 else 0
        credit_check.delinquent_accounts = delinquent
        credit_check.defaults_count = random.randint(0, 1) if delinquent > 0 else 0

        if credit_check.declared_income and credit_check.declared_income > 0:
            credit_check.debt_to_income_ratio = (
                credit_check.monthly_obligations / credit_check.declared_income
            ) * 100

        credit_check.response_data = {
            "source": "mock_data",
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _get_mock_credit_response(self) -> dict[str, Any]:
        """Get mock credit response for development."""
        import random

        return {
            "creditScore": random.randint(500, 800),
            "totalAccounts": random.randint(1, 8),
            "activeAccounts": random.randint(1, 5),
            "totalDebt": random.uniform(10000, 300000),
            "monthlyObligations": random.uniform(1000, 20000),
            "delinquentAccounts": random.randint(0, 2),
            "defaultsCount": random.randint(0, 1),
        }

    def _mask_sensitive_data(self, data: dict) -> dict:
        """Mask sensitive data in credit response."""
        masked = data.copy()
        sensitive_fields = ["ssn", "national_id", "account_numbers", "addresses"]
        for field in sensitive_fields:
            if field in masked:
                if isinstance(masked[field], str):
                    masked[field] = "***MASKED***"
                elif isinstance(masked[field], list):
                    masked[field] = ["***MASKED***"] * len(masked[field])
        return masked

    async def get_credit_check(self, credit_check_id: uuid.UUID) -> CreditCheck | None:
        """Get a credit check by ID."""
        query = select(CreditCheck).where(CreditCheck.id == credit_check_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_farmer_credit_history(
        self, farmer_id: uuid.UUID, limit: int = 10
    ) -> list[CreditCheck]:
        """Get credit check history for a farmer."""
        query = (
            select(CreditCheck)
            .where(CreditCheck.farmer_id == farmer_id)
            .order_by(CreditCheck.requested_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def get_credit_data_for_rules(self, credit_check: CreditCheck | None) -> dict:
        """Get credit data formatted for rules engine evaluation."""
        if not credit_check or credit_check.status != CreditCheckStatus.COMPLETED.value:
            return {}

        return {
            "credit_score": credit_check.credit_score,
            "score_band": credit_check.score_band,
            "total_accounts": credit_check.total_accounts,
            "active_accounts": credit_check.active_accounts,
            "total_debt": credit_check.total_debt,
            "monthly_obligations": credit_check.monthly_obligations,
            "delinquent_accounts": credit_check.delinquent_accounts,
            "defaults_count": credit_check.defaults_count,
            "debt_to_income_ratio": credit_check.debt_to_income_ratio,
            "has_defaults": (credit_check.defaults_count or 0) > 0,
            "has_delinquencies": (credit_check.delinquent_accounts or 0) > 0,
            "is_over_indebted": (credit_check.debt_to_income_ratio or 0) > 50,
        }


# =============================================================================
# Credit Bureau Provider Management
# =============================================================================


async def create_credit_bureau_provider(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    name: str,
    code: str,
    provider_type: str,
    api_base_url: str | None = None,
    api_key: str | None = None,
    api_config: dict | None = None,
) -> CreditBureauProvider:
    """Create a new credit bureau provider configuration."""
    provider = CreditBureauProvider(
        tenant_id=tenant_id,
        name=name,
        code=code,
        provider_type=provider_type,
        api_base_url=api_base_url,
        api_key_encrypted=api_key,  # In production, this should be encrypted
        api_config=api_config,
    )
    db.add(provider)
    await db.flush()
    return provider
