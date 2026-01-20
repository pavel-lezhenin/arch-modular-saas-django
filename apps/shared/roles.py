"""Role and permission definitions for tenant-based access control."""
from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """Tenant member roles.

    Roles are hierarchical: owner > admin > member.
    """

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Permission(StrEnum):
    """Available permissions for tenant resources."""

    # Tenant permissions
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"

    # Member permissions
    MEMBERS_INVITE = "members:invite"
    MEMBERS_REMOVE = "members:remove"
    MEMBERS_CHANGE_ROLE = "members:change_role"

    # Billing permissions
    BILLING_READ = "billing:read"
    BILLING_MANAGE = "billing:manage"

    # Feature permissions
    FEATURES_READ = "features:read"
    FEATURES_OVERRIDE = "features:override"


# Role -> permissions mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.OWNER: set(Permission),  # Owner has all permissions
    Role.ADMIN: {
        Permission.TENANT_READ,
        Permission.TENANT_UPDATE,
        Permission.MEMBERS_INVITE,
        Permission.MEMBERS_REMOVE,
        Permission.MEMBERS_CHANGE_ROLE,
        Permission.BILLING_READ,
        Permission.BILLING_MANAGE,
        Permission.FEATURES_READ,
    },
    Role.MEMBER: {
        Permission.TENANT_READ,
        Permission.FEATURES_READ,
    },
}


def has_permission(role: Role | str, permission: Permission | str) -> bool:
    """Check if a role has a specific permission.

    Args:
        role: The role to check.
        permission: The permission to verify.

    Returns:
        True if the role has the permission, False otherwise.
    """
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            return False

    if isinstance(permission, str):
        try:
            permission = Permission(permission)
        except ValueError:
            return False

    return permission in ROLE_PERMISSIONS.get(role, set())


def get_role_permissions(role: Role | str) -> set[Permission]:
    """Get all permissions for a role.

    Args:
        role: The role to get permissions for.

    Returns:
        Set of permissions for the role.
    """
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            return set()

    return ROLE_PERMISSIONS.get(role, set())
