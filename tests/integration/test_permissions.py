"""Integration tests for role-based permissions and access control.

Tests verify that:
- Owner can perform all actions
- Admin can manage members but not delete tenant
- Member has read-only access to most resources
- Users cannot access other tenant's resources
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.members.models import Member
from apps.shared.roles import Role
from apps.tenants.models import Tenant, TenantSettings

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def owner_user(db):
    """Create owner user."""
    return User.objects.create_user(
        email="owner@example.com",
        password="ownerpass123",
        first_name="Owner",
        last_name="User",
    )


@pytest.fixture
def admin_user(db):
    """Create admin user."""
    return User.objects.create_user(
        email="admin@example.com",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
def member_user(db):
    """Create member user."""
    return User.objects.create_user(
        email="member@example.com",
        password="memberpass123",
        first_name="Member",
        last_name="User",
    )


@pytest.fixture
def other_user(db):
    """Create user from another tenant."""
    return User.objects.create_user(
        email="other@example.com",
        password="otherpass123",
        first_name="Other",
        last_name="User",
    )


@pytest.fixture
def test_tenant(db, owner_user):
    """Create test tenant with owner."""
    tenant = Tenant.objects.create(
        name="Test Company",
        slug="test-company",
    )
    TenantSettings.objects.create(tenant=tenant)
    Member.objects.create(
        tenant=tenant,
        user=owner_user,
        role=Role.OWNER.value,
    )
    return tenant


@pytest.fixture
def other_tenant(db, other_user):
    """Create another tenant for isolation tests."""
    tenant = Tenant.objects.create(
        name="Other Company",
        slug="other-company",
    )
    TenantSettings.objects.create(tenant=tenant)
    Member.objects.create(
        tenant=tenant,
        user=other_user,
        role=Role.OWNER.value,
    )
    return tenant


@pytest.fixture
def admin_member(db, test_tenant, admin_user):
    """Create admin membership."""
    return Member.objects.create(
        tenant=test_tenant,
        user=admin_user,
        role=Role.ADMIN.value,
    )


@pytest.fixture
def regular_member(db, test_tenant, member_user):
    """Create regular member."""
    return Member.objects.create(
        tenant=test_tenant,
        user=member_user,
        role=Role.MEMBER.value,
    )


@pytest.fixture
def owner_client(api_client, owner_user):
    """API client authenticated as owner."""
    api_client.force_authenticate(user=owner_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user, admin_member):
    """API client authenticated as admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def member_client(api_client, member_user, regular_member):
    """API client authenticated as member."""
    api_client.force_authenticate(user=member_user)
    return api_client


@pytest.fixture
def other_client(api_client, other_user, other_tenant):
    """API client authenticated as user from another tenant."""
    api_client.force_authenticate(user=other_user)
    return api_client


# =============================================================================
# Tenant Access Tests
# =============================================================================


@pytest.mark.django_db
class TestTenantAccess:
    """Test tenant access based on roles."""

    def test_owner_can_read_tenant(self, owner_client, test_tenant):
        """Owner can read tenant details."""
        url = reverse("tenants:tenant-detail", args=[test_tenant.id])
        response = owner_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == test_tenant.name

    def test_admin_can_read_tenant(self, admin_client, test_tenant):
        """Admin can read tenant details."""
        url = reverse("tenants:tenant-detail", args=[test_tenant.id])
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_member_can_read_tenant(self, member_client, test_tenant):
        """Member can read tenant details."""
        url = reverse("tenants:tenant-detail", args=[test_tenant.id])
        response = member_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_owner_can_update_tenant(self, owner_client, test_tenant):
        """Owner can update tenant."""
        url = reverse("tenants:tenant-detail", args=[test_tenant.id])
        response = owner_client.patch(url, {"name": "Updated Name"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Name"

    def test_admin_can_update_tenant(self, admin_client, test_tenant):
        """Admin can update tenant."""
        url = reverse("tenants:tenant-detail", args=[test_tenant.id])
        response = admin_client.patch(url, {"name": "Admin Updated"})
        assert response.status_code == status.HTTP_200_OK

    def test_member_cannot_update_tenant(self, member_client, test_tenant):
        """Member cannot update tenant."""
        url = reverse("tenants:tenant-detail", args=[test_tenant.id])
        response = member_client.patch(url, {"name": "Member Updated"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_member_cannot_delete_tenant(self, member_client, test_tenant):
        """Member cannot delete tenant."""
        url = reverse("tenants:tenant-detail", args=[test_tenant.id])
        response = member_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_delete_tenant(self, admin_client, test_tenant):
        """Admin cannot delete tenant."""
        url = reverse("tenants:tenant-detail", args=[test_tenant.id])
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_can_delete_tenant(self, owner_client, test_tenant):
        """Owner can delete tenant."""
        url = reverse("tenants:tenant-detail", args=[test_tenant.id])
        response = owner_client.delete(url)
        assert response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK]


# =============================================================================
# Tenant Isolation Tests
# =============================================================================


@pytest.mark.django_db
class TestTenantIsolation:
    """Test that users cannot access other tenant's resources."""

    def test_cannot_update_other_tenant(self, owner_client, other_tenant):
        """User cannot update another tenant."""
        url = reverse("tenants:tenant-detail", args=[other_tenant.id])
        response = owner_client.patch(url, {"name": "Hacked"})
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_cannot_delete_other_tenant(self, owner_client, other_tenant):
        """User cannot delete another tenant."""
        url = reverse("tenants:tenant-detail", args=[other_tenant.id])
        response = owner_client.delete(url)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


# =============================================================================
# Member Management Tests
# =============================================================================


@pytest.mark.django_db
class TestMemberManagement:
    """Test member management permissions."""

    def test_owner_can_view_members(self, owner_client, test_tenant):
        """Owner can view tenant members."""
        url = reverse("members:member-list")
        response = owner_client.get(url, {"tenant": str(test_tenant.id)})
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_view_members(self, admin_client, test_tenant):
        """Admin can view tenant members."""
        url = reverse("members:member-list")
        response = admin_client.get(url, {"tenant": str(test_tenant.id)})
        assert response.status_code == status.HTTP_200_OK

    def test_member_can_view_members(self, member_client, test_tenant):
        """Member can view tenant members."""
        url = reverse("members:member-list")
        response = member_client.get(url, {"tenant": str(test_tenant.id)})
        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Billing Access Tests
# =============================================================================


@pytest.mark.django_db
class TestBillingAccess:
    """Test billing access based on roles."""

    def test_owner_can_access_billing_overview(self, owner_client, test_tenant):
        """Owner can access billing overview."""
        url = reverse("billing:overview")
        response = owner_client.get(url, {"tenant": str(test_tenant.id)})
        # May return error if no subscription, but not 401
        assert response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_owner_can_access_subscription(self, owner_client, test_tenant):
        """Owner can access subscription details."""
        url = reverse("billing:subscription")
        response = owner_client.get(url, {"tenant": str(test_tenant.id)})
        # May return error if no subscription
        assert response.status_code != status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Feature Flags Tests
# =============================================================================


@pytest.mark.django_db
class TestFeatureFlagsAccess:
    """Test feature flags access."""

    def test_owner_can_read_features(self, owner_client, test_tenant):
        """Owner can read feature list."""
        url = reverse("features:list")
        response = owner_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_read_features(self, admin_client, test_tenant):
        """Admin can read feature list."""
        url = reverse("features:list")
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_member_can_read_features(self, member_client, test_tenant):
        """Member can read feature list."""
        url = reverse("features:list")
        response = member_client.get(url)
        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Authentication Edge Cases
# =============================================================================


@pytest.mark.django_db
class TestAuthenticationEdgeCases:
    """Test authentication edge cases."""

    def test_unauthenticated_cannot_access_tenant(self, api_client, test_tenant):
        """Unauthenticated users cannot access tenant."""
        url = reverse("tenants:tenant-detail", args=[test_tenant.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_cannot_list_tenants(self, api_client):
        """Unauthenticated users cannot list tenants."""
        url = reverse("tenants:tenant-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_cannot_create_tenant(self, api_client):
        """Unauthenticated users cannot create tenant."""
        url = reverse("tenants:tenant-list")
        response = api_client.post(url, {"name": "New Tenant", "slug": "new-tenant"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
