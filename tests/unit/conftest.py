"""Unit test fixtures - no external dependencies."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from apps.shared.roles import Role


@pytest.fixture
def mock_tenant():
    """Mock tenant for unit tests."""
    tenant = MagicMock()
    tenant.id = uuid4()
    tenant.name = "Test Company"
    tenant.slug = "test-company"
    tenant.is_active = True
    tenant.settings = MagicMock()
    tenant.settings.max_members = 10
    return tenant


@pytest.fixture
def mock_user():
    """Mock user for unit tests."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.is_active = True
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_member(mock_tenant, mock_user):
    """Mock member for unit tests."""
    member = MagicMock()
    member.id = uuid4()
    member.tenant = mock_tenant
    member.user = mock_user
    member.role = Role.MEMBER.value
    member.is_active = True
    return member


@pytest.fixture
def mock_request(mock_user):
    """Mock HTTP request for unit tests."""
    request = MagicMock()
    request.user = mock_user
    request.META = {"HTTP_X_TENANT_ID": str(uuid4())}
    return request
