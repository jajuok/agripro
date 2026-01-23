"""Eligibility Assessment Engine Schemas (Phase 2.3)."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================


class SchemeStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    ARCHIVED = "archived"


class AssessmentStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    WAITLISTED = "waitlisted"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RuleOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    REGEX_MATCH = "regex_match"


class RuleFieldType(str, Enum):
    FARMER = "farmer"
    FARM = "farm"
    KYC = "kyc"
    CREDIT = "credit"
    LOCATION = "location"
    CROP = "crop"
    CUSTOM = "custom"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class WorkflowDecision(str, Enum):
    AUTO_APPROVE = "auto_approve"
    AUTO_REJECT = "auto_reject"
    MANUAL_REVIEW = "manual_review"
    WAITLIST = "waitlist"


class CreditCheckStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


# =============================================================================
# Scheme Schemas
# =============================================================================


class EligibilitySchemeBase(BaseModel):
    """Base scheme schema."""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    scheme_type: str = Field(..., max_length=50)


class EligibilitySchemeCreate(EligibilitySchemeBase):
    """Create scheme schema."""
    tenant_id: UUID
    start_date: datetime | None = None
    end_date: datetime | None = None
    application_deadline: datetime | None = None
    max_beneficiaries: int | None = None
    budget_amount: float | None = None
    benefit_type: str | None = None
    benefit_amount: float | None = None
    benefit_description: str | None = None
    auto_approve_enabled: bool = False
    min_score_for_auto_approve: float | None = None
    max_risk_for_auto_approve: RiskLevel | None = None
    waitlist_enabled: bool = True
    waitlist_capacity: int | None = None


class EligibilitySchemeUpdate(BaseModel):
    """Update scheme schema."""
    name: str | None = None
    description: str | None = None
    status: SchemeStatus | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    application_deadline: datetime | None = None
    max_beneficiaries: int | None = None
    budget_amount: float | None = None
    benefit_type: str | None = None
    benefit_amount: float | None = None
    benefit_description: str | None = None
    auto_approve_enabled: bool | None = None
    min_score_for_auto_approve: float | None = None
    max_risk_for_auto_approve: RiskLevel | None = None
    waitlist_enabled: bool | None = None
    waitlist_capacity: int | None = None


class EligibilitySchemeResponse(EligibilitySchemeBase):
    """Scheme response schema."""
    id: UUID
    tenant_id: UUID
    status: str
    start_date: datetime | None
    end_date: datetime | None
    application_deadline: datetime | None
    max_beneficiaries: int | None
    current_beneficiaries: int
    budget_amount: float | None
    disbursed_amount: float
    benefit_type: str | None
    benefit_amount: float | None
    auto_approve_enabled: bool
    waitlist_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EligibilitySchemeListResponse(BaseModel):
    """Paginated scheme list."""
    items: list[EligibilitySchemeResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# Rule Schemas
# =============================================================================


class EligibilityRuleBase(BaseModel):
    """Base rule schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    field_type: RuleFieldType
    field_name: str = Field(..., max_length=100)
    field_path: str | None = None
    operator: RuleOperator
    value: str | None = None
    value_type: str = "string"


class EligibilityRuleCreate(EligibilityRuleBase):
    """Create rule schema."""
    scheme_id: UUID
    rule_group_id: UUID | None = None
    is_mandatory: bool = True
    is_exclusion: bool = False
    weight: float = 1.0
    priority: int = 1
    pass_message: str | None = None
    fail_message: str | None = None


class EligibilityRuleUpdate(BaseModel):
    """Update rule schema."""
    name: str | None = None
    description: str | None = None
    field_type: RuleFieldType | None = None
    field_name: str | None = None
    field_path: str | None = None
    operator: RuleOperator | None = None
    value: str | None = None
    value_type: str | None = None
    is_mandatory: bool | None = None
    is_exclusion: bool | None = None
    weight: float | None = None
    priority: int | None = None
    pass_message: str | None = None
    fail_message: str | None = None
    is_active: bool | None = None


class EligibilityRuleResponse(EligibilityRuleBase):
    """Rule response schema."""
    id: UUID
    scheme_id: UUID
    rule_group_id: UUID | None
    is_mandatory: bool
    is_exclusion: bool
    weight: float
    priority: int
    pass_message: str | None
    fail_message: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EligibilityRuleGroupBase(BaseModel):
    """Base rule group schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    logic_operator: str = "AND"
    priority: int = 1
    is_mandatory: bool = True
    weight: float = 1.0


class EligibilityRuleGroupCreate(EligibilityRuleGroupBase):
    """Create rule group schema."""
    scheme_id: UUID


class EligibilityRuleGroupResponse(EligibilityRuleGroupBase):
    """Rule group response schema."""
    id: UUID
    scheme_id: UUID
    is_active: bool
    created_at: datetime
    rules: list[EligibilityRuleResponse] = []

    model_config = {"from_attributes": True}


# =============================================================================
# Assessment Schemas
# =============================================================================


class EligibilityAssessmentRequest(BaseModel):
    """Request to assess farmer eligibility."""
    farmer_id: UUID
    scheme_id: UUID
    farm_id: UUID | None = None


class RuleEvaluationResult(BaseModel):
    """Result of a single rule evaluation."""
    rule_id: UUID
    rule_name: str
    passed: bool
    actual_value: str | None
    expected_value: str | None
    message: str | None
    is_mandatory: bool
    weight: float


class EligibilityAssessmentResponse(BaseModel):
    """Eligibility assessment response."""
    id: UUID
    farmer_id: UUID
    scheme_id: UUID
    farm_id: UUID | None
    status: str
    assessment_date: datetime | None
    eligibility_score: float | None
    risk_score: float | None
    risk_level: str | None
    credit_score: float | None
    rules_passed: int
    rules_failed: int
    mandatory_rules_passed: bool | None
    rule_results: list[RuleEvaluationResult] | None
    workflow_decision: str | None
    final_decision: str | None
    decision_reason: str | None
    waitlist_position: int | None
    valid_until: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EligibilityAssessmentListResponse(BaseModel):
    """Paginated assessment list."""
    items: list[EligibilityAssessmentResponse]
    total: int
    page: int
    page_size: int


class AssessmentDecisionRequest(BaseModel):
    """Manual decision on an assessment."""
    decision: str = Field(..., pattern="^(approved|rejected)$")
    reason: str | None = None
    notes: str | None = None


# =============================================================================
# Credit Check Schemas
# =============================================================================


class CreditCheckRequest(BaseModel):
    """Request for credit check."""
    farmer_id: UUID
    assessment_id: UUID | None = None
    request_type: str = "full_report"
    consent_given: bool = True
    declared_income: float | None = None


class CreditCheckResponse(BaseModel):
    """Credit check response."""
    id: UUID
    farmer_id: UUID
    assessment_id: UUID | None
    reference_number: str | None
    status: str
    credit_score: int | None
    score_band: str | None
    total_accounts: int | None
    active_accounts: int | None
    total_debt: float | None
    monthly_obligations: float | None
    delinquent_accounts: int | None
    defaults_count: int | None
    debt_to_income_ratio: float | None
    requested_at: datetime
    completed_at: datetime | None
    valid_until: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}


# =============================================================================
# Risk Assessment Schemas
# =============================================================================


class RiskFactorScore(BaseModel):
    """Individual risk factor score."""
    factor_code: str
    factor_name: str
    raw_value: float | str | None
    normalized_score: float
    weight: float
    weighted_score: float
    category: str


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response."""
    id: UUID
    farmer_id: UUID
    assessment_id: UUID | None
    assessed_at: datetime
    total_risk_score: float
    risk_level: str
    confidence_score: float | None
    credit_risk_score: float | None
    performance_risk_score: float | None
    external_risk_score: float | None
    fraud_risk_score: float | None
    factor_scores: list[RiskFactorScore] | None
    fraud_indicators: list[str] | None
    risk_flags: list[str] | None
    recommendations: list[str] | None
    model_version: str | None
    valid_until: datetime | None

    model_config = {"from_attributes": True}


# =============================================================================
# Waitlist Schemas
# =============================================================================


class WaitlistEntryResponse(BaseModel):
    """Waitlist entry response."""
    id: UUID
    scheme_id: UUID
    farmer_id: UUID
    assessment_id: UUID
    position: int
    original_position: int
    eligibility_score: float
    risk_score: float | None
    status: str
    offered_at: datetime | None
    offer_expires_at: datetime | None
    added_at: datetime

    model_config = {"from_attributes": True}


class WaitlistResponse(BaseModel):
    """Paginated waitlist."""
    items: list[WaitlistEntryResponse]
    total: int
    scheme_id: UUID
    scheme_name: str


class WaitlistOfferResponse(BaseModel):
    """Response to waitlist offer."""
    accept: bool


# =============================================================================
# Review Queue Schemas
# =============================================================================


class ReviewQueueItemResponse(BaseModel):
    """Review queue item response."""
    id: UUID
    assessment_id: UUID
    farmer_id: UUID
    farmer_name: str
    scheme_id: UUID
    scheme_name: str
    priority: int
    queue_reason: str
    queue_category: str | None
    status: str
    assigned_to: UUID | None
    sla_due_at: datetime | None
    is_overdue: bool
    queued_at: datetime

    model_config = {"from_attributes": True}


class ReviewQueueListResponse(BaseModel):
    """Paginated review queue."""
    items: list[ReviewQueueItemResponse]
    total: int
    pending_count: int
    overdue_count: int


class ReviewQueueAssignRequest(BaseModel):
    """Assign review queue item."""
    reviewer_id: UUID


# =============================================================================
# Batch Operations
# =============================================================================


class BatchAssessmentRequest(BaseModel):
    """Request for batch eligibility assessment."""
    scheme_id: UUID
    farmer_ids: list[UUID] | None = None
    filters: dict | None = None  # Filter criteria for selecting farmers


class BatchAssessmentResponse(BaseModel):
    """Batch assessment response."""
    total_processed: int
    eligible_count: int
    not_eligible_count: int
    error_count: int
    assessment_ids: list[UUID]


# =============================================================================
# Summary and Analytics Schemas
# =============================================================================


class SchemeEligibilitySummary(BaseModel):
    """Summary of scheme eligibility statistics."""
    scheme_id: UUID
    scheme_name: str
    total_assessments: int
    eligible_count: int
    not_eligible_count: int
    approved_count: int
    rejected_count: int
    pending_review_count: int
    waitlisted_count: int
    average_eligibility_score: float | None
    average_risk_score: float | None


class FarmerEligibilitySummary(BaseModel):
    """Summary of farmer's eligibility across schemes."""
    farmer_id: UUID
    farmer_name: str
    total_schemes_assessed: int
    eligible_schemes: int
    approved_schemes: int
    pending_schemes: int
    waitlisted_schemes: int
    latest_risk_level: str | None
    latest_credit_score: int | None
