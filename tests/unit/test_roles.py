"""Unit tests for shared roles module."""
from __future__ import annotations

import pytest

from apps.shared.roles import Permission, Role, has_permission


class TestRole:
    """Tests for Role enum."""

    def test_role_values(self):
        """Test that all roles have expected values."""
        assert Role.OWNER.value == "owner"
        assert Role.ADMIN.value == "admin"
        assert Role.MEMBER.value == "member"

    def test_role_hierarchy(self):
        """Test role ordering."""
        roles = list(Role)
        assert roles == [Role.OWNER, Role.ADMIN, Role.MEMBER]


class TestPermission:
    """Tests for Permission enum."""

    def test_permission_values(self):
        """Test that permissions have expected values."""
        assert Permission.TENANT_READ.value == "tenant:read"
        assert Permission.TENANT_UPDATE.value == "tenant:update"
        assert Permission.BILLING_MANAGE.value == "billing:manage"

    def test_all_permissions_have_values(self):
        """Test that all permissions have non-empty values."""
        for perm in Permission:
            assert perm.value
            assert ":" in perm.value


class TestHasPermission:
    """Tests for has_permission function."""

    def test_owner_has_all_permissions(self):
        """Test that owner role has all permissions."""
        for perm in Permission:
            assert has_permission(Role.OWNER, perm) is True

    def test_member_limited_permissions(self):
        """Test that member role has limited permissions."""
        assert has_permission(Role.MEMBER, Permission.TENANT_READ) is True
        assert has_permission(Role.MEMBER, Permission.TENANT_UPDATE) is False
        assert has_permission(Role.MEMBER, Permission.BILLING_MANAGE) is False

    def test_admin_intermediate_permissions(self):
        """Test that admin role has more than member but less than owner."""
        assert has_permission(Role.ADMIN, Permission.MEMBERS_INVITE) is True
        assert has_permission(Role.ADMIN, Permission.BILLING_MANAGE) is True  # Admin can manage billing
        # Owner-only permissions
        assert has_permission(Role.ADMIN, Permission.TENANT_DELETE) is False

    def test_with_string_role(self):
        """Test has_permission with string role value."""
        assert has_permission(Role("owner"), Permission.BILLING_MANAGE) is True
        assert has_permission(Role("member"), Permission.BILLING_MANAGE) is False
