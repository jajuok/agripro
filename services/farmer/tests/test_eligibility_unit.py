"""Unit tests for Eligibility Assessment Engine."""

import json
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.eligibility import (
    EligibilityScheme,
    EligibilityRule,
    EligibilityRuleGroup,
    EligibilityAssessment,
    CreditCheck,
    RiskAssessment,
    SchemeStatus,
    AssessmentStatus,
    RuleOperator,
    RuleFieldType,
    CreditCheckStatus,
    RiskLevel,
    WorkflowDecision,
)
from app.models.farmer import Farmer, FarmProfile, KYCStatus
from app.schemas.eligibility import (
    EligibilitySchemeCreate,
    EligibilityRuleCreate,
    EligibilityAssessmentRequest,
    CreditCheckRequest,
    RiskLevel as RiskLevelEnum,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_farmer():
    """Create a sample farmer for testing."""
    return Farmer(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        first_name="John",
        last_name="Doe",
        phone_number="+254712345678",
        email="john.doe@example.com",
        national_id="12345678",
        kyc_status=KYCStatus.APPROVED.value,
        kyc_verified_at=datetime.now(timezone.utc),
        county="Kiambu",
        sub_county="Thika",
        ward="Ngoliba",
        village="Kiandutu",
        bank_account="1234567890",
        mobile_money_number="+254712345678",
        is_active=True,
    )


@pytest.fixture
def sample_farm(sample_farmer):
    """Create a sample farm for testing."""
    return FarmProfile(
        id=uuid.uuid4(),
        farmer_id=sample_farmer.id,
        name="Test Farm",
        total_acreage=5.0,
        cultivable_acreage=4.5,
        ownership_type="owned",
        latitude=-1.2921,
        longitude=36.8219,
        county="Kiambu",
        sub_county="Thika",
        soil_type="loam",
        soil_ph=6.5,
        water_source="borehole",
        irrigation_type="drip",
        has_year_round_water=True,
        is_verified=True,
        registration_complete=True,
    )


@pytest.fixture
def sample_scheme():
    """Create a sample eligibility scheme."""
    return EligibilityScheme(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Test Subsidy Scheme",
        code="TSS-2024",
        description="Test scheme for unit testing",
        scheme_type="subsidy",
        status=SchemeStatus.ACTIVE.value,
        start_date=datetime.now(timezone.utc) - timedelta(days=30),
        end_date=datetime.now(timezone.utc) + timedelta(days=60),
        application_deadline=datetime.now(timezone.utc) + timedelta(days=30),
        max_beneficiaries=100,
        current_beneficiaries=50,
        budget_amount=1000000.0,
        benefit_type="voucher",
        benefit_amount=15000.0,
        auto_approve_enabled=True,
        min_score_for_auto_approve=70.0,
        max_risk_for_auto_approve=RiskLevel.MEDIUM.value,
        waitlist_enabled=True,
    )


@pytest.fixture
def sample_credit_check(sample_farmer):
    """Create a sample credit check result."""
    return CreditCheck(
        id=uuid.uuid4(),
        farmer_id=sample_farmer.id,
        reference_number=f"CC-{uuid.uuid4().hex[:12].upper()}",
        request_type="full_report",
        consent_given=True,
        consent_date=datetime.now(timezone.utc),
        status=CreditCheckStatus.COMPLETED.value,
        requested_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        credit_score=720,
        score_band="good",
        total_accounts=5,
        active_accounts=3,
        total_debt=50000.0,
        monthly_obligations=5000.0,
        delinquent_accounts=0,
        defaults_count=0,
        declared_income=30000.0,
        debt_to_income_ratio=16.67,
        valid_until=datetime.now(timezone.utc) + timedelta(days=90),
    )


# =============================================================================
# Rules Engine Tests
# =============================================================================


class TestRulesEngine:
    """Test suite for the Rules Engine."""

    def test_build_evaluation_context(self, sample_farmer, sample_farm):
        """Test building evaluation context from farmer and farm data."""
        from app.services.rules_engine import RulesEngine

        # Mock the database session
        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        context = engine._build_evaluation_context(
            farmer=sample_farmer,
            farm=sample_farm,
            credit_data={"credit_score": 720},
            additional_data={"custom_field": "value"},
        )

        # Verify farmer data
        assert context["farmer"]["first_name"] == "John"
        assert context["farmer"]["last_name"] == "Doe"
        assert context["farmer"]["county"] == "Kiambu"

        # Verify KYC data
        assert context["kyc"]["status"] == KYCStatus.APPROVED.value
        assert context["kyc"]["has_bank_account"] is True

        # Verify farm data
        assert context["farm"]["total_acreage"] == 5.0
        assert context["farm"]["is_verified"] is True

        # Verify credit data
        assert context["credit"]["credit_score"] == 720

        # Verify custom data
        assert context["custom"]["custom_field"] == "value"

    def test_parse_value_number(self):
        """Test parsing numeric values."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        assert engine._parse_value("100", "number") == 100.0
        assert engine._parse_value("3.14", "number") == 3.14
        assert engine._parse_value("42", "integer") == 42

    def test_parse_value_boolean(self):
        """Test parsing boolean values."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        assert engine._parse_value("true", "boolean") is True
        assert engine._parse_value("True", "boolean") is True
        assert engine._parse_value("1", "boolean") is True
        assert engine._parse_value("yes", "boolean") is True
        assert engine._parse_value("false", "boolean") is False
        assert engine._parse_value("0", "boolean") is False

    def test_parse_value_array(self):
        """Test parsing array values."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        result = engine._parse_value('["Kiambu", "Nairobi", "Mombasa"]', "array")
        assert result == ["Kiambu", "Nairobi", "Mombasa"]

    def test_compare_values_equals(self):
        """Test equals comparison."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        assert engine._compare_values("approved", "approved", "equals") is True
        assert engine._compare_values("APPROVED", "approved", "equals") is True
        assert engine._compare_values("pending", "approved", "equals") is False

    def test_compare_values_greater_than(self):
        """Test greater than comparison."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        assert engine._compare_values(5.0, 3.0, "greater_than") is True
        assert engine._compare_values(3.0, 5.0, "greater_than") is False
        assert engine._compare_values(5.0, 5.0, "greater_than") is False
        assert engine._compare_values(5.0, 5.0, "greater_than_or_equal") is True

    def test_compare_values_in_list(self):
        """Test in_list comparison."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        counties = ["Kiambu", "Nairobi", "Mombasa"]
        assert engine._compare_values("Kiambu", counties, "in_list") is True
        assert engine._compare_values("kiambu", counties, "in_list") is True  # Case insensitive
        assert engine._compare_values("Nakuru", counties, "in_list") is False

    def test_compare_values_between(self):
        """Test between comparison."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        assert engine._compare_values(5.0, [1.0, 10.0], "between") is True
        assert engine._compare_values(1.0, [1.0, 10.0], "between") is True
        assert engine._compare_values(10.0, [1.0, 10.0], "between") is True
        assert engine._compare_values(0.5, [1.0, 10.0], "between") is False
        assert engine._compare_values(15.0, [1.0, 10.0], "between") is False

    def test_compare_values_null_checks(self):
        """Test null checks."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        assert engine._compare_values(None, None, "is_null") is True
        assert engine._compare_values("value", None, "is_null") is False
        assert engine._compare_values("value", None, "is_not_null") is True
        assert engine._compare_values(None, None, "is_not_null") is False

    def test_evaluate_rule_passed(self, sample_farmer, sample_farm):
        """Test evaluating a passing rule."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        rule = EligibilityRule(
            id=uuid.uuid4(),
            scheme_id=uuid.uuid4(),
            name="Minimum Land Size",
            field_type=RuleFieldType.FARM.value,
            field_name="total_acreage",
            operator=RuleOperator.GREATER_THAN_OR_EQUAL.value,
            value="2.0",
            value_type="number",
            is_mandatory=True,
            is_exclusion=False,
            weight=1.0,
            pass_message="Farm meets minimum size requirement",
            fail_message="Farm is too small",
        )

        context = engine._build_evaluation_context(sample_farmer, sample_farm)
        result = engine._evaluate_rule(rule, context)

        assert result.passed is True
        assert result.rule_name == "Minimum Land Size"
        assert "5.0" in result.actual_value

    def test_evaluate_rule_failed(self, sample_farmer, sample_farm):
        """Test evaluating a failing rule."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        rule = EligibilityRule(
            id=uuid.uuid4(),
            scheme_id=uuid.uuid4(),
            name="Maximum Land Size",
            field_type=RuleFieldType.FARM.value,
            field_name="total_acreage",
            operator=RuleOperator.LESS_THAN.value,
            value="3.0",
            value_type="number",
            is_mandatory=True,
            is_exclusion=False,
            weight=1.0,
            fail_message="Farm is too large",
        )

        context = engine._build_evaluation_context(sample_farmer, sample_farm)
        result = engine._evaluate_rule(rule, context)

        assert result.passed is False
        assert "too large" in result.message

    def test_exclusion_rule(self, sample_farmer, sample_farm):
        """Test exclusion rule (match = exclude)."""
        from app.services.rules_engine import RulesEngine

        mock_db = AsyncMock()
        engine = RulesEngine(mock_db)

        # Exclusion rule: exclude if county is "Excluded County"
        rule = EligibilityRule(
            id=uuid.uuid4(),
            scheme_id=uuid.uuid4(),
            name="Excluded Counties",
            field_type=RuleFieldType.LOCATION.value,
            field_name="county",
            operator=RuleOperator.EQUALS.value,
            value="Excluded County",
            value_type="string",
            is_mandatory=True,
            is_exclusion=True,  # This is an exclusion rule
            weight=1.0,
        )

        context = engine._build_evaluation_context(sample_farmer, sample_farm)
        result = engine._evaluate_rule(rule, context)

        # Since farmer is in Kiambu (not Excluded County), the exclusion doesn't apply
        # So the rule should pass
        assert result.passed is True


# =============================================================================
# Credit Service Tests
# =============================================================================


class TestCreditService:
    """Test suite for the Credit Bureau Service."""

    def test_get_score_band(self):
        """Test credit score band calculation."""
        from app.services.credit_service import CreditBureauService

        mock_db = AsyncMock()
        service = CreditBureauService(mock_db)

        assert service._get_score_band(800) == "excellent"
        assert service._get_score_band(750) == "excellent"
        assert service._get_score_band(720) == "good"
        assert service._get_score_band(700) == "good"
        assert service._get_score_band(680) == "fair"
        assert service._get_score_band(650) == "fair"
        assert service._get_score_band(580) == "poor"
        assert service._get_score_band(500) == "very_poor"
        assert service._get_score_band(None) is None

    def test_get_credit_data_for_rules(self, sample_credit_check):
        """Test formatting credit data for rules engine."""
        from app.services.credit_service import CreditBureauService

        mock_db = AsyncMock()
        service = CreditBureauService(mock_db)

        data = service.get_credit_data_for_rules(sample_credit_check)

        assert data["credit_score"] == 720
        assert data["score_band"] == "good"
        assert data["defaults_count"] == 0
        assert data["has_defaults"] is False
        assert data["has_delinquencies"] is False
        assert data["debt_to_income_ratio"] == 16.67

    def test_get_credit_data_for_rules_no_data(self):
        """Test formatting credit data when no check exists."""
        from app.services.credit_service import CreditBureauService

        mock_db = AsyncMock()
        service = CreditBureauService(mock_db)

        data = service.get_credit_data_for_rules(None)
        assert data == {}


# =============================================================================
# Risk Scoring Tests
# =============================================================================


class TestRiskScoringService:
    """Test suite for the Risk Scoring Service."""

    def test_risk_level_thresholds(self):
        """Test risk level determination from scores."""
        from app.services.risk_scoring import RiskScoringService

        mock_db = AsyncMock()
        service = RiskScoringService(mock_db)

        assert service._get_risk_level(10) == RiskLevel.LOW
        assert service._get_risk_level(24) == RiskLevel.LOW
        assert service._get_risk_level(25) == RiskLevel.MEDIUM
        assert service._get_risk_level(49) == RiskLevel.MEDIUM
        assert service._get_risk_level(50) == RiskLevel.HIGH
        assert service._get_risk_level(74) == RiskLevel.HIGH
        assert service._get_risk_level(75) == RiskLevel.VERY_HIGH
        assert service._get_risk_level(100) == RiskLevel.VERY_HIGH

    def test_calculate_credit_risk_good_score(self, sample_credit_check):
        """Test credit risk calculation with good score."""
        from app.services.risk_scoring import RiskScoringService

        mock_db = AsyncMock()
        service = RiskScoringService(mock_db)

        risk, factors = service._calculate_credit_risk(sample_credit_check)

        # Good credit score (720) should result in low risk
        credit_score_factor = next(f for f in factors if f.factor_code == "credit_score")
        assert credit_score_factor.normalized_score <= 30  # Low risk score

        # No defaults should result in 0 risk
        defaults_factor = next(f for f in factors if f.factor_code == "defaults")
        assert defaults_factor.normalized_score == 0

    def test_calculate_credit_risk_no_data(self):
        """Test credit risk calculation with no credit data."""
        from app.services.risk_scoring import RiskScoringService

        mock_db = AsyncMock()
        service = RiskScoringService(mock_db)

        risk, factors = service._calculate_credit_risk(None)

        # No credit data should assign moderate risk
        assert len(factors) == 1
        assert factors[0].factor_code == "credit_data_missing"
        assert factors[0].normalized_score == 50.0

    def test_calculate_yield_performance(self):
        """Test yield performance calculation."""
        from app.services.risk_scoring import RiskScoringService
        from app.models.farmer import CropRecord

        mock_db = AsyncMock()
        service = RiskScoringService(mock_db)

        # Create mock crop records
        records = [
            MagicMock(expected_yield_kg=1000, actual_yield_kg=900),  # 90%
            MagicMock(expected_yield_kg=1000, actual_yield_kg=1100),  # 110%
            MagicMock(expected_yield_kg=1000, actual_yield_kg=800),  # 80%
        ]

        performance = service._calculate_yield_performance(records)

        # Average should be (90 + 110 + 80) / 3 = 93.33%
        assert 93 <= performance <= 94

    def test_generate_recommendations_low_risk(self):
        """Test recommendation generation for low risk."""
        from app.services.risk_scoring import RiskScoringService

        mock_db = AsyncMock()
        service = RiskScoringService(mock_db)

        recommendations = service._generate_recommendations(RiskLevel.LOW, [])
        assert any("standard" in r.lower() for r in recommendations)

    def test_generate_recommendations_high_risk(self):
        """Test recommendation generation for high risk."""
        from app.services.risk_scoring import RiskScoringService

        mock_db = AsyncMock()
        service = RiskScoringService(mock_db)

        recommendations = service._generate_recommendations(RiskLevel.HIGH, ["High credit risk"])
        assert any("manual review" in r.lower() for r in recommendations)


# =============================================================================
# Eligibility Service Tests
# =============================================================================


class TestEligibilityService:
    """Test suite for the main Eligibility Service."""

    def test_determine_outcome_auto_approve(self, sample_scheme):
        """Test auto-approval decision."""
        from app.services.eligibility_service import EligibilityService

        mock_db = AsyncMock()
        service = EligibilityService(mock_db)

        status, decision = service._determine_assessment_outcome(
            scheme=sample_scheme,
            eligibility_score=85.0,
            mandatory_passed=True,
            risk_level=RiskLevel.LOW,
        )

        assert status == AssessmentStatus.APPROVED
        assert decision == WorkflowDecision.AUTO_APPROVE

    def test_determine_outcome_mandatory_failed(self, sample_scheme):
        """Test rejection when mandatory rules fail."""
        from app.services.eligibility_service import EligibilityService

        mock_db = AsyncMock()
        service = EligibilityService(mock_db)

        status, decision = service._determine_assessment_outcome(
            scheme=sample_scheme,
            eligibility_score=85.0,
            mandatory_passed=False,  # Mandatory rules failed
            risk_level=RiskLevel.LOW,
        )

        assert status == AssessmentStatus.NOT_ELIGIBLE
        assert decision == WorkflowDecision.AUTO_REJECT

    def test_determine_outcome_high_risk(self, sample_scheme):
        """Test manual review for high risk."""
        from app.services.eligibility_service import EligibilityService

        mock_db = AsyncMock()
        service = EligibilityService(mock_db)

        status, decision = service._determine_assessment_outcome(
            scheme=sample_scheme,
            eligibility_score=85.0,
            mandatory_passed=True,
            risk_level=RiskLevel.HIGH,  # High risk
        )

        assert status == AssessmentStatus.ELIGIBLE
        assert decision == WorkflowDecision.MANUAL_REVIEW

    def test_determine_outcome_low_score(self, sample_scheme):
        """Test manual review for low eligibility score."""
        from app.services.eligibility_service import EligibilityService

        mock_db = AsyncMock()
        service = EligibilityService(mock_db)

        status, decision = service._determine_assessment_outcome(
            scheme=sample_scheme,
            eligibility_score=50.0,  # Below auto-approve threshold
            mandatory_passed=True,
            risk_level=RiskLevel.LOW,
        )

        assert status == AssessmentStatus.ELIGIBLE
        assert decision == WorkflowDecision.MANUAL_REVIEW

    def test_determine_outcome_capacity_full(self, sample_scheme):
        """Test waitlisting when scheme is at capacity."""
        from app.services.eligibility_service import EligibilityService

        mock_db = AsyncMock()
        service = EligibilityService(mock_db)

        # Set scheme to full capacity
        sample_scheme.current_beneficiaries = sample_scheme.max_beneficiaries

        status, decision = service._determine_assessment_outcome(
            scheme=sample_scheme,
            eligibility_score=85.0,
            mandatory_passed=True,
            risk_level=RiskLevel.LOW,
        )

        assert status == AssessmentStatus.WAITLISTED
        assert decision == WorkflowDecision.WAITLIST


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestSchemaValidation:
    """Test suite for Pydantic schema validation."""

    def test_scheme_create_validation(self):
        """Test scheme creation schema validation."""
        data = EligibilitySchemeCreate(
            tenant_id=uuid.uuid4(),
            name="Test Scheme",
            code="TS-001",
            description="A test scheme",
            scheme_type="subsidy",
            max_beneficiaries=100,
            benefit_type="voucher",
            benefit_amount=15000.0,
        )

        assert data.name == "Test Scheme"
        assert data.code == "TS-001"
        assert data.auto_approve_enabled is False  # Default

    def test_rule_create_validation(self):
        """Test rule creation schema validation."""
        data = EligibilityRuleCreate(
            scheme_id=uuid.uuid4(),
            name="Min Land Size",
            description="Minimum land size requirement",
            field_type=RuleFieldType.FARM,
            field_name="total_acreage",
            operator=RuleOperator.GREATER_THAN_OR_EQUAL,
            value="2.0",
            value_type="number",
        )

        assert data.name == "Min Land Size"
        assert data.field_type == RuleFieldType.FARM
        assert data.is_mandatory is True  # Default

    def test_assessment_request_validation(self):
        """Test assessment request schema validation."""
        farmer_id = uuid.uuid4()
        scheme_id = uuid.uuid4()

        data = EligibilityAssessmentRequest(
            farmer_id=farmer_id,
            scheme_id=scheme_id,
        )

        assert data.farmer_id == farmer_id
        assert data.scheme_id == scheme_id
        assert data.farm_id is None  # Optional


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestHelperFunctions:
    """Test suite for rule builder helper functions."""

    def test_create_land_size_rule_range(self):
        """Test creating land size rule with range."""
        from app.services.rules_engine import create_land_size_rule

        scheme_id = uuid.uuid4()
        rule_data = create_land_size_rule(
            scheme_id=scheme_id,
            min_acreage=1.0,
            max_acreage=10.0,
        )

        assert rule_data["scheme_id"] == scheme_id
        assert rule_data["operator"] == RuleOperator.BETWEEN.value
        assert json.loads(rule_data["value"]) == [1.0, 10.0]

    def test_create_land_size_rule_minimum(self):
        """Test creating land size rule with minimum only."""
        from app.services.rules_engine import create_land_size_rule

        scheme_id = uuid.uuid4()
        rule_data = create_land_size_rule(
            scheme_id=scheme_id,
            min_acreage=2.0,
        )

        assert rule_data["operator"] == RuleOperator.GREATER_THAN_OR_EQUAL.value
        assert rule_data["value"] == "2.0"

    def test_create_kyc_status_rule(self):
        """Test creating KYC status rule."""
        from app.services.rules_engine import create_kyc_status_rule

        scheme_id = uuid.uuid4()
        rule_data = create_kyc_status_rule(
            scheme_id=scheme_id,
            required_status="approved",
        )

        assert rule_data["field_type"] == RuleFieldType.KYC.value
        assert rule_data["field_name"] == "status"
        assert rule_data["value"] == "approved"

    def test_create_location_rule(self):
        """Test creating location eligibility rule."""
        from app.services.rules_engine import create_location_rule

        scheme_id = uuid.uuid4()
        counties = ["Kiambu", "Nairobi", "Mombasa"]
        rule_data = create_location_rule(
            scheme_id=scheme_id,
            allowed_counties=counties,
        )

        assert rule_data["field_type"] == RuleFieldType.LOCATION.value
        assert rule_data["operator"] == RuleOperator.IN_LIST.value
        assert json.loads(rule_data["value"]) == counties

    def test_create_credit_score_rule(self):
        """Test creating credit score rule."""
        from app.services.rules_engine import create_credit_score_rule

        scheme_id = uuid.uuid4()
        rule_data = create_credit_score_rule(
            scheme_id=scheme_id,
            min_score=600,
            is_mandatory=False,
            weight=0.5,
        )

        assert rule_data["field_type"] == RuleFieldType.CREDIT.value
        assert rule_data["field_name"] == "credit_score"
        assert rule_data["value"] == "600"
        assert rule_data["is_mandatory"] is False
        assert rule_data["weight"] == 0.5
