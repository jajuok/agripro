"""API routes."""

from fastapi import APIRouter

from app.api import crop_planning, documents, eligibility, farm_registration, farmers, farms, kyc

router = APIRouter()

router.include_router(farmers.router, prefix="/farmers", tags=["Farmers"])
router.include_router(farms.router, prefix="/farms", tags=["Farm Profiles"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(kyc.router, prefix="/kyc", tags=["KYC Verification"])
router.include_router(
    farm_registration.router, prefix="/farm-registration", tags=["Farm Registration"]
)
router.include_router(eligibility.router, tags=["Eligibility Assessment"])
router.include_router(crop_planning.router, prefix="/crop-planning", tags=["Crop Planning"])
