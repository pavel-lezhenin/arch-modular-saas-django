"""Integration test fixtures - uses real database via testcontainers.

These tests run against real PostgreSQL to verify:
- Database-specific features (JSON fields, constraints)
- Migrations work correctly
- Multi-table queries and transactions
- Realistic performance characteristics

Usage:
    pytest tests/integration -v                    # SQLite (fast)
    pytest tests/integration -v --use-postgres     # Real PostgreSQL
"""

from __future__ import annotations

import os

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--use-postgres",
        action="store_true",
        default=False,
        help="Run integration tests with real PostgreSQL via testcontainers",
    )


@pytest.fixture(scope="session")
def postgres_container(request):
    """Start PostgreSQL container for tests (if --use-postgres flag is set).

    This fixture is session-scoped to reuse the same container across all tests.
    """
    if not request.config.getoption("--use-postgres"):
        yield None
        return

    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers not installed. Run: uv pip install testcontainers")
        return

    with PostgresContainer("postgres:16-alpine") as postgres:
        # Set environment variables for Django
        os.environ["POSTGRES_HOST"] = postgres.get_container_host_ip()
        os.environ["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))
        os.environ["POSTGRES_DB"] = postgres.dbname
        os.environ["POSTGRES_USER"] = postgres.username
        os.environ["POSTGRES_PASSWORD"] = postgres.password

        # Switch to integration settings
        os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.integration"

        yield postgres


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker, postgres_container):  # noqa: ARG001
    """Configure Django database for tests.

    Runs migrations on either PostgreSQL (if --use-postgres) or SQLite.
    """
    from django.core.management import call_command

    with django_db_blocker.unblock():
        call_command("migrate", "--run-syncdb", verbosity=0)


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
