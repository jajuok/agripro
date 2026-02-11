"""Authentication service."""

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import RefreshToken, User, UserRole
from app.schemas.auth import LoginResponse, PhoneRegisterRequest, RegisterRequest, TokenResponse


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, data: RegisterRequest) -> LoginResponse:
        """Register a new user."""
        # Check if user exists
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

        if data.phone_number:
            result = await self.db.execute(
                select(User).where(User.phone_number == data.phone_number)
            )
            if result.scalar_one_or_none():
                raise ValueError("Phone number already registered")

        # Create user
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
            national_id=data.national_id,
        )
        self.db.add(user)
        await self.db.flush()

        # Generate tokens
        return await self._create_tokens_response(user)

    async def register_phone(self, data: PhoneRegisterRequest) -> LoginResponse:
        """Register a new user with phone number and PIN."""
        # Check if phone already exists
        result = await self.db.execute(
            select(User).where(User.phone_number == data.phone_number)
        )
        if result.scalar_one_or_none():
            raise ValueError("Phone number already registered")

        # Create user with phone as primary identifier, no email
        user = User(
            email=None,
            phone_number=data.phone_number,
            hashed_password=hash_password(data.pin),
            first_name=data.first_name,
            last_name=data.last_name,
            auth_method="phone_pin",
        )
        self.db.add(user)
        await self.db.flush()

        return await self._create_tokens_response(user)

    async def login(
        self, email: str, password: str, totp_code: str | None = None
    ) -> LoginResponse | dict | None:
        """Authenticate user and return tokens.

        Returns:
            LoginResponse: On successful authentication
            dict with {"requires_2fa": True}: When 2FA is required but code not provided
            None: On invalid credentials
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        # Check if 2FA is required
        if user.totp_enabled:
            if not totp_code:
                # 2FA is enabled but no code provided
                return {"requires_2fa": True}

            # Verify TOTP code
            from app.services.totp_service import TOTPService
            totp_service = TOTPService(self.db)
            if not await totp_service.verify_totp(user.id, totp_code):
                return None  # Invalid TOTP code

        # Update last login
        user.last_login = datetime.now(timezone.utc)

        # Extract role names from loaded relationships
        roles = [ur.role.name for ur in user.roles] if user.roles else []

        return await self._create_tokens_response(user, roles)

    async def login_phone(
        self, phone_number: str, pin: str
    ) -> LoginResponse | None:
        """Authenticate user with phone number and PIN."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.phone_number == phone_number)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(pin, user.hashed_password):
            return None

        if not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.now(timezone.utc)

        roles = [ur.role.name for ur in user.roles] if user.roles else []
        return await self._create_tokens_response(user, roles)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse | None:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        result = await self.db.execute(
            select(RefreshToken)
            .options(selectinload(RefreshToken.user))
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        stored_token = result.scalar_one_or_none()

        if not stored_token or not stored_token.user.is_active:
            return None

        # Revoke old refresh token
        stored_token.revoked_at = datetime.now(timezone.utc)

        # Generate new tokens
        user = stored_token.user
        token_data = {"sub": str(user.id)}
        if user.email:
            token_data["email"] = user.email
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"sub": str(user.id)})

        # Store new refresh token
        await self._store_refresh_token(user.id, new_refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def logout(self, refresh_token: str) -> None:
        """Revoke refresh token."""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored_token = result.scalar_one_or_none()
        if stored_token:
            stored_token.revoked_at = datetime.now(timezone.utc)

    async def _create_tokens_response(self, user: User, roles: list[str] | None = None) -> LoginResponse:
        """Create token response for user."""
        token_data = {"sub": str(user.id)}
        if user.email:
            token_data["email"] = user.email

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user.id)})

        await self._store_refresh_token(user.id, refresh_token)

        # Use provided roles or empty list for new users
        user_roles = roles if roles is not None else []

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user_id=str(user.id),
            email=user.email,
            phone_number=user.phone_number,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=user_roles,
        )

    async def _store_refresh_token(self, user_id, token: str) -> None:
        """Store refresh token hash in database."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(refresh_token)
