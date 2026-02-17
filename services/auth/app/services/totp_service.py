"""Two-Factor Authentication service using TOTP."""

import base64
from io import BytesIO
from uuid import UUID

import pyotp
import qrcode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TOTPService:
    """Service for TOTP-based two-factor authentication."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def setup_totp(self, user_id: UUID) -> dict:
        """Generate TOTP secret and QR code for setup."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        if user.totp_enabled:
            raise ValueError("2FA is already enabled")

        # Generate new secret
        secret = pyotp.random_base32()
        user.totp_secret = secret

        # Create provisioning URI for authenticator apps
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="AgriScheme Pro")

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_base64}",
            "provisioning_uri": provisioning_uri,
        }

    async def verify_and_enable_totp(self, user_id: UUID, code: str) -> bool:
        """Verify TOTP code and enable 2FA if valid."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        if not user.totp_secret:
            raise ValueError("TOTP not set up. Call setup first.")

        if user.totp_enabled:
            raise ValueError("2FA is already enabled")

        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code):
            user.totp_enabled = True
            return True
        return False

    async def verify_totp(self, user_id: UUID, code: str) -> bool:
        """Verify TOTP code for login."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        if not user.totp_enabled or not user.totp_secret:
            return False

        totp = pyotp.TOTP(user.totp_secret)
        return totp.verify(code)

    async def disable_totp(self, user_id: UUID, code: str) -> bool:
        """Disable 2FA after verifying current code."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        if not user.totp_enabled:
            raise ValueError("2FA is not enabled")

        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code):
            user.totp_enabled = False
            user.totp_secret = None
            return True
        return False

    async def is_totp_enabled(self, user_id: UUID) -> bool:
        """Check if TOTP is enabled for user."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user.totp_enabled if user else False
