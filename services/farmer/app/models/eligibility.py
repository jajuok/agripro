"""Eligibility Assessment Engine Models (Phase 2.3)."""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_types import JSONBCompatible
from app.models.farmer import Base

if TYPE_CHECKING:
    from app.models.farmer import Farmer, FarmProfile


class SchemeStatus(str, Enum):
    """Scheme status."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    ARCHIVED = "archived"


class AssessmentStatus(str, Enum):
    """Eligibility assessment status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    WAITLISTED = "waitlisted"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RuleOperator(str, Enum):
    """Rule comparison operators."""

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
    """Field types for rules."""

    FARMER = "farmer"  # Farmer profile fields
    FARM = "farm"  # Farm profile fields
    KYC = "kyc"  # KYC status fields
    CREDIT = "credit"  # Credit check fields
    LOCATION = "location"  # Geographic fields
    CROP = "crop"  # Crop history fields
    CUSTOM = "custom"  # Custom computed fields


class CreditCheckStatus(str, Enum):
    """Credit check status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class RiskLevel(str, Enum):
    """Risk level classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class WorkflowDecision(str, Enum):
    """Workflow decision types."""

    AUTO_APPROVE = "auto_approve"
    AUTO_REJECT = "auto_reject"
    MANUAL_REVIEW = "manual_review"
    WAITLIST = "waitlist"


# =============================================================================
# Scheme and Rule Models
# =============================================================================


class EligibilityScheme(Base):
    """Agricultural scheme definition with eligibility criteria."""

    __tablename__ = "eligibility_schemes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)

    # Scheme details
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    scheme_type: Mapped[str] = mapped_column(String(50))  # subsidy, loan, insurance, support

    # Status and dates
    status: Mapped[str] = mapped_column(String(20), default=SchemeStatus.DRAFT.value)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    application_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Capacity
    max_beneficiaries: Mapped[int | None] = mapped_column(Integer)
    current_beneficiaries: Mapped[int] = mapped_column(Integer, default=0)
    budget_amount: Mapped[float | None] = mapped_column(Float)
    disbursed_amount: Mapped[float] = mapped_column(Float, default=0.0)

    # Benefit details
    benefit_type: Mapped[str | None] = mapped_column(String(50))  # cash, voucher, input, service
    benefit_amount: Mapped[float | None] = mapped_column(Float)
    benefit_description: Mapped[str | None] = mapped_column(Text)

    # Auto-approval settings
    auto_approve_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    min_score_for_auto_approve: Mapped[float | None] = mapped_column(Float)
    max_risk_for_auto_approve: Mapped[str | None] = mapped_column(String(20))  # RiskLevel

    # Waitlist settings
    waitlist_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    waitlist_capacity: Mapped[int | None] = mapped_column(Integer)

    # Metadata
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    rules: Mapped[list["EligibilityRule"]] = relationship(
        "EligibilityRule", back_populates="scheme", cascade="all, delete-orphan"
    )
    rule_groups: Mapped[list["EligibilityRuleGroup"]] = relationship(
        "EligibilityRuleGroup", back_populates="scheme", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["EligibilityAssessment"]] = relationship(
        "EligibilityAssessment", back_populates="scheme"
    )


class EligibilityRuleGroup(Base):
    """Group of rules with AND/OR logic."""

    __tablename__ = "eligibility_rule_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_schemes.id", ondelete="CASCADE")
    )

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    logic_operator: Mapped[str] = mapped_column(String(10), default="AND")  # AND, OR
    priority: Mapped[int] = mapped_column(Integer, default=1)  # Evaluation order
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)  # Must pass for eligibility
    weight: Mapped[float] = mapped_column(Float, default=1.0)  # Weight in scoring

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    scheme: Mapped["EligibilityScheme"] = relationship(
        "EligibilityScheme", back_populates="rule_groups"
    )
    rules: Mapped[list["EligibilityRule"]] = relationship(
        "EligibilityRule", back_populates="rule_group", cascade="all, delete-orphan"
    )


class EligibilityRule(Base):
    """Individual eligibility rule definition."""

    __tablename__ = "eligibility_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_schemes.id", ondelete="CASCADE")
    )
    rule_group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_rule_groups.id", ondelete="SET NULL")
    )

    # Rule definition
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)

    # Field configuration
    field_type: Mapped[str] = mapped_column(String(20))  # RuleFieldType
    field_name: Mapped[str] = mapped_column(String(100))  # e.g., "total_acreage", "kyc_status"
    field_path: Mapped[str | None] = mapped_column(String(200))  # JSON path for nested fields

    # Comparison
    operator: Mapped[str] = mapped_column(String(30))  # RuleOperator
    value: Mapped[str | None] = mapped_column(Text)  # JSON-encoded comparison value
    value_type: Mapped[str] = mapped_column(
        String(20), default="string"
    )  # string, number, boolean, array, date

    # Rule behavior
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    is_exclusion: Mapped[bool] = mapped_column(Boolean, default=False)  # If true, match = exclude
    weight: Mapped[float] = mapped_column(Float, default=1.0)  # Weight for scoring
    priority: Mapped[int] = mapped_column(Integer, default=1)  # Evaluation order

    # Messages
    pass_message: Mapped[str | None] = mapped_column(String(500))
    fail_message: Mapped[str | None] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    scheme: Mapped["EligibilityScheme"] = relationship("EligibilityScheme", back_populates="rules")
    rule_group: Mapped["EligibilityRuleGroup | None"] = relationship(
        "EligibilityRuleGroup", back_populates="rules"
    )


# =============================================================================
# Assessment and Application Models
# =============================================================================


class EligibilityAssessment(Base):
    """Farmer eligibility assessment for a scheme."""

    __tablename__ = "eligibility_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE"), index=True
    )
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_schemes.id", ondelete="CASCADE"), index=True
    )
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farm_profiles.id", ondelete="SET NULL")
    )

    # Assessment status
    status: Mapped[str] = mapped_column(String(20), default=AssessmentStatus.PENDING.value)
    assessment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Scores
    eligibility_score: Mapped[float | None] = mapped_column(Float)
    risk_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(String(20))  # RiskLevel
    credit_score: Mapped[float | None] = mapped_column(Float)

    # Rule evaluation results
    rules_passed: Mapped[int] = mapped_column(Integer, default=0)
    rules_failed: Mapped[int] = mapped_column(Integer, default=0)
    mandatory_rules_passed: Mapped[bool | None] = mapped_column(Boolean)
    rule_results: Mapped[dict | None] = mapped_column(JSONBCompatible)  # Detailed per-rule results

    # Decision
    workflow_decision: Mapped[str | None] = mapped_column(String(20))  # WorkflowDecision
    final_decision: Mapped[str | None] = mapped_column(String(20))  # approved, rejected
    decision_reason: Mapped[str | None] = mapped_column(Text)
    decision_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Waitlist
    waitlist_position: Mapped[int | None] = mapped_column(Integer)
    waitlisted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Expiry
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", backref="eligibility_assessments")
    scheme: Mapped["EligibilityScheme"] = relationship(
        "EligibilityScheme", back_populates="assessments"
    )
    farm: Mapped["FarmProfile | None"] = relationship(
        "FarmProfile", backref="eligibility_assessments"
    )
    credit_checks: Mapped[list["CreditCheck"]] = relationship(
        "CreditCheck", back_populates="assessment", cascade="all, delete-orphan"
    )
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(
        "RiskAssessment", back_populates="assessment", cascade="all, delete-orphan"
    )


# =============================================================================
# Credit Bureau Integration Models
# =============================================================================


class CreditBureauProvider(Base):
    """Credit bureau provider configuration."""

    __tablename__ = "credit_bureau_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)

    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    provider_type: Mapped[str] = mapped_column(String(50))  # transunion, experian, equifax, local

    # API configuration (encrypted)
    api_base_url: Mapped[str | None] = mapped_column(String(500))
    api_key_encrypted: Mapped[str | None] = mapped_column(Text)
    api_config: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)  # Order of provider usage
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    retry_count: Mapped[int] = mapped_column(Integer, default=3)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CreditCheck(Base):
    """Credit check record for a farmer."""

    __tablename__ = "credit_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE"), index=True
    )
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_assessments.id", ondelete="SET NULL")
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("credit_bureau_providers.id", ondelete="SET NULL")
    )

    # Request info
    reference_number: Mapped[str | None] = mapped_column(String(100), unique=True)
    request_type: Mapped[str] = mapped_column(
        String(50)
    )  # full_report, score_only, identity_verify
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Status
    status: Mapped[str] = mapped_column(String(20), default=CreditCheckStatus.PENDING.value)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Results
    credit_score: Mapped[int | None] = mapped_column(Integer)
    score_band: Mapped[str | None] = mapped_column(
        String(20)
    )  # excellent, good, fair, poor, very_poor
    total_accounts: Mapped[int | None] = mapped_column(Integer)
    active_accounts: Mapped[int | None] = mapped_column(Integer)
    total_debt: Mapped[float | None] = mapped_column(Float)
    monthly_obligations: Mapped[float | None] = mapped_column(Float)
    delinquent_accounts: Mapped[int | None] = mapped_column(Integer)
    defaults_count: Mapped[int | None] = mapped_column(Integer)

    # Debt-to-income calculation
    declared_income: Mapped[float | None] = mapped_column(Float)
    debt_to_income_ratio: Mapped[float | None] = mapped_column(Float)

    # Full response (encrypted/hashed sensitive data)
    response_data: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Error handling
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)

    # Validity
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", backref="credit_checks")
    assessment: Mapped["EligibilityAssessment | None"] = relationship(
        "EligibilityAssessment", back_populates="credit_checks"
    )


# =============================================================================
# Risk Scoring Models
# =============================================================================


class RiskFactor(Base):
    """Risk factor definition for scoring model."""

    __tablename__ = "risk_factors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)

    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))  # credit, performance, external, fraud

    # Scoring configuration
    data_source: Mapped[str] = mapped_column(String(50))  # farmer, farm, credit, weather, market
    field_path: Mapped[str | None] = mapped_column(String(200))
    calculation_method: Mapped[str] = mapped_column(String(50))  # direct, formula, lookup, ml_model

    # Scoring ranges
    scoring_config: Mapped[dict | None] = mapped_column(JSONBCompatible)
    # Example: {"ranges": [{"min": 0, "max": 300, "score": 100}, {"min": 301, "max": 600, "score": 50}]}

    # Weight in overall score
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    max_score: Mapped[float] = mapped_column(Float, default=100.0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskAssessment(Base):
    """Risk assessment result for a farmer/assessment."""

    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE"), index=True
    )
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_assessments.id", ondelete="SET NULL")
    )

    # Assessment timestamp
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Overall scores
    total_risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20))  # RiskLevel
    confidence_score: Mapped[float | None] = mapped_column(Float)  # 0-100

    # Component scores
    credit_risk_score: Mapped[float | None] = mapped_column(Float)
    performance_risk_score: Mapped[float | None] = mapped_column(Float)
    external_risk_score: Mapped[float | None] = mapped_column(Float)
    fraud_risk_score: Mapped[float | None] = mapped_column(Float)

    # Factor breakdown
    factor_scores: Mapped[dict | None] = mapped_column(JSONBCompatible)
    # Example: {"credit_score": {"raw": 650, "normalized": 75, "weight": 0.3}, ...}

    # Flags
    fraud_indicators: Mapped[list | None] = mapped_column(JSONBCompatible)
    risk_flags: Mapped[list | None] = mapped_column(JSONBCompatible)

    # Recommendations
    recommendations: Mapped[list | None] = mapped_column(JSONBCompatible)

    # Model info
    model_version: Mapped[str | None] = mapped_column(String(50))
    model_type: Mapped[str] = mapped_column(
        String(50), default="rule_based"
    )  # rule_based, ml_model

    # Validity
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", backref="risk_assessments")
    assessment: Mapped["EligibilityAssessment | None"] = relationship(
        "EligibilityAssessment", back_populates="risk_assessments"
    )


# =============================================================================
# Workflow and Queue Models
# =============================================================================


class EligibilityReviewQueue(Base):
    """Queue for manual review of eligibility assessments."""

    __tablename__ = "eligibility_review_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_assessments.id", ondelete="CASCADE"), index=True
    )

    # Queue management
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1 = highest
    queue_reason: Mapped[str] = mapped_column(String(200))
    queue_category: Mapped[str | None] = mapped_column(
        String(50)
    )  # exception, fraud_review, escalation

    # Assignment
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, in_progress, completed
    decision: Mapped[str | None] = mapped_column(String(20))  # approved, rejected, escalated
    decision_notes: Mapped[str | None] = mapped_column(Text)

    # SLA tracking
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_overdue: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationship
    assessment: Mapped["EligibilityAssessment"] = relationship(
        "EligibilityAssessment", backref="review_queue"
    )


class SchemeWaitlist(Base):
    """Waitlist for oversubscribed schemes."""

    __tablename__ = "scheme_waitlists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_schemes.id", ondelete="CASCADE"), index=True
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE"), index=True
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_assessments.id", ondelete="CASCADE")
    )

    # Position
    position: Mapped[int] = mapped_column(Integer)
    original_position: Mapped[int] = mapped_column(Integer)  # Initial position when added

    # Scores for ranking
    eligibility_score: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float | None] = mapped_column(Float)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="waiting"
    )  # waiting, offered, accepted, declined, expired
    offered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    offer_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Timestamps
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    scheme: Mapped["EligibilityScheme"] = relationship(
        "EligibilityScheme", backref="waitlist_entries"
    )
    farmer: Mapped["Farmer"] = relationship("Farmer", backref="waitlist_entries")
    assessment: Mapped["EligibilityAssessment"] = relationship(
        "EligibilityAssessment", backref="waitlist_entry"
    )


class EligibilityNotification(Base):
    """Notifications related to eligibility status changes."""

    __tablename__ = "eligibility_notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE"), index=True
    )
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_assessments.id", ondelete="SET NULL")
    )

    # Notification details
    notification_type: Mapped[str] = mapped_column(
        String(50)
    )  # status_change, waitlist_update, reminder, offer
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    data: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Delivery
    channels: Mapped[list] = mapped_column(
        JSONBCompatible, default=list
    )  # sms, push, email, in_app
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", backref="eligibility_notifications")
