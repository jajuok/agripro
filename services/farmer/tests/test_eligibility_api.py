"""API Integration tests for Eligibility Assessment Engine."""

import json
import uuid
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.eligibility import (
    EligibilityScheme,
    EligibilityRule,
    EligibilityAssessment,
    SchemeStatus,
    AssessmentStatus,
    RuleOperator,
    RuleFieldType,
)
from app.models.farmer import Farmer, FarmProfile, KYCStatus


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def elig_tenant_id():
    """Create a test tenant ID."""
    return uuid.uuid4()


@pytest_asyncio.fixture
async def elig_farmer(db_session: AsyncSession, elig_tenant_id):
    """Create a test farmer in the database."""
    farmer = Farmer(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=elig_tenant_id,
        first_name="Test",
        last_name="Farmer",
        phone_number="+254712345678",
        email="test.farmer@example.com",
        national_id="TEST123456",
        kyc_status=KYCStatus.APPROVED.value,
        kyc_verified_at=datetime.now(timezone.utc),
        county="Kiambu",
        sub_county="Thika",
        bank_account="1234567890",
        is_active=True,
    )
    db_session.add(farmer)
    await db_session.commit()
    await db_session.refresh(farmer)
    return farmer


@pytest_asyncio.fixture
async def elig_farm(db_session: AsyncSession, elig_farmer):
    """Create a test farm in the database."""
    farm = FarmProfile(
        id=uuid.uuid4(),
        farmer_id=elig_farmer.id,
        name="Test Farm",
        total_acreage=5.0,
        cultivable_acreage=4.5,
        ownership_type="owned",
        latitude=-1.2921,
        longitude=36.8219,
        county="Kiambu",
        is_verified=True,
        registration_complete=True,
    )
    db_session.add(farm)
    await db_session.commit()
    await db_session.refresh(farm)
    return farm


@pytest_asyncio.fixture
async def elig_scheme(db_session: AsyncSession, elig_tenant_id):
    """Create a test scheme in the database."""
    scheme = EligibilityScheme(
        id=uuid.uuid4(),
        tenant_id=elig_tenant_id,
        name="Test Subsidy Scheme",
        code=f"TSS-{uuid.uuid4().hex[:8]}",
        description="Test scheme for API testing",
        scheme_type="subsidy",
        status=SchemeStatus.ACTIVE.value,
        start_date=datetime.now(timezone.utc) - timedelta(days=30),
        end_date=datetime.now(timezone.utc) + timedelta(days=60),
        application_deadline=datetime.now(timezone.utc) + timedelta(days=30),
        max_beneficiaries=100,
        current_beneficiaries=50,
        benefit_type="voucher",
        benefit_amount=15000.0,
        auto_approve_enabled=True,
        min_score_for_auto_approve=70.0,
        waitlist_enabled=True,
    )
    db_session.add(scheme)
    await db_session.commit()
    await db_session.refresh(scheme)
    return scheme


@pytest_asyncio.fixture
async def elig_rules(db_session: AsyncSession, elig_scheme):
    """Create test rules for the scheme."""
    rules = [
        EligibilityRule(
            id=uuid.uuid4(),
            scheme_id=elig_scheme.id,
            name="KYC Verification",
            field_type=RuleFieldType.KYC.value,
            field_name="status",
            operator=RuleOperator.EQUALS.value,
            value="approved",
            value_type="string",
            is_mandatory=True,
            weight=1.0,
            priority=1,
        ),
        EligibilityRule(
            id=uuid.uuid4(),
            scheme_id=elig_scheme.id,
            name="Minimum Land Size",
            field_type=RuleFieldType.FARM.value,
            field_name="total_acreage",
            operator=RuleOperator.GREATER_THAN_OR_EQUAL.value,
            value="1.0",
            value_type="number",
            is_mandatory=True,
            weight=1.0,
            priority=2,
        ),
        EligibilityRule(
            id=uuid.uuid4(),
            scheme_id=elig_scheme.id,
            name="Eligible County",
            field_type=RuleFieldType.LOCATION.value,
            field_name="county",
            operator=RuleOperator.IN_LIST.value,
            value=json.dumps(["Kiambu", "Nairobi", "Mombasa"]),
            value_type="array",
            is_mandatory=True,
            weight=1.0,
            priority=3,
        ),
    ]

    for rule in rules:
        db_session.add(rule)

    await db_session.commit()
    return rules


# =============================================================================
# Scheme API Tests
# =============================================================================


class TestSchemeAPI:
    """Test suite for Scheme API endpoints."""

    @pytest.mark.asyncio
    async def test_create_scheme(self, client: AsyncClient, elig_tenant_id):
        """Test creating a new scheme."""
        scheme_data = {
            "tenant_id": str(elig_tenant_id),
            "name": "New Test Scheme",
            "code": f"NTS-{uuid.uuid4().hex[:8]}",
            "description": "A new test scheme",
            "scheme_type": "subsidy",
            "max_beneficiaries": 200,
            "benefit_type": "cash",
            "benefit_amount": 20000.0,
        }

        response = await client.post(
            "/api/v1/eligibility/schemes",
            json=scheme_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Test Scheme"
        assert data["status"] == "draft"

    @pytest.mark.asyncio
    async def test_create_scheme_duplicate_code(
        self, client: AsyncClient, elig_scheme, elig_tenant_id
    ):
        """Test that duplicate scheme codes are rejected."""
        scheme_data = {
            "tenant_id": str(elig_tenant_id),
            "name": "Duplicate Scheme",
            "code": elig_scheme.code,  # Duplicate code
            "scheme_type": "subsidy",
        }

        response = await client.post(
            "/api/v1/eligibility/schemes",
            json=scheme_data,
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_schemes(
        self, client: AsyncClient, elig_scheme, elig_tenant_id
    ):
        """Test listing schemes."""
        response = await client.get(
            f"/api/v1/eligibility/schemes?tenant_id={elig_tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_scheme(self, client: AsyncClient, elig_scheme):
        """Test getting a specific scheme."""
        response = await client.get(
            f"/api/v1/eligibility/schemes/{elig_scheme.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(elig_scheme.id)
        assert data["name"] == elig_scheme.name

    @pytest.mark.asyncio
    async def test_get_scheme_not_found(self, client: AsyncClient):
        """Test getting a non-existent scheme."""
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/eligibility/schemes/{fake_id}"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_scheme(self, client: AsyncClient, elig_scheme):
        """Test updating a scheme."""
        update_data = {
            "name": "Updated Scheme Name",
            "description": "Updated description",
        }

        response = await client.patch(
            f"/api/v1/eligibility/schemes/{elig_scheme.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Scheme Name"

    @pytest.mark.asyncio
    async def test_activate_scheme(
        self, client: AsyncClient, db_session: AsyncSession, elig_tenant_id
    ):
        """Test activating a draft scheme."""
        # Create a draft scheme
        scheme = EligibilityScheme(
            id=uuid.uuid4(),
            tenant_id=elig_tenant_id,
            name="Draft Scheme",
            code=f"DS-{uuid.uuid4().hex[:8]}",
            scheme_type="subsidy",
            status=SchemeStatus.DRAFT.value,
        )
        db_session.add(scheme)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/eligibility/schemes/{scheme.id}/activate"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"


# =============================================================================
# Rule API Tests
# =============================================================================


class TestRuleAPI:
    """Test suite for Rule API endpoints."""

    @pytest.mark.asyncio
    async def test_create_rule(self, client: AsyncClient, elig_scheme):
        """Test creating a new rule."""
        rule_data = {
            "scheme_id": str(elig_scheme.id),
            "name": "Test Rule",
            "description": "A test eligibility rule",
            "field_type": "farmer",
            "field_name": "is_active",
            "operator": "equals",
            "value": "true",
            "value_type": "boolean",
            "is_mandatory": True,
        }

        response = await client.post(
            "/api/v1/eligibility/rules",
            json=rule_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Rule"
        assert data["is_mandatory"] is True

    @pytest.mark.asyncio
    async def test_create_rule_scheme_not_found(self, client: AsyncClient):
        """Test creating a rule for non-existent scheme."""
        fake_scheme_id = uuid.uuid4()
        rule_data = {
            "scheme_id": str(fake_scheme_id),
            "name": "Test Rule",
            "field_type": "farmer",
            "field_name": "is_active",
            "operator": "equals",
            "value": "true",
            "value_type": "boolean",
        }

        response = await client.post(
            "/api/v1/eligibility/rules",
            json=rule_data,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_scheme_rules(
        self, client: AsyncClient, elig_scheme, elig_rules
    ):
        """Test listing rules for a scheme."""
        response = await client.get(
            f"/api/v1/eligibility/schemes/{elig_scheme.id}/rules"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(elig_rules)


# =============================================================================
# Assessment API Tests
# =============================================================================


class TestAssessmentAPI:
    """Test suite for Assessment API endpoints."""

    @pytest.mark.asyncio
    async def test_assess_eligibility(
        self,
        client: AsyncClient,
        elig_farmer,
        elig_farm,
        elig_scheme,
        elig_rules,
        elig_tenant_id,
    ):
        """Test assessing farmer eligibility."""
        assessment_data = {
            "farmer_id": str(elig_farmer.id),
            "scheme_id": str(elig_scheme.id),
            "farm_id": str(elig_farm.id),
        }

        response = await client.post(
            f"/api/v1/eligibility/assessments?tenant_id={elig_tenant_id}",
            json=assessment_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["farmer_id"] == str(elig_farmer.id)
        assert data["scheme_id"] == str(elig_scheme.id)
        assert "eligibility_score" in data
        assert "risk_level" in data

    @pytest.mark.asyncio
    async def test_assess_eligibility_farmer_not_found(
        self, client: AsyncClient, elig_scheme, elig_tenant_id
    ):
        """Test assessment with non-existent farmer."""
        fake_farmer_id = uuid.uuid4()
        assessment_data = {
            "farmer_id": str(fake_farmer_id),
            "scheme_id": str(elig_scheme.id),
        }

        response = await client.post(
            f"/api/v1/eligibility/assessments?tenant_id={elig_tenant_id}",
            json=assessment_data,
        )

        assert response.status_code == 400
        assert "Farmer not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_assess_eligibility_scheme_not_active(
        self,
        client: AsyncClient,
        elig_farmer,
        db_session: AsyncSession,
        elig_tenant_id,
    ):
        """Test assessment against inactive scheme."""
        # Create inactive scheme
        inactive_scheme = EligibilityScheme(
            id=uuid.uuid4(),
            tenant_id=elig_tenant_id,
            name="Inactive Scheme",
            code=f"IS-{uuid.uuid4().hex[:8]}",
            scheme_type="subsidy",
            status=SchemeStatus.DRAFT.value,  # Not active
        )
        db_session.add(inactive_scheme)
        await db_session.commit()

        assessment_data = {
            "farmer_id": str(elig_farmer.id),
            "scheme_id": str(inactive_scheme.id),
        }

        response = await client.post(
            f"/api/v1/eligibility/assessments?tenant_id={elig_tenant_id}",
            json=assessment_data,
        )

        assert response.status_code == 400
        assert "not active" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_assessment(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        elig_farmer,
        elig_scheme,
    ):
        """Test getting a specific assessment."""
        # Create assessment
        assessment = EligibilityAssessment(
            id=uuid.uuid4(),
            farmer_id=elig_farmer.id,
            scheme_id=elig_scheme.id,
            status=AssessmentStatus.ELIGIBLE.value,
            eligibility_score=85.0,
            risk_score=20.0,
            risk_level="low",
        )
        db_session.add(assessment)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/eligibility/assessments/{assessment.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(assessment.id)
        assert data["eligibility_score"] == 85.0

    @pytest.mark.asyncio
    async def test_list_farmer_assessments(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        elig_farmer,
        elig_scheme,
    ):
        """Test listing assessments for a farmer."""
        # Create assessments
        for i in range(3):
            assessment = EligibilityAssessment(
                id=uuid.uuid4(),
                farmer_id=elig_farmer.id,
                scheme_id=elig_scheme.id,
                status=AssessmentStatus.ELIGIBLE.value,
            )
            db_session.add(assessment)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/eligibility/farmers/{elig_farmer.id}/assessments"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_make_assessment_decision(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        elig_farmer,
        elig_scheme,
    ):
        """Test making a manual decision on an assessment."""
        # Create assessment pending review
        assessment = EligibilityAssessment(
            id=uuid.uuid4(),
            farmer_id=elig_farmer.id,
            scheme_id=elig_scheme.id,
            status=AssessmentStatus.ELIGIBLE.value,
        )
        db_session.add(assessment)
        await db_session.commit()

        reviewer_id = uuid.uuid4()
        decision_data = {
            "decision": "approved",
            "reason": "All criteria met",
            "notes": "Approved after manual review",
        }

        response = await client.post(
            f"/api/v1/eligibility/assessments/{assessment.id}/decision?reviewer_id={reviewer_id}",
            json=decision_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["final_decision"] == "approved"
        assert data["status"] == "approved"


# =============================================================================
# Waitlist API Tests
# =============================================================================


class TestWaitlistAPI:
    """Test suite for Waitlist API endpoints."""

    @pytest.mark.asyncio
    async def test_get_scheme_waitlist(
        self, client: AsyncClient, elig_scheme
    ):
        """Test getting scheme waitlist."""
        response = await client.get(
            f"/api/v1/eligibility/schemes/{elig_scheme.id}/waitlist"
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["scheme_id"] == str(elig_scheme.id)


# =============================================================================
# Credit Check API Tests
# =============================================================================


class TestCreditCheckAPI:
    """Test suite for Credit Check API endpoints."""

    @pytest.mark.asyncio
    async def test_request_credit_check(
        self, client: AsyncClient, elig_farmer, elig_tenant_id
    ):
        """Test requesting a credit check."""
        request_data = {
            "farmer_id": str(elig_farmer.id),
            "request_type": "full_report",
            "consent_given": True,
            "declared_income": 50000.0,
        }

        response = await client.post(
            f"/api/v1/eligibility/credit-checks?tenant_id={elig_tenant_id}",
            json=request_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["farmer_id"] == str(elig_farmer.id)
        assert "credit_score" in data or "status" in data

    @pytest.mark.asyncio
    async def test_get_farmer_credit_history(
        self, client: AsyncClient, elig_farmer
    ):
        """Test getting credit check history."""
        response = await client.get(
            f"/api/v1/eligibility/farmers/{elig_farmer.id}/credit-checks"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# =============================================================================
# Analytics API Tests
# =============================================================================


class TestAnalyticsAPI:
    """Test suite for Analytics API endpoints."""

    @pytest.mark.asyncio
    async def test_get_scheme_summary(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        elig_scheme,
        elig_farmer,
    ):
        """Test getting scheme eligibility summary."""
        # Create some assessments
        for status in [AssessmentStatus.ELIGIBLE, AssessmentStatus.APPROVED, AssessmentStatus.REJECTED]:
            assessment = EligibilityAssessment(
                id=uuid.uuid4(),
                farmer_id=elig_farmer.id,
                scheme_id=elig_scheme.id,
                status=status.value,
                eligibility_score=75.0,
                risk_score=25.0,
            )
            db_session.add(assessment)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/eligibility/schemes/{elig_scheme.id}/summary"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["scheme_id"] == str(elig_scheme.id)
        assert "total_assessments" in data
        assert "eligible_count" in data
        assert "approved_count" in data
