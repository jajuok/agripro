"""API routes."""

from fastapi import APIRouter

from app.api import farmers, farms, documents, kyc, farm_registration

router = APIRouter()

router.include_router(farmers.router, prefix="/farmers", tags=["Farmers"])
router.include_router(farms.router, prefix="/farms", tags=["Farm Profiles"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(kyc.router, prefix="/kyc", tags=["KYC Verification"])
router.include_router(farm_registration.router, prefix="/farm-registration", tags=["Farm Registration"])
