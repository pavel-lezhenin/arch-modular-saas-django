"""API views for tenants module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.shared.permissions import IsTenantAdmin, IsTenantOwner
from apps.tenants.models import Tenant
from apps.tenants.serializers import (
    TenantCreateSerializer,
    TenantSerializer,
    TenantSettingsSerializer,
    TenantStatusSerializer,
    TenantUpdateSerializer,
)
from apps.tenants.services import TenantService

if TYPE_CHECKING:
    from rest_framework.request import Request


class TenantViewSet(viewsets.ModelViewSet):
    """ViewSet for tenant CRUD operations."""

    queryset = Tenant.objects.select_related("settings").all()
    serializer_class = TenantSerializer

    def get_serializer_class(self):  # noqa: ANN201
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return TenantCreateSerializer
        if self.action in ("update", "partial_update"):
            return TenantUpdateSerializer
        if self.action == "update_status":
            return TenantStatusSerializer
        if self.action == "update_settings":
            return TenantSettingsSerializer
        return TenantSerializer

    def get_permissions(self):  # noqa: ANN201
        """Return permissions based on action."""
        if self.action in ("update", "partial_update", "update_settings"):
            return [IsTenantAdmin()]
        if self.action in ("destroy", "update_status"):
            return [IsTenantOwner()]
        return super().get_permissions()

    def create(self, request: Request) -> Response:
        """Create a new tenant.

        Args:
            request: HTTP request with tenant data.

        Returns:
            Created tenant data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = TenantService.create_tenant(
            name=serializer.validated_data["name"],
            slug=serializer.validated_data["slug"],
        )

        output_serializer = TenantSerializer(tenant)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request: Request, *args, **kwargs) -> Response:  # noqa: ANN002, ANN003, ARG002
        """Update tenant details.

        Args:
            request: HTTP request with update data.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Updated tenant data.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        tenant = TenantService.update_tenant(
            tenant_id=instance.id,
            name=serializer.validated_data.get("name"),
        )

        output_serializer = TenantSerializer(tenant)
        return Response(output_serializer.data)

    @action(detail=True, methods=["post"], url_path="status")
    def update_status(self, request: Request, pk: str | None = None) -> Response:  # noqa: ARG002
        """Update tenant status.

        Args:
            request: HTTP request with new status.
            pk: Tenant primary key (unused, get_object handles it).

        Returns:
            Updated tenant data.
        """
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = TenantService.update_status(
            tenant_id=instance.id,
            status=serializer.validated_data["status"],
        )

        output_serializer = TenantSerializer(tenant)
        return Response(output_serializer.data)

    @action(detail=True, methods=["get", "patch"], url_path="settings")
    def update_settings(self, request: Request, pk: str | None = None) -> Response:  # noqa: ARG002
        """Get or update tenant settings.

        Args:
            request: HTTP request (GET or PATCH).
            pk: Tenant primary key (unused, get_object handles it).

        Returns:
            Tenant settings data.
        """
        instance = self.get_object()

        if request.method == "GET":
            serializer = TenantSettingsSerializer(instance.settings)
            return Response(serializer.data)

        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        settings = TenantService.update_settings(
            tenant_id=instance.id,
            **serializer.validated_data,
        )

        output_serializer = TenantSettingsSerializer(settings)
        return Response(output_serializer.data)
