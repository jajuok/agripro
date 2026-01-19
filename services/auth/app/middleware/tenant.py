"""Multi-tenancy middleware."""

from contextvars import ContextVar
from typing import Any
from uuid import UUID

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# Context variable to store current tenant
current_tenant_id: ContextVar[UUID | None] = ContextVar("current_tenant_id", default=None)


def get_current_tenant() -> UUID | None:
    """Get the current tenant ID from context."""
    return current_tenant_id.get()


def set_current_tenant(tenant_id: UUID | None) -> None:
    """Set the current tenant ID in context."""
    current_tenant_id.set(tenant_id)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for extracting and setting tenant context from requests."""

    TENANT_HEADER = "X-Tenant-ID"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Extract tenant ID from request and set in context."""
        tenant_id: UUID | None = None

        # Try to get tenant from header
        tenant_header = request.headers.get(self.TENANT_HEADER)
        if tenant_header:
            try:
                tenant_id = UUID(tenant_header)
            except ValueError:
                pass

        # Set tenant in context
        token = current_tenant_id.set(tenant_id)

        try:
            response = await call_next(request)
            return response
        finally:
            # Reset context
            current_tenant_id.reset(token)


class TenantFilter:
    """Mixin for SQLAlchemy queries to filter by tenant."""

    @staticmethod
    def apply_tenant_filter(query: Any, tenant_column: Any) -> Any:
        """Apply tenant filter to a query if tenant is set."""
        tenant_id = get_current_tenant()
        if tenant_id:
            return query.where(tenant_column == tenant_id)
        return query
