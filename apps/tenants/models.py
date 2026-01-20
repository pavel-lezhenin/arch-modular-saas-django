"""Tenant models."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from apps.shared.models import BaseModel


class TenantStatus(models.TextChoices):
    """Tenant lifecycle status."""

    TRIAL = "trial", "Trial"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    CANCELLED = "cancelled", "Cancelled"


class Tenant(BaseModel):
    """Tenant represents an organization/company in the system.

    This is the root entity for multi-tenancy. All other resources
    are scoped to a tenant.
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.TRIAL,
    )

    # Optional billing fields (linked to Stripe via dj-stripe)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)

    # Trial/subscription tracking
    trial_ends_at = models.DateTimeField(blank=True, null=True)
    subscription_ends_at = models.DateTimeField(blank=True, null=True)

    # Type hint for OneToOne reverse relation (populated by TenantSettings)
    # Django creates 'settings' attribute automatically via OneToOneField related_name
    if TYPE_CHECKING:
        settings: TenantSettings

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        return self.name

    @property
    def is_active(self) -> bool:
        """Check if tenant is active (trial or active status)."""
        return self.status in (TenantStatus.TRIAL, TenantStatus.ACTIVE)


class TenantSettings(BaseModel):
    """Tenant-specific settings and configuration.

    Stores configuration options that can be customized per-tenant.
    """

    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="settings",
    )

    # Branding
    logo_url = models.URLField(blank=True, null=True)
    primary_color = models.CharField(max_length=7, default="#3B82F6")  # Hex color
    secondary_color = models.CharField(max_length=7, default="#10B981")

    # Feature settings
    allow_member_invites = models.BooleanField(default=True)
    max_members = models.PositiveIntegerField(default=10)
    require_2fa = models.BooleanField(default=False)

    # Notifications
    email_notifications_enabled = models.BooleanField(default=True)
    weekly_digest_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tenant Settings"
        verbose_name_plural = "Tenant Settings"

    def __str__(self) -> str:
        """Return string representation."""
        return f"Settings for {self.tenant.name}"
