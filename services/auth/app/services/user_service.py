"""User management service."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.schemas.user import UserListResponse, UserResponse, UserUpdate


class UserService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        """Update user profile."""
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        return user

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        tenant_id: UUID | None = None,
    ) -> UserListResponse:
        """List users with pagination."""
        query = select(User).options(selectinload(User.roles))

        if tenant_id:
            query = query.where(User.tenant_id == tenant_id)

        # Count total
        count_query = select(func.count()).select_from(User)
        if tenant_id:
            count_query = count_query.where(User.tenant_id == tenant_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get page
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        users = result.scalars().all()

        items = [
            UserResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                phone_number=user.phone_number,
                national_id=user.national_id,
                is_active=user.is_active,
                is_verified=user.is_verified,
                roles=[ur.role.name for ur in user.roles],
                created_at=user.created_at,
                last_login=user.last_login,
            )
            for user in users
        ]

        return UserListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    async def deactivate_user(self, user_id: UUID) -> User:
        """Deactivate user account."""
        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        user.is_active = False
        return user
