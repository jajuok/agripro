"""Farmer management API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.farmer import FarmerCreate, FarmerListResponse, FarmerResponse, FarmerUpdate
from app.services.farmer_service import FarmerService

router = APIRouter()


@router.post("", response_model=FarmerResponse, status_code=status.HTTP_201_CREATED)
async def create_farmer(
    data: FarmerCreate,
    db: AsyncSession = Depends(get_db),
) -> FarmerResponse:
    """Register a new farmer."""
    service = FarmerService(db)
    return await service.create_farmer(data)


@router.get("", response_model=FarmerListResponse)
async def list_farmers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    kyc_status: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> FarmerListResponse:
    """List all farmers with pagination."""
    service = FarmerService(db)
    return await service.list_farmers(page=page, page_size=page_size, kyc_status=kyc_status)


@router.get("/by-user/{user_id}", response_model=FarmerResponse)
async def get_farmer_by_user_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FarmerResponse:
    """Get farmer by auth user ID."""
    service = FarmerService(db)
    farmer = await service.get_farmer_by_user_id(user_id)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return farmer


@router.get("/{farmer_id}", response_model=FarmerResponse)
async def get_farmer(
    farmer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FarmerResponse:
    """Get farmer by ID."""
    service = FarmerService(db)
    farmer = await service.get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return farmer


@router.patch("/{farmer_id}", response_model=FarmerResponse)
async def update_farmer(
    farmer_id: UUID,
    data: FarmerUpdate,
    db: AsyncSession = Depends(get_db),
) -> FarmerResponse:
    """Update farmer profile."""
    service = FarmerService(db)
    farmer = await service.update_farmer(farmer_id, data)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return farmer
