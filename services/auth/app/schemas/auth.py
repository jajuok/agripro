"""Authentication schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    totp_code: str | None = Field(None, min_length=6, max_length=6)


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(TokenResponse):
    """Login response with user info."""

    user_id: str
    email: str | None = None
    phone_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    roles: list[str]
    totp_required: bool = False


class TwoFactorRequiredResponse(BaseModel):
    """Response when 2FA is required."""

    requires_2fa: bool = True
    message: str = "Two-factor authentication required"


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: str | None = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    national_id: str | None = None


class PhoneRegisterRequest(BaseModel):
    """Phone+PIN registration for mobile farmers."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    pin: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


class PhoneLoginRequest(BaseModel):
    """Phone+PIN login for mobile farmers."""

    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    pin: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


# Two-Factor Authentication schemas
class TOTPSetupResponse(BaseModel):
    """TOTP setup response with QR code."""

    secret: str
    qr_code: str
    provisioning_uri: str


class TOTPVerifyRequest(BaseModel):
    """TOTP verification request."""

    code: str = Field(..., min_length=6, max_length=6)


class TOTPStatusResponse(BaseModel):
    """TOTP status response."""

    enabled: bool


# Password reset schemas
class PasswordResetRequest(BaseModel):
    """Request password reset."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""

    token: str
    new_password: str = Field(..., min_length=8)


class PasswordChangeRequest(BaseModel):
    """Change password for authenticated user."""

    current_password: str
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


# Role and Permission schemas
class RoleCreate(BaseModel):
    """Create role request."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    tenant_id: UUID | None = None


class RoleResponse(BaseModel):
    """Role response."""

    id: UUID
    name: str
    description: str | None
    tenant_id: UUID | None
    is_system_role: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    """Permission response."""

    id: UUID
    code: str
    name: str
    description: str | None
    resource: str
    action: str

    model_config = {"from_attributes": True}


class RoleAssignRequest(BaseModel):
    """Assign role to user request."""

    role_id: UUID


class UserRoleResponse(BaseModel):
    """User role assignment response."""

    user_id: UUID
    role_id: UUID
    role_name: str
    assigned_at: datetime


# Audit log schemas
class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: UUID
    user_id: UUID | None
    tenant_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
