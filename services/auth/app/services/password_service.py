"""Password reset and management service."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import PasswordResetToken, User


class PasswordService:
    """Service for password management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_reset_token(self, email: str) -> str | None:
        """Create a password reset token for a user."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return None

        # Generate secure token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Create reset token (valid for 1 hour)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        self.db.add(reset_token)

        return token

    async def validate_reset_token(self, token: str) -> User | None:
        """Validate a password reset token and return the user."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.expires_at > datetime.now(UTC),
                PasswordResetToken.used_at.is_(None),
            )
        )
        reset_token = result.scalar_one_or_none()
        if not reset_token:
            return None

        # Get user
        user_result = await self.db.execute(select(User).where(User.id == reset_token.user_id))
        return user_result.scalar_one_or_none()

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using a valid reset token."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.expires_at > datetime.now(UTC),
                PasswordResetToken.used_at.is_(None),
            )
        )
        reset_token = result.scalar_one_or_none()
        if not reset_token:
            return False

        # Get user and update password
        user_result = await self.db.execute(select(User).where(User.id == reset_token.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return False

        user.hashed_password = hash_password(new_password)
        reset_token.used_at = datetime.now(UTC)

        return True

    async def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        """Change password for authenticated user."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        if not verify_password(current_password, user.hashed_password):
            return False

        user.hashed_password = hash_password(new_password)
        return True
