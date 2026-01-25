"""Serializers for tenant models."""

from __future__ import annotations

from rest_framework import serializers

from apps.tenants.models import Tenant, TenantSettings, TenantStatus


class TenantSettingsSerializer(serializers.ModelSerializer):
    """Serializer for TenantSettings."""

    class Meta:
        model = TenantSettings
        fields = [
            "logo_url",
            "primary_color",
            "secondary_color",
            "allow_member_invites",
            "max_members",
            "require_2fa",
            "email_notifications_enabled",
            "weekly_digest_enabled",
        ]
        read_only_fields = ["max_members"]  # Controlled by plan


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model."""

    settings = TenantSettingsSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "status",
            "is_active",
            "trial_ends_at",
            "subscription_ends_at",
            "settings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "trial_ends_at",
            "subscription_ends_at",
            "created_at",
            "updated_at",
        ]


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new tenant."""

    class Meta:
        model = Tenant
        fields = ["name", "slug"]

    def validate_slug(self, value: str) -> str:
        """Validate slug is URL-safe and unique.

        Args:
            value: The slug value to validate.

        Returns:
            Validated slug.

        Raises:
            ValidationError: If slug is invalid or taken.
        """
        if not value.replace("-", "").replace("_", "").isalnum():
            msg = "Slug must contain only letters, numbers, hyphens, and underscores"
            raise serializers.ValidationError(msg)
        return value.lower()


class TenantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tenant details."""

    class Meta:
        model = Tenant
        fields = ["name"]


class TenantStatusSerializer(serializers.Serializer):
    """Serializer for tenant status updates."""

    status = serializers.ChoiceField(
        choices=[
            (TenantStatus.ACTIVE, "Active"),
            (TenantStatus.SUSPENDED, "Suspended"),
            (TenantStatus.CANCELLED, "Cancelled"),
        ]
    )
