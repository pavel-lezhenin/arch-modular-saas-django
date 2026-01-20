"""Feature flag models."""
from __future__ import annotations

from django.db import models

from apps.shared.models import BaseModel


class Feature(BaseModel):
    """Feature definition.

    Defines a feature that can be enabled/disabled per tenant.
    """

    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Feature behavior
    is_active = models.BooleanField(default=True)  # Global kill switch
    enabled_by_default = models.BooleanField(default=False)
    requires_plan_tier = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Minimum plan tier required (free, starter, professional, enterprise)",
    )

    class Meta:
        verbose_name = "Feature"
        verbose_name_plural = "Features"
        ordering = ["code"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name} ({self.code})"


class TenantFeature(BaseModel):
    """Feature flag override for a specific tenant.

    Allows enabling/disabling features per-tenant, overriding defaults.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="feature_flags",
    )
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name="tenant_overrides",
    )
    is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tenant Feature"
        verbose_name_plural = "Tenant Features"
        unique_together = [("tenant", "feature")]

    def __str__(self) -> str:
        """Return string representation."""
        status = "enabled" if self.is_enabled else "disabled"
        return f"{self.feature.code} for {self.tenant.name}: {status}"
