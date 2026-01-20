"""Middleware for tenant context handling."""
from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse

    from apps.tenants.models import Tenant

# Context variable to store current tenant
_current_tenant: contextvars.ContextVar[Tenant | None] = contextvars.ContextVar(
    "current_tenant",
    default=None,
)


def get_current_tenant() -> Any | None:
    """Get the current tenant from context.

    Returns:
        The current tenant or None if not set.
    """
    return _current_tenant.get()


def set_current_tenant(tenant: Any | None) -> None:
    """Set the current tenant in context.

    Args:
        tenant: The tenant to set as current.
    """
    _current_tenant.set(tenant)


class TenantContextMiddleware:
    """Middleware to set tenant context from request.

    Extracts tenant from:
    1. X-Tenant-ID header
    2. tenant_id query parameter
    3. URL path parameter

    The tenant is then available via `get_current_tenant()`.
    """

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        """Initialize middleware.

        Args:
            get_response: The next middleware or view.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request.

        Args:
            request: The incoming HTTP request.

        Returns:
            The HTTP response.
        """
        # Reset tenant context
        set_current_tenant(None)

        # Try to get tenant ID from various sources
        tenant_id = self._extract_tenant_id(request)

        if tenant_id and request.user.is_authenticated:
            self._set_tenant_from_id(tenant_id, request)

        response = self.get_response(request)

        # Clean up
        set_current_tenant(None)

        return response

    def _extract_tenant_id(self, request: HttpRequest) -> UUID | None:
        """Extract tenant ID from request.

        Args:
            request: The incoming HTTP request.

        Returns:
            The tenant UUID or None.
        """
        # Check header first
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            try:
                return UUID(tenant_header)
            except ValueError:
                pass

        # Check query parameter
        tenant_param = request.GET.get("tenant_id")
        if tenant_param:
            try:
                return UUID(tenant_param)
            except ValueError:
                pass

        return None

    def _set_tenant_from_id(self, tenant_id: UUID, request: HttpRequest) -> None:
        """Set tenant context from ID.

        Args:
            tenant_id: The tenant UUID.
            request: The incoming HTTP request.
        """
        from apps.members.models import Member
        from apps.tenants.models import Tenant

        try:
            # Verify user has access to tenant
            tenant = Tenant.objects.get(id=tenant_id)
            Member.objects.get(tenant=tenant, user=request.user)
            set_current_tenant(tenant)
        except (Tenant.DoesNotExist, Member.DoesNotExist):
            pass
