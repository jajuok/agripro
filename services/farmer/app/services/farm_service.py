"""Farm profile service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer, FarmProfile
from app.schemas.farm import FarmCreate, FarmResponse, FarmUpdate


class FarmService:
    """Service for farm operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_farm(self, data: FarmCreate) -> FarmResponse:
        """Create a new farm profile."""
        farm = FarmProfile(**data.model_dump())
        self.db.add(farm)
        await self.db.flush()
        return FarmResponse.model_validate(farm)

    async def get_farm(self, farm_id: UUID) -> FarmResponse | None:
        """Get farm by ID."""
        result = await self.db.execute(select(FarmProfile).where(FarmProfile.id == farm_id))
        farm = result.scalar_one_or_none()
        return FarmResponse.model_validate(farm) if farm else None

    async def update_farm(self, farm_id: UUID, data: FarmUpdate) -> FarmResponse | None:
        """Update farm profile."""
        result = await self.db.execute(select(FarmProfile).where(FarmProfile.id == farm_id))
        farm = result.scalar_one_or_none()
        if not farm:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(farm, field, value)

        return FarmResponse.model_validate(farm)

    async def list_farmer_farms(self, farmer_id: UUID) -> list[FarmResponse]:
        """List all farms for a farmer."""
        result = await self.db.execute(
            select(FarmProfile).where(FarmProfile.farmer_id == farmer_id)
        )
        farms = result.scalars().all()
        return [FarmResponse.model_validate(f) for f in farms]

    async def list_farms_by_user_id(self, user_id: UUID) -> list[FarmResponse]:
        """List all farms for a user (via farmer lookup)."""
        # First find the farmer by user_id
        farmer_result = await self.db.execute(
            select(Farmer).where(Farmer.user_id == user_id)
        )
        farmer = farmer_result.scalar_one_or_none()
        if not farmer:
            return []

        # Then get their farms
        result = await self.db.execute(
            select(FarmProfile).where(FarmProfile.farmer_id == farmer.id)
        )
        farms = result.scalars().all()
        return [FarmResponse.model_validate(f) for f in farms]
