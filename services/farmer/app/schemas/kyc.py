"""KYC schemas."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class KYCStep(str, Enum):
    """KYC workflow steps."""

    PERSONAL_INFO = "personal_info"
    DOCUMENTS = "documents"
    BIOMETRICS = "biometrics"
    BANK_INFO = "bank_info"
    EXTERNAL_VERIFICATION = "external_verification"
    REVIEW = "review"
    COMPLETE = "complete"


class DocumentType(str, Enum):
    """Document types for KYC."""

    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    LAND_TITLE = "land_title"
    LEASE_AGREEMENT = "lease_agreement"
    TAX_ID = "tax_id"
    BANK_STATEMENT = "bank_statement"
    SOIL_TEST = "soil_test"
    OTHER = "other"


class BiometricType(str, Enum):
    """Types of biometric data."""

    FINGERPRINT_RIGHT_THUMB = "fingerprint_right_thumb"
    FINGERPRINT_RIGHT_INDEX = "fingerprint_right_index"
    FINGERPRINT_LEFT_THUMB = "fingerprint_left_thumb"
    FINGERPRINT_LEFT_INDEX = "fingerprint_left_index"
    FACE = "face"


# Request Schemas
class StartKYCRequest(BaseModel):
    """Request to start KYC application."""

    required_documents: list[str] | None = None
    required_biometrics: list[str] | None = None


class CompleteStepRequest(BaseModel):
    """Request to complete a KYC step."""

    step: KYCStep
    data: dict[str, Any] | None = None


class DocumentUploadRequest(BaseModel):
    """Request metadata for document upload."""

    document_type: DocumentType
    document_number: str | None = None
    expiry_date: datetime | None = None


class BiometricCaptureRequest(BaseModel):
    """Request for biometric capture."""

    biometric_type: BiometricType
    capture_device: str | None = None
    capture_location: dict[str, float] | None = None  # {lat, lng}


class KYCReviewRequest(BaseModel):
    """KYC review request."""

    action: str = Field(..., pattern="^(approve|reject)$")
    reviewer_id: UUID
    notes: str | None = None
    rejection_reason: str | None = None


class AssignReviewRequest(BaseModel):
    """Assign review to a reviewer."""

    reviewer_id: UUID


# Response Schemas
class StepStatus(BaseModel):
    """Status of a single KYC step."""

    complete: bool
    required: bool = True
    details: dict[str, Any] | None = None


class DocumentSubmission(BaseModel):
    """Document submission status."""

    document_type: str
    document_id: UUID | None = None
    is_submitted: bool
    is_verified: bool
    verified_at: datetime | None = None


class BiometricCapture(BaseModel):
    """Biometric capture status."""

    biometric_type: str
    is_captured: bool
    is_verified: bool
    quality_score: float | None = None


class ExternalVerificationStatus(BaseModel):
    """External verification status."""

    verification_type: str
    provider: str
    status: str
    is_verified: bool
    completed_at: datetime | None = None


class KYCStatusResponse(BaseModel):
    """Comprehensive KYC status response."""

    farmer_id: UUID
    current_step: str
    overall_status: str
    progress_percentage: int

    # Step completion
    personal_info_complete: bool
    documents_complete: bool
    biometrics_complete: bool
    bank_info_complete: bool

    # Document status
    required_documents: list[str]
    documents_submitted: list[DocumentSubmission]
    missing_documents: list[str]

    # Biometric status
    required_biometrics: list[str]
    biometrics_captured: list[BiometricCapture]
    missing_biometrics: list[str]

    # External verifications
    external_verifications: list[ExternalVerificationStatus]

    # Review status
    in_review_queue: bool
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KYCApplicationResponse(BaseModel):
    """KYC application response."""

    id: UUID
    farmer_id: UUID
    current_step: str
    submitted_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewQueueItem(BaseModel):
    """Item in the review queue."""

    queue_id: UUID
    farmer_id: UUID
    farmer_name: str
    priority: int
    reason: str
    queued_at: datetime
    assigned_to: UUID | None = None
    status: str


class ReviewQueueResponse(BaseModel):
    """Review queue response."""

    items: list[ReviewQueueItem]
    total: int
    pending_count: int
    in_progress_count: int


class DocumentVerificationResult(BaseModel):
    """Result of document verification."""

    document_id: UUID
    document_type: str
    is_verified: bool
    extracted_data: dict[str, Any] | None = None
    confidence_score: float | None = None
    verification_notes: str | None = None


class BiometricCaptureResult(BaseModel):
    """Result of biometric capture."""

    success: bool
    biometric_id: UUID | None = None
    biometric_type: str
    quality_score: float
    is_duplicate: bool = False
    duplicate_farmer_id: UUID | None = None
    errors: list[str] = []


class BiometricVerifyResult(BaseModel):
    """Result of biometric verification."""

    match: bool
    confidence: float
    farmer_id: UUID | None = None


class ExternalVerificationResult(BaseModel):
    """Result of external verification."""

    success: bool
    verification_type: str
    is_verified: bool
    match_score: float | None = None
    data: dict[str, Any] = {}
    error: str | None = None
