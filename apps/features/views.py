"""API views for features module."""
from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.features.serializers import (
    FeatureSerializer,
    FeatureStatusSerializer,
    TenantFeatureUpdateSerializer,
)
from apps.features.services import FeatureService
from apps.shared.middleware import get_current_tenant
from apps.shared.permissions import IsTenantAdmin, IsTenantMember

if TYPE_CHECKING:
    from rest_framework.request import Request


class FeatureListView(APIView):
    """List all available features."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:  # noqa: ARG002
        """Get all features.

        Args:
            request: HTTP request.

        Returns:
            List of features.
        """
        features = FeatureService.get_all_features()
        serializer = FeatureSerializer(features, many=True)
        return Response(serializer.data)


class TenantFeaturesView(APIView):
    """View and manage feature flags for current tenant."""

    def get_permissions(self):  # noqa: ANN201
        """Return permissions based on method."""
        if self.request.method == "GET":
            return [IsAuthenticated(), IsTenantMember()]
        return [IsAuthenticated(), IsTenantAdmin()]

    def get(self, request: Request) -> Response:  # noqa: ARG002
        """Get all feature statuses for current tenant.

        Args:
            request: HTTP request.

        Returns:
            Feature statuses.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        features = FeatureService.get_tenant_features(tenant)
        serializer = FeatureStatusSerializer(features, many=True)
        return Response({"features": serializer.data})

    def post(self, request: Request) -> Response:
        """Update feature flag for current tenant.

        Args:
            request: HTTP request with feature update data.

        Returns:
            Updated feature status.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TenantFeatureUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        FeatureService.set_tenant_feature(
            tenant=tenant,
            feature_code=serializer.validated_data["feature_code"],
            is_enabled=serializer.validated_data["is_enabled"],
        )

        # Return updated status
        is_enabled, reason = FeatureService.is_feature_enabled(
            tenant, serializer.validated_data["feature_code"]
        )

        feature = FeatureService.get_feature(serializer.validated_data["feature_code"])
        return Response({
            "code": feature.code,
            "name": feature.name,
            "is_enabled": is_enabled,
            "reason": reason,
        })

    def delete(self, request: Request) -> Response:
        """Reset feature flag to default for current tenant.

        Args:
            request: HTTP request with feature code.

        Returns:
            Updated feature status.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        feature_code = request.data.get("feature_code")
        if not feature_code:
            return Response(
                {"detail": "feature_code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        FeatureService.reset_tenant_feature(tenant, feature_code)

        # Return updated status
        is_enabled, reason = FeatureService.is_feature_enabled(tenant, feature_code)
        feature = FeatureService.get_feature(feature_code)

        return Response({
            "code": feature.code,
            "name": feature.name,
            "is_enabled": is_enabled,
            "reason": reason,
        })


class FeatureCheckView(APIView):
    """Check if a specific feature is enabled."""

    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request: Request, feature_code: str) -> Response:  # noqa: ARG002
        """Check if feature is enabled for current tenant.

        Args:
            request: HTTP request.
            feature_code: Feature code to check.

        Returns:
            Feature status.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_enabled, reason = FeatureService.is_feature_enabled(tenant, feature_code)

        try:
            feature = FeatureService.get_feature(feature_code)
            name = feature.name
        except Exception:
            name = feature_code

        return Response({
            "code": feature_code,
            "name": name,
            "is_enabled": is_enabled,
            "reason": reason,
        })
