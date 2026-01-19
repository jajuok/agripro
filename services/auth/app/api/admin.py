"""Admin API endpoints for user, role, and permission management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin import (
    PermissionCreate,
    PermissionResponse,
    RoleCreate,
    RolePermissionAssign,
    RoleResponse,
    RoleWithPermissions,
    UserListResponse,
    UserResponse,
    UserRoleAssign,
    UserUpdate,
)
from app.services.audit_service import AuditAction, AuditService, ResourceType
from app.services.rbac_service import RBACService


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


router = APIRouter()


# Role Management Endpoints
@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> RoleResponse:
    """Create a new role."""
    rbac = RBACService(db)
    audit = AuditService(db)

    # Check if role name already exists
    existing = await rbac.get_role_by_name(role_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists",
        )

    role = await rbac.create_role(
        name=role_data.name,
        description=role_data.description,
        tenant_id=role_data.tenant_id,
    )
    await db.commit()

    await audit.log(
        action=AuditAction.ROLE_CREATE,
        resource_type=ResourceType.ROLE,
        resource_id=str(role.id),
        user_id=current_user.id,
        details={"name": role.name},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()

    return RoleResponse.model_validate(role)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    tenant_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> list[RoleResponse]:
    """List all roles."""
    rbac = RBACService(db)
    roles = await rbac.list_roles(tenant_id)
    return [RoleResponse.model_validate(r) for r in roles]


@router.get("/roles/{role_id}", response_model=RoleWithPermissions)
async def get_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> RoleWithPermissions:
    """Get role with its permissions."""
    rbac = RBACService(db)
    role = await rbac.get_role(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    permissions = await rbac.get_role_permissions(role_id)
    return RoleWithPermissions(
        id=role.id,
        name=role.name,
        description=role.description,
        tenant_id=role.tenant_id,
        is_system_role=role.is_system_role,
        created_at=role.created_at,
        permissions=[PermissionResponse.model_validate(p) for p in permissions],
    )


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> None:
    """Delete a role."""
    rbac = RBACService(db)
    audit = AuditService(db)

    role = await rbac.get_role(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    try:
        await rbac.delete_role(role_id)
        await db.commit()

        await audit.log(
            action=AuditAction.ROLE_DELETE,
            resource_type=ResourceType.ROLE,
            resource_id=str(role_id),
            user_id=current_user.id,
            details={"name": role.name},
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Permission Management Endpoints
@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    perm_data: PermissionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> PermissionResponse:
    """Create a new permission."""
    rbac = RBACService(db)
    audit = AuditService(db)

    # Check if permission code already exists
    existing = await rbac.get_permission_by_code(perm_data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission with this code already exists",
        )

    permission = await rbac.create_permission(
        code=perm_data.code,
        name=perm_data.name,
        resource=perm_data.resource,
        action=perm_data.action,
        description=perm_data.description,
    )
    await db.commit()

    await audit.log(
        action=AuditAction.PERMISSION_CREATE,
        resource_type=ResourceType.PERMISSION,
        resource_id=str(permission.id),
        user_id=current_user.id,
        details={"code": permission.code},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()

    return PermissionResponse.model_validate(permission)


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> list[PermissionResponse]:
    """List all permissions."""
    rbac = RBACService(db)
    permissions = await rbac.list_permissions()
    return [PermissionResponse.model_validate(p) for p in permissions]


# Role-Permission Assignment
@router.post("/roles/{role_id}/permissions", status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(
    role_id: UUID,
    data: RolePermissionAssign,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """Assign a permission to a role."""
    rbac = RBACService(db)
    audit = AuditService(db)

    role = await rbac.get_role(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    await rbac.assign_permission_to_role(role_id, data.permission_id)
    await db.commit()

    await audit.log(
        action=AuditAction.PERMISSION_ASSIGN,
        resource_type=ResourceType.ROLE,
        resource_id=str(role_id),
        user_id=current_user.id,
        details={"permission_id": str(data.permission_id)},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()

    return {"message": "Permission assigned to role"}


@router.delete("/roles/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> None:
    """Revoke a permission from a role."""
    rbac = RBACService(db)
    audit = AuditService(db)

    if not await rbac.revoke_permission_from_role(role_id, permission_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role-permission assignment not found",
        )
    await db.commit()

    await audit.log(
        action=AuditAction.PERMISSION_REVOKE,
        resource_type=ResourceType.ROLE,
        resource_id=str(role_id),
        user_id=current_user.id,
        details={"permission_id": str(permission_id)},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()


# User-Role Assignment
@router.post("/users/{user_id}/roles", status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: UUID,
    data: UserRoleAssign,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """Assign a role to a user."""
    rbac = RBACService(db)
    audit = AuditService(db)

    await rbac.assign_role_to_user(user_id, data.role_id, assigned_by=current_user.id)
    await db.commit()

    await audit.log(
        action=AuditAction.ROLE_ASSIGN,
        resource_type=ResourceType.USER,
        resource_id=str(user_id),
        user_id=current_user.id,
        details={"role_id": str(data.role_id)},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()

    return {"message": "Role assigned to user"}


@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_role_from_user(
    user_id: UUID,
    role_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> None:
    """Revoke a role from a user."""
    rbac = RBACService(db)
    audit = AuditService(db)

    if not await rbac.revoke_role_from_user(user_id, role_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User-role assignment not found",
        )
    await db.commit()

    await audit.log(
        action=AuditAction.ROLE_REVOKE,
        resource_type=ResourceType.USER,
        resource_id=str(user_id),
        user_id=current_user.id,
        details={"role_id": str(role_id)},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()


@router.get("/users/{user_id}/roles", response_model=list[RoleResponse])
async def get_user_roles(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> list[RoleResponse]:
    """Get all roles for a user."""
    rbac = RBACService(db)
    roles = await rbac.get_user_roles(user_id)
    return [RoleResponse.model_validate(r) for r in roles]


@router.get("/users/{user_id}/permissions", response_model=list[str])
async def get_user_permissions(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> list[str]:
    """Get all permission codes for a user."""
    rbac = RBACService(db)
    return await rbac.get_user_permissions(user_id)
