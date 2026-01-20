"""Integration test fixtures - uses real database."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    """DRF API test client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def authenticated_client(api_client, user) -> APIClient:
    """API client with authenticated user."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    from apps.tenants.models import Tenant, TenantSettings

    tenant = Tenant.objects.create(
        name="Test Company",
        slug="test-company",
    )
    TenantSettings.objects.create(tenant=tenant)
    return tenant


@pytest.fixture
def member(db, tenant, user):
    """Create a test membership."""
    from apps.members.models import Member
    from apps.shared.roles import Role

    return Member.objects.create(
        tenant=tenant,
        user=user,
        role=Role.OWNER.value,
    )


@pytest.fixture
def authenticated_member_client(api_client, user, member) -> APIClient:
    """API client with authenticated user who is a tenant member."""
    api_client.force_authenticate(user=user)
    api_client.credentials(HTTP_X_TENANT_ID=str(member.tenant.id))
    return api_client
