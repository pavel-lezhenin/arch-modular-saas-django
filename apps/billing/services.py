"""Business logic services for billing module."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.billing.models import (
    BillingInterval,
    Plan,
    PlanTier,
    Subscription,
    SubscriptionStatus,
    UsageRecord,
)
from apps.shared.exceptions import NotFoundError, ValidationError

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from apps.tenants.models import Tenant

logger = logging.getLogger(__name__)


class PlanService:
    """Service for plan operations."""

    @staticmethod
    def get_active_plans(*, public_only: bool = True) -> list[Plan]:
        """Get all active plans.

        Args:
            public_only: If True, return only public plans.

        Returns:
            List of Plan instances.
        """
        qs = Plan.objects.filter(is_active=True)
        if public_only:
            qs = qs.filter(is_public=True)
        return list(qs.order_by("price_monthly"))

    @staticmethod
    def get_plan(plan_id: UUID) -> Plan:
        """Get plan by ID.

        Args:
            plan_id: UUID of the plan.

        Returns:
            Plan instance.

        Raises:
            NotFoundError: If plan not found.
        """
        try:
            return Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            msg = "Plan"
            raise NotFoundError(msg, str(plan_id)) from None

    @staticmethod
    def get_plan_by_tier(tier: PlanTier) -> Plan | None:
        """Get plan by tier.

        Args:
            tier: Plan tier to look up.

        Returns:
            Plan instance or None.
        """
        return Plan.objects.filter(tier=tier, is_active=True).first()

    @staticmethod
    def get_free_plan() -> Plan | None:
        """Get the free plan."""
        return PlanService.get_plan_by_tier(PlanTier.FREE)


class SubscriptionService:
    """Service for subscription operations."""

    @staticmethod
    def get_subscription(tenant: Tenant) -> Subscription | None:
        """Get subscription for a tenant.

        Args:
            tenant: Tenant to get subscription for.

        Returns:
            Subscription instance or None.
        """
        return Subscription.objects.filter(tenant=tenant).select_related("plan").first()

    @staticmethod
    @transaction.atomic
    def create_subscription(
        tenant: Tenant,
        plan: Plan,
        billing_interval: BillingInterval = BillingInterval.MONTHLY,
    ) -> Subscription:
        """Create a subscription for a tenant.

        Args:
            tenant: Tenant to create subscription for.
            plan: Plan to subscribe to.
            billing_interval: Billing interval (monthly/yearly).

        Returns:
            Created Subscription instance.

        Raises:
            ValidationError: If tenant already has subscription.
        """
        existing = SubscriptionService.get_subscription(tenant)
        if existing:
            msg = "Tenant already has a subscription"
            raise ValidationError(msg)

        now = timezone.now()

        # Calculate period end based on interval
        if billing_interval == BillingInterval.YEARLY:
            period_end = now + relativedelta(years=1)
        else:
            period_end = now + relativedelta(months=1)

        subscription = Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=billing_interval,
            current_period_start=now,
            current_period_end=period_end,
        )

        # Update tenant settings with plan limits
        if hasattr(tenant, "settings"):
            tenant.settings.max_members = plan.max_members
            tenant.settings.save(update_fields=["max_members", "updated_at"])

        logger.info(
            "Created subscription for %s: %s (%s)",
            tenant.slug,
            plan.name,
            billing_interval,
        )
        return subscription

    @staticmethod
    @transaction.atomic
    def change_plan(
        tenant: Tenant,
        new_plan: Plan,
        billing_interval: BillingInterval | None = None,
    ) -> Subscription:
        """Change a tenant's subscription plan.

        Args:
            tenant: Tenant to change plan for.
            new_plan: New plan to subscribe to.
            billing_interval: New billing interval (optional).

        Returns:
            Updated Subscription instance.

        Raises:
            NotFoundError: If no subscription exists.
        """
        subscription = SubscriptionService.get_subscription(tenant)
        if not subscription:
            # Create new subscription if none exists
            return SubscriptionService.create_subscription(
                tenant=tenant,
                plan=new_plan,
                billing_interval=billing_interval or BillingInterval.MONTHLY,
            )

        old_plan = subscription.plan
        subscription.plan = new_plan

        if billing_interval:
            subscription.billing_interval = billing_interval

        subscription.save(update_fields=["plan", "billing_interval", "updated_at"])

        # Update tenant settings with new plan limits
        if hasattr(tenant, "settings"):
            tenant.settings.max_members = new_plan.max_members
            tenant.settings.save(update_fields=["max_members", "updated_at"])

        logger.info(
            "Changed plan for %s: %s -> %s",
            tenant.slug,
            old_plan.name,
            new_plan.name,
        )
        return subscription

    @staticmethod
    @transaction.atomic
    def cancel_subscription(tenant: Tenant, *, immediate: bool = False) -> Subscription:
        """Cancel a tenant's subscription.

        Args:
            tenant: Tenant to cancel subscription for.
            immediate: If True, cancel immediately. Otherwise, cancel at period end.

        Returns:
            Updated Subscription instance.

        Raises:
            NotFoundError: If no subscription exists.
        """
        subscription = SubscriptionService.get_subscription(tenant)
        if not subscription:
            msg = "Subscription"
            raise NotFoundError(msg, str(tenant.id))

        subscription.cancelled_at = timezone.now()

        if immediate:
            subscription.status = SubscriptionStatus.CANCELLED
        # If not immediate, Stripe webhook will update status at period end

        subscription.save(update_fields=["status", "cancelled_at", "updated_at"])

        logger.info("Cancelled subscription for %s (immediate=%s)", tenant.slug, immediate)
        return subscription

    @staticmethod
    def update_subscription_from_stripe(
        stripe_subscription_id: str,
        status: str,
        current_period_start: int,
        current_period_end: int,
    ) -> Subscription | None:
        """Update subscription from Stripe webhook.

        Args:
            stripe_subscription_id: Stripe subscription ID.
            status: New status from Stripe.
            current_period_start: Unix timestamp.
            current_period_end: Unix timestamp.

        Returns:
            Updated Subscription or None if not found.
        """
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
        except Subscription.DoesNotExist:
            logger.warning(
                "Subscription not found for Stripe ID: %s",
                stripe_subscription_id,
            )
            return None

        # Map Stripe status to our status
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELLED,
            "incomplete": SubscriptionStatus.INCOMPLETE,
            "trialing": SubscriptionStatus.TRIALING,
        }

        subscription.status = status_map.get(status, SubscriptionStatus.ACTIVE)
        subscription.current_period_start = timezone.datetime.fromtimestamp(
            current_period_start, tz=timezone.utc
        )
        subscription.current_period_end = timezone.datetime.fromtimestamp(
            current_period_end, tz=timezone.utc
        )
        subscription.save(
            update_fields=[
                "status",
                "current_period_start",
                "current_period_end",
                "updated_at",
            ]
        )

        logger.info(
            "Updated subscription %s from Stripe: status=%s",
            subscription.tenant.slug,
            status,
        )
        return subscription


class StripeService:
    """Service for Stripe operations.

    This service handles all Stripe API interactions.
    If Stripe is not configured, operations are no-ops.
    """

    @staticmethod
    def is_configured() -> bool:
        """Check if Stripe is configured."""
        return bool(getattr(settings, "STRIPE_SECRET_KEY", None))

    @staticmethod
    def create_checkout_session(
        tenant: Tenant,
        plan: Plan,
        billing_interval: BillingInterval,
        success_url: str,
        cancel_url: str,
    ) -> str | None:
        """Create a Stripe Checkout session.

        Args:
            tenant: Tenant to create session for.
            plan: Plan to subscribe to.
            billing_interval: Monthly or yearly.
            success_url: URL to redirect on success.
            cancel_url: URL to redirect on cancel.

        Returns:
            Checkout session URL or None if Stripe not configured.
        """
        if not StripeService.is_configured():
            logger.warning("Stripe not configured - skipping checkout session creation")
            return None

        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Get appropriate price ID
        if billing_interval == BillingInterval.YEARLY:
            price_id = plan.stripe_price_id_yearly
        else:
            price_id = plan.stripe_price_id_monthly

        if not price_id:
            logger.error("No Stripe price ID for plan %s (%s)", plan.name, billing_interval)
            return None

        # Create or get customer
        if not tenant.stripe_customer_id:
            customer = stripe.Customer.create(
                name=tenant.name,
                metadata={"tenant_id": str(tenant.id)},
            )
            tenant.stripe_customer_id = customer.id
            tenant.save(update_fields=["stripe_customer_id"])

        session = stripe.checkout.Session.create(
            customer=tenant.stripe_customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"tenant_id": str(tenant.id)},
        )

        return session.url

    @staticmethod
    def create_portal_session(tenant: Tenant, return_url: str) -> str | None:
        """Create a Stripe Customer Portal session.

        Args:
            tenant: Tenant to create session for.
            return_url: URL to return to after portal.

        Returns:
            Portal session URL or None if not available.
        """
        if not StripeService.is_configured():
            logger.warning("Stripe not configured - skipping portal session creation")
            return None

        if not tenant.stripe_customer_id:
            logger.warning("No Stripe customer for tenant %s", tenant.slug)
            return None

        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY

        session = stripe.billing_portal.Session.create(
            customer=tenant.stripe_customer_id,
            return_url=return_url,
        )

        return session.url


class UsageService:
    """Service for usage tracking."""

    @staticmethod
    def record_usage(
        tenant: Tenant,
        metric: str,
        quantity: int = 1,
        period_date: date | None = None,
    ) -> UsageRecord:
        """Record usage for a tenant.

        Args:
            tenant: Tenant to record usage for.
            metric: Usage metric name.
            quantity: Amount to add.
            period_date: Date within the billing period.

        Returns:
            Updated or created UsageRecord.
        """
        if period_date is None:
            period_date = timezone.now().date()

        # Get current billing period (monthly)
        period_start = period_date.replace(day=1)
        next_month = period_start + relativedelta(months=1)
        period_end = next_month - relativedelta(days=1)

        record, created = UsageRecord.objects.get_or_create(
            tenant=tenant,
            metric=metric,
            period_start=period_start,
            defaults={"period_end": period_end, "quantity": 0},
        )

        record.quantity += quantity
        record.save(update_fields=["quantity", "updated_at"])

        return record

    @staticmethod
    def get_current_usage(tenant: Tenant) -> list[UsageRecord]:
        """Get current period usage for a tenant.

        Args:
            tenant: Tenant to get usage for.

        Returns:
            List of current period UsageRecords.
        """
        today = timezone.now().date()
        period_start = today.replace(day=1)

        return list(
            UsageRecord.objects.filter(tenant=tenant, period_start=period_start)
        )

    @staticmethod
    def get_usage_history(
        tenant: Tenant, months: int = 6
    ) -> list[UsageRecord]:
        """Get usage history for a tenant.

        Args:
            tenant: Tenant to get usage for.
            months: Number of months of history.

        Returns:
            List of UsageRecords.
        """
        cutoff = timezone.now().date() - relativedelta(months=months)

        return list(
            UsageRecord.objects.filter(
                tenant=tenant, period_start__gte=cutoff
            ).order_by("-period_start", "metric")
        )
