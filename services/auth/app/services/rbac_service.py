"""Role-Based Access Control service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Permission, Role, RolePermission, User, UserRole


class RBACService:
    """Service for role and permission management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # Role operations
    async def create_role(
        self,
        name: str,
        description: str | None = None,
        tenant_id: UUID | None = None,
        is_system_role: bool = False,
    ) -> Role:
        """Create a new role."""
        role = Role(
            name=name,
            description=description,
            tenant_id=tenant_id,
            is_system_role=is_system_role,
        )
        self.db.add(role)
        await self.db.flush()
        return role

    async def get_role(self, role_id: UUID) -> Role | None:
        """Get role by ID."""
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_role_by_name(self, name: str) -> Role | None:
        """Get role by name."""
        result = await self.db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def list_roles(self, tenant_id: UUID | None = None) -> list[Role]:
        """List all roles, optionally filtered by tenant."""
        query = select(Role)
        if tenant_id:
            query = query.where(
                (Role.tenant_id == tenant_id) | (Role.is_system_role == True)  # noqa: E712
            )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_role(self, role_id: UUID) -> bool:
        """Delete a role."""
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            return False
        if role.is_system_role:
            raise ValueError("Cannot delete system role")
        await self.db.delete(role)
        return True

    # Permission operations
    async def create_permission(
        self,
        code: str,
        name: str,
        resource: str,
        action: str,
        description: str | None = None,
    ) -> Permission:
        """Create a new permission."""
        permission = Permission(
            code=code,
            name=name,
            resource=resource,
            action=action,
            description=description,
        )
        self.db.add(permission)
        await self.db.flush()
        return permission

    async def get_permission_by_code(self, code: str) -> Permission | None:
        """Get permission by code."""
        result = await self.db.execute(select(Permission).where(Permission.code == code))
        return result.scalar_one_or_none()

    async def list_permissions(self) -> list[Permission]:
        """List all permissions."""
        result = await self.db.execute(select(Permission))
        return list(result.scalars().all())

    # Role-Permission operations
    async def assign_permission_to_role(self, role_id: UUID, permission_id: UUID) -> RolePermission:
        """Assign a permission to a role."""
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
        )
        self.db.add(role_permission)
        await self.db.flush()
        return role_permission

    async def revoke_permission_from_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Revoke a permission from a role."""
        result = await self.db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        role_permission = result.scalar_one_or_none()
        if not role_permission:
            return False
        await self.db.delete(role_permission)
        return True

    async def get_role_permissions(self, role_id: UUID) -> list[Permission]:
        """Get all permissions for a role."""
        result = await self.db.execute(
            select(Permission).join(RolePermission).where(RolePermission.role_id == role_id)
        )
        return list(result.scalars().all())

    # User-Role operations
    async def assign_role_to_user(
        self, user_id: UUID, role_id: UUID, assigned_by: UUID | None = None
    ) -> UserRole:
        """Assign a role to a user."""
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
        )
        self.db.add(user_role)
        await self.db.flush()
        return user_role

    async def revoke_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        """Revoke a role from a user."""
        result = await self.db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        user_role = result.scalar_one_or_none()
        if not user_role:
            return False
        await self.db.delete(user_role)
        return True

    async def get_user_roles(self, user_id: UUID) -> list[Role]:
        """Get all roles for a user."""
        result = await self.db.execute(
            select(Role).join(UserRole).where(UserRole.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_user_permissions(self, user_id: UUID) -> list[str]:
        """Get all permission codes for a user."""
        # Get user with roles and permissions
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return []

        # Superuser has all permissions
        if user.is_superuser:
            perms_result = await self.db.execute(select(Permission.code))
            return list(perms_result.scalars().all())

        # Collect permission codes from all roles
        permission_codes = set()
        for user_role in user.roles:
            role_perms = await self.get_role_permissions(user_role.role_id)
            for perm in role_perms:
                permission_codes.add(perm.code)

        return list(permission_codes)

    async def has_permission(self, user_id: UUID, permission_code: str) -> bool:
        """Check if user has a specific permission."""
        permissions = await self.get_user_permissions(user_id)
        return permission_code in permissions

    async def has_any_permission(self, user_id: UUID, permission_codes: list[str]) -> bool:
        """Check if user has any of the specified permissions."""
        permissions = await self.get_user_permissions(user_id)
        return any(code in permissions for code in permission_codes)

    async def has_all_permissions(self, user_id: UUID, permission_codes: list[str]) -> bool:
        """Check if user has all of the specified permissions."""
        permissions = await self.get_user_permissions(user_id)
        return all(code in permissions for code in permission_codes)
