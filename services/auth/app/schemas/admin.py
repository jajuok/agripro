"""Admin schemas for user and role management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# Role schemas
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


# Permission schemas
class PermissionCreate(BaseModel):
    """Create permission request."""

    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)
    description: str | None = None


class PermissionResponse(BaseModel):
    """Permission response."""

    id: UUID
    code: str
    name: str
    description: str | None
    resource: str
    action: str

    model_config = {"from_attributes": True}


class RoleWithPermissions(RoleResponse):
    """Role with its assigned permissions."""

    permissions: list[PermissionResponse]


# Assignment schemas
class RolePermissionAssign(BaseModel):
    """Assign permission to role."""

    permission_id: UUID


class UserRoleAssign(BaseModel):
    """Assign role to user."""

    role_id: UUID


# User management schemas
class UserResponse(BaseModel):
    """User response for admin."""

    id: UUID
    email: str
    first_name: str
    last_name: str
    phone_number: str | None
    is_active: bool
    is_superuser: bool
    totp_enabled: bool
    created_at: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Update user request."""

    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserListResponse(BaseModel):
    """Paginated user list response."""

    items: list[UserResponse]
    total: int
    page: int
    size: int
    pages: int
