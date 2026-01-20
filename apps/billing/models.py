"""Billing-related models."""
from __future__ import annotations

from django.db import models

from apps.shared.models import BaseModel


class PlanTier(models.TextChoices):
    """Plan tier levels."""

    FREE = "free", "Free"
    STARTER = "starter", "Starter"
    PROFESSIONAL = "professional", "Professional"
    ENTERPRISE = "enterprise", "Enterprise"


class BillingInterval(models.TextChoices):
    """Billing interval options."""

    MONTHLY = "monthly", "Monthly"
    YEARLY = "yearly", "Yearly"


class Plan(BaseModel):
    """Subscription plan definition.

    Defines what features and limits are available at each pricing tier.
    """

    name = models.CharField(max_length=100)
    tier = models.CharField(
        max_length=20,
        choices=PlanTier.choices,
        unique=True,
    )
    description = models.TextField(blank=True)

    # Pricing (in cents to avoid floating point issues)
    price_monthly = models.PositiveIntegerField(default=0)  # cents
    price_yearly = models.PositiveIntegerField(default=0)  # cents

    # Stripe integration
    stripe_price_id_monthly = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id_yearly = models.CharField(max_length=255, blank=True, null=True)

    # Limits
    max_members = models.PositiveIntegerField(default=5)
    max_storage_gb = models.PositiveIntegerField(default=1)

    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)  # Show on pricing page

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Plans"
        ordering = ["price_monthly"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name} ({self.tier})"

    @property
    def price_monthly_dollars(self) -> float:
        """Get monthly price in dollars."""
        return self.price_monthly / 100

    @property
    def price_yearly_dollars(self) -> float:
        """Get yearly price in dollars."""
        return self.price_yearly / 100


class SubscriptionStatus(models.TextChoices):
    """Subscription status values."""

    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past Due"
    CANCELLED = "cancelled", "Cancelled"
    INCOMPLETE = "incomplete", "Incomplete"
    TRIALING = "trialing", "Trialing"


class Subscription(BaseModel):
    """Tenant subscription to a plan.

    Tracks the billing relationship between tenant and plan.
    """

    tenant = models.OneToOneField(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    billing_interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
    )

    # Stripe integration
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)

    # Period tracking
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.tenant.name} - {self.plan.name}"

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)


class UsageRecord(BaseModel):
    """Track usage for metered billing features.

    Used for features that are billed based on usage (API calls, storage, etc.)
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="usage_records",
    )
    metric = models.CharField(max_length=50)  # e.g., "api_calls", "storage_gb"
    quantity = models.PositiveIntegerField(default=0)
    period_start = models.DateField()
    period_end = models.DateField()

    class Meta:
        verbose_name = "Usage Record"
        verbose_name_plural = "Usage Records"
        unique_together = [("tenant", "metric", "period_start")]
        ordering = ["-period_start"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.tenant.name} - {self.metric}: {self.quantity}"
