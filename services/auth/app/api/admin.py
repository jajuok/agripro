"""Admin API endpoints for user, role, and permission management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminUserCreate,
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
from app.services.user_service import UserService


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


router = APIRouter()


# User Management Endpoints
@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> UserListResponse:
    """List all users with pagination and optional filters."""
    from sqlalchemy import select as sa_select
    from sqlalchemy.orm import selectinload as si_load

    from app.models.user import User as UserModel

    query = sa_select(UserModel).options(si_load(UserModel.roles))

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            UserModel.first_name.ilike(search_filter)
            | UserModel.last_name.ilike(search_filter)
            | UserModel.email.ilike(search_filter)
        )

    if is_active is not None:
        query = query.where(UserModel.is_active == is_active)

    from sqlalchemy import func

    count_q = sa_select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(UserModel.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    rows = (await db.execute(query)).scalars().all()

    items = [
        UserResponse(
            id=u.id,
            email=u.email or "",
            first_name=u.first_name,
            last_name=u.last_name,
            phone_number=u.phone_number,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            totp_enabled=u.totp_enabled,
            created_at=u.created_at,
            last_login=u.last_login,
        )
        for u in rows
    ]

    return UserListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if total else 1,
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: AdminUserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> UserResponse:
    """Create a new user account."""
    user_svc = UserService(db)
    audit = AuditService(db)

    try:
        user = await user_svc.create_user(
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
            is_superuser=data.is_superuser,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await audit.log(
        action=AuditAction.USER_CREATE,
        resource_type=ResourceType.USER,
        resource_id=str(user.id),
        user_id=current_user.id,
        details={"email": user.email},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()

    return UserResponse(
        id=user.id,
        email=user.email or "",
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        totp_enabled=user.totp_enabled,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> UserResponse:
    """Update a user account."""
    user_svc = UserService(db)
    audit = AuditService(db)

    try:
        from app.schemas.user import UserUpdate as BaseUserUpdate

        base_update = BaseUserUpdate(**data.model_dump(exclude_unset=True))
        user = await user_svc.update_user(user_id, base_update)

        # Handle is_superuser separately (not in base UserUpdate)
        if data.is_superuser is not None:
            user.is_superuser = data.is_superuser

        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    await audit.log(
        action=AuditAction.USER_UPDATE,
        resource_type=ResourceType.USER,
        resource_id=str(user_id),
        user_id=current_user.id,
        details=data.model_dump(exclude_unset=True),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()

    return UserResponse(
        id=user.id,
        email=user.email or "",
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        totp_enabled=user.totp_enabled,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.post("/users/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> UserResponse:
    """Toggle user active status."""
    user_svc = UserService(db)
    audit = AuditService(db)

    try:
        existing = await user_svc.get_user(user_id)
        if not existing:
            raise ValueError("User not found")

        if existing.is_active:
            user = await user_svc.deactivate_user(user_id)
            action = AuditAction.USER_DEACTIVATE
        else:
            user = await user_svc.activate_user(user_id)
            action = AuditAction.USER_ACTIVATE

        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    await audit.log(
        action=action,
        resource_type=ResourceType.USER,
        resource_id=str(user_id),
        user_id=current_user.id,
        details={"is_active": user.is_active},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()

    return UserResponse(
        id=user.id,
        email=user.email or "",
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        totp_enabled=user.totp_enabled,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> None:
    """Permanently delete a user account."""
    user_svc = UserService(db)
    audit = AuditService(db)

    try:
        user = await user_svc.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        email = user.email
        await user_svc.delete_user(user_id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    await audit.log(
        action=AuditAction.USER_DELETE,
        resource_type=ResourceType.USER,
        resource_id=str(user_id),
        user_id=current_user.id,
        details={"email": email},
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()


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


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT
)
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
