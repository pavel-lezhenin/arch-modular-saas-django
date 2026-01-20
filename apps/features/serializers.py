"""Serializers for features module."""

from __future__ import annotations

from rest_framework import serializers

from apps.features.models import Feature, TenantFeature


class FeatureSerializer(serializers.ModelSerializer):
    """Serializer for Feature model."""

    class Meta:
        model = Feature
        fields = [
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "enabled_by_default",
            "requires_plan_tier",
        ]


class TenantFeatureSerializer(serializers.ModelSerializer):
    """Serializer for TenantFeature model."""

    feature = FeatureSerializer(read_only=True)

    class Meta:
        model = TenantFeature
        fields = ["id", "feature", "is_enabled", "created_at", "updated_at"]


class TenantFeatureUpdateSerializer(serializers.Serializer):
    """Serializer for updating tenant feature flags."""

    feature_code = serializers.CharField()
    is_enabled = serializers.BooleanField()


class FeatureStatusSerializer(serializers.Serializer):
    """Serializer for feature status check response."""

    code = serializers.CharField()
    name = serializers.CharField()
    is_enabled = serializers.BooleanField()
    reason = serializers.CharField()


class TenantFeaturesListSerializer(serializers.Serializer):
    """Serializer for list of tenant feature statuses."""

    features = FeatureStatusSerializer(many=True)
