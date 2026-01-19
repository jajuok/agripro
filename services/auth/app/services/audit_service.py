"""Audit logging service for compliance."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuditLog


class AuditService:
    """Service for immutable audit logging."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Create an immutable audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(audit_log)
        await self.db.flush()
        return audit_log


# Common audit actions
class AuditAction:
    """Standard audit action constants."""

    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    REGISTER = "auth.register"
    PASSWORD_RESET_REQUEST = "auth.password_reset.request"
    PASSWORD_RESET_COMPLETE = "auth.password_reset.complete"
    PASSWORD_CHANGE = "auth.password.change"
    TOTP_ENABLED = "auth.totp.enabled"
    TOTP_DISABLED = "auth.totp.disabled"

    # User management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ACTIVATE = "user.activate"
    USER_DEACTIVATE = "user.deactivate"

    # Role management
    ROLE_CREATE = "role.create"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"
    ROLE_ASSIGN = "role.assign"
    ROLE_REVOKE = "role.revoke"

    # Permission management
    PERMISSION_CREATE = "permission.create"
    PERMISSION_GRANT = "permission.grant"
    PERMISSION_ASSIGN = "permission.assign"
    PERMISSION_REVOKE = "permission.revoke"

    # Tenant management
    TENANT_CREATE = "tenant.create"
    TENANT_UPDATE = "tenant.update"


# Resource types
class ResourceType:
    """Standard resource type constants."""

    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    TENANT = "tenant"
    SESSION = "session"
