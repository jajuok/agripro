"""Farm profile API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.farm import FarmCreate, FarmResponse, FarmUpdate
from app.services.farm_service import FarmService

router = APIRouter()


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    data: FarmCreate,
    db: AsyncSession = Depends(get_db),
) -> FarmResponse:
    """Register a new farm/plot."""
    service = FarmService(db)
    return await service.create_farm(data)


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FarmResponse:
    """Get farm by ID."""
    service = FarmService(db)
    farm = await service.get_farm(farm_id)
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm


@router.patch("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: UUID,
    data: FarmUpdate,
    db: AsyncSession = Depends(get_db),
) -> FarmResponse:
    """Update farm profile."""
    service = FarmService(db)
    farm = await service.update_farm(farm_id, data)
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm


@router.get("/farmer/{farmer_id}", response_model=list[FarmResponse])
async def list_farmer_farms(
    farmer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FarmResponse]:
    """List all farms for a farmer."""
    service = FarmService(db)
    return await service.list_farmer_farms(farmer_id)
