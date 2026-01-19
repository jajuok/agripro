"""Farmer management service."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer
from app.schemas.farmer import FarmerCreate, FarmerListResponse, FarmerResponse, FarmerUpdate


class FarmerService:
    """Service for farmer operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_farmer(self, data: FarmerCreate) -> FarmerResponse:
        """Create a new farmer."""
        farmer = Farmer(**data.model_dump())
        self.db.add(farmer)
        await self.db.flush()
        return FarmerResponse.model_validate(farmer)

    async def get_farmer(self, farmer_id: UUID) -> FarmerResponse | None:
        """Get farmer by ID."""
        result = await self.db.execute(select(Farmer).where(Farmer.id == farmer_id))
        farmer = result.scalar_one_or_none()
        return FarmerResponse.model_validate(farmer) if farmer else None

    async def update_farmer(self, farmer_id: UUID, data: FarmerUpdate) -> FarmerResponse | None:
        """Update farmer profile."""
        result = await self.db.execute(select(Farmer).where(Farmer.id == farmer_id))
        farmer = result.scalar_one_or_none()
        if not farmer:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(farmer, field, value)

        return FarmerResponse.model_validate(farmer)

    async def list_farmers(
        self, page: int = 1, page_size: int = 20, kyc_status: str | None = None
    ) -> FarmerListResponse:
        """List farmers with pagination."""
        query = select(Farmer)
        count_query = select(func.count()).select_from(Farmer)

        if kyc_status:
            query = query.where(Farmer.kyc_status == kyc_status)
            count_query = count_query.where(Farmer.kyc_status == kyc_status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        farmers = result.scalars().all()

        return FarmerListResponse(
            items=[FarmerResponse.model_validate(f) for f in farmers],
            total=total,
            page=page,
            page_size=page_size,
        )
