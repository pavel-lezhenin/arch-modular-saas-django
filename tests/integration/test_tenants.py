"""Integration tests for tenants module."""
from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestTenantAPI:
    """Integration tests for Tenant API."""

    def test_create_tenant(self, authenticated_client):
        """Test creating a new tenant."""
        url = reverse("tenants:tenant-list")
        data = {
            "name": "New Company",
            "slug": "new-company",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Company"
        assert response.data["slug"] == "new-company"
        assert response.data["status"] == "trial"

    def test_create_tenant_duplicate_slug(self, authenticated_client, tenant):
        """Test that duplicate slugs are rejected."""
        url = reverse("tenants:tenant-list")
        data = {
            "name": "Another Company",
            "slug": tenant.slug,  # Duplicate
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_tenant(self, authenticated_member_client, tenant):
        """Test retrieving a tenant."""
        url = reverse("tenants:tenant-detail", args=[tenant.id])

        response = authenticated_member_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == tenant.name

    def test_update_tenant(self, authenticated_member_client, tenant):
        """Test updating a tenant."""
        url = reverse("tenants:tenant-detail", args=[tenant.id])
        data = {"name": "Updated Company Name"}

        response = authenticated_member_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Company Name"


@pytest.mark.django_db
class TestTenantSettings:
    """Integration tests for Tenant Settings."""

    def test_get_settings(self, authenticated_member_client, tenant):
        """Test retrieving tenant settings."""
        url = reverse("tenants:tenant-update-settings", args=[tenant.id])

        response = authenticated_member_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "max_members" in response.data

    def test_update_settings(self, authenticated_member_client, tenant):
        """Test updating tenant settings."""
        url = reverse("tenants:tenant-update-settings", args=[tenant.id])
        data = {"primary_color": "#FF5733"}

        response = authenticated_member_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["primary_color"] == "#FF5733"
