"""KYC schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KYCStatusResponse(BaseModel):
    """KYC status response."""
    farmer_id: UUID
    status: str
    verified_at: datetime | None
    documents_submitted: int
    documents_verified: int
    biometrics_captured: bool
    missing_requirements: list[str]


class KYCReviewRequest(BaseModel):
    """KYC review request."""
    action: str  # approve, reject
    reviewer_id: UUID
    notes: str | None = None
    rejection_reason: str | None = None
