"""DRF permission classes for tenant-based access control."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework import permissions

from .roles import Permission, has_permission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class TenantPermission(permissions.BasePermission):
    """Base permission class for tenant-scoped resources.

    Subclasses should set `required_permission` to the permission
    that is required to access the resource.
    """

    required_permission: Permission | None = None

    def has_object_permission(
        self,
        request: Request,
        view: APIView,  # noqa: ARG002
        obj: Any,
    ) -> bool:
        """Check if user has permission for the object.

        Args:
            request: The incoming request.
            view: The view being accessed.
            obj: The object being accessed.

        Returns:
            True if user has permission, False otherwise.
        """
        if not request.user.is_authenticated:
            return False

        # Get tenant from object (either the object itself or via tenant FK)
        tenant = getattr(obj, "tenant", obj)

        # Import here to avoid circular imports
        from apps.members.models import Member

        try:
            member = Member.objects.get(
                tenant=tenant,
                user=request.user,
            )
        except Member.DoesNotExist:
            return False

        if self.required_permission is None:
            return True

        return has_permission(member.role, self.required_permission)


class IsTenantMember(TenantPermission):
    """User must be a member of the tenant."""

    required_permission = Permission.TENANT_READ


class IsTenantAdmin(TenantPermission):
    """User must be admin or owner of the tenant."""

    required_permission = Permission.TENANT_UPDATE


class IsTenantOwner(TenantPermission):
    """User must be owner of the tenant."""

    required_permission = Permission.TENANT_DELETE


class CanInviteMembers(TenantPermission):
    """User can invite new members to the tenant."""

    required_permission = Permission.MEMBERS_INVITE


class CanRemoveMembers(TenantPermission):
    """User can remove members from the tenant."""

    required_permission = Permission.MEMBERS_REMOVE


class CanManageMembers(TenantPermission):
    """User can manage members (invite, remove, change roles)."""

    required_permission = Permission.MEMBERS_INVITE


class CanManageBilling(TenantPermission):
    """User can manage billing for the tenant."""

    required_permission = Permission.BILLING_MANAGE


class CanReadBilling(TenantPermission):
    """User can read billing information."""

    required_permission = Permission.BILLING_READ


class CanOverrideFeatures(TenantPermission):
    """User can override feature flags for the tenant."""

    required_permission = Permission.FEATURES_OVERRIDE
