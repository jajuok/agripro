"""Login attempt tracking service for security."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import LoginAttempt


class LoginTracker:
    """Service for tracking and rate-limiting login attempts."""

    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 5

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_attempt(
        self,
        email: str,
        ip_address: str,
        success: bool,
        user_agent: str | None = None,
        failure_reason: str | None = None,
    ) -> LoginAttempt:
        """Record a login attempt."""
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            success=success,
            user_agent=user_agent,
            failure_reason=failure_reason,
        )
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def is_locked_out(self, email: str, ip_address: str) -> bool:
        """Check if an account or IP is locked out due to too many failed attempts."""
        cutoff = datetime.now(UTC) - timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)

        # Check failed attempts for this email
        email_result = await self.db.execute(
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.email == email,
                LoginAttempt.success == False,  # noqa: E712
                LoginAttempt.attempted_at > cutoff,
            )
        )
        email_failures = email_result.scalar() or 0

        if email_failures >= self.MAX_ATTEMPTS:
            return True

        # Check failed attempts for this IP
        ip_result = await self.db.execute(
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.ip_address == ip_address,
                LoginAttempt.success == False,  # noqa: E712
                LoginAttempt.attempted_at > cutoff,
            )
        )
        ip_failures = ip_result.scalar() or 0

        # Allow more attempts from same IP since multiple users might share it
        return ip_failures >= self.MAX_ATTEMPTS * 3

    async def get_failed_attempts_count(self, email: str, since_minutes: int = 5) -> int:
        """Get count of failed login attempts for an email."""
        cutoff = datetime.now(UTC) - timedelta(minutes=since_minutes)

        result = await self.db.execute(
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.email == email,
                LoginAttempt.success == False,  # noqa: E712
                LoginAttempt.attempted_at > cutoff,
            )
        )
        return result.scalar() or 0

    async def clear_failed_attempts(self, email: str) -> None:
        """Clear failed attempt count after successful login.

        Note: We don't actually delete records for audit purposes,
        but the lockout check only looks at recent attempts.
        """
        pass  # Records are kept for audit trail
