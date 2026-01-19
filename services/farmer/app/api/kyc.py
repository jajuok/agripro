"""KYC verification API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.kyc import KYCReviewRequest, KYCStatusResponse
from app.services.kyc_service import KYCService

router = APIRouter()


@router.get("/{farmer_id}/status", response_model=KYCStatusResponse)
async def get_kyc_status(
    farmer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> KYCStatusResponse:
    """Get KYC verification status for a farmer."""
    service = KYCService(db)
    status_response = await service.get_kyc_status(farmer_id)
    if not status_response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return status_response


@router.post("/{farmer_id}/submit", response_model=KYCStatusResponse)
async def submit_for_kyc_review(
    farmer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> KYCStatusResponse:
    """Submit farmer profile for KYC review."""
    service = KYCService(db)
    return await service.submit_for_review(farmer_id)


@router.post("/{farmer_id}/review", response_model=KYCStatusResponse)
async def review_kyc(
    farmer_id: UUID,
    review: KYCReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> KYCStatusResponse:
    """Review and approve/reject KYC (admin only)."""
    service = KYCService(db)
    return await service.review_kyc(farmer_id, review)


@router.post("/{farmer_id}/verify-biometric")
async def verify_biometric(
    farmer_id: UUID,
    biometric_type: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Verify farmer biometric data."""
    service = KYCService(db)
    result = await service.verify_biometric(farmer_id, biometric_type)
    return {"verified": result}
