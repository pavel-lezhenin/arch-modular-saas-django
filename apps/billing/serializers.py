"""Serializers for billing module."""
from __future__ import annotations

from rest_framework import serializers

from apps.billing.models import (
    BillingInterval,
    Plan,
    Subscription,
    UsageRecord,
)


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for Plan model."""

    price_monthly_dollars = serializers.FloatField(read_only=True)
    price_yearly_dollars = serializers.FloatField(read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "tier",
            "description",
            "price_monthly",
            "price_yearly",
            "price_monthly_dollars",
            "price_yearly_dollars",
            "max_members",
            "max_storage_gb",
            "is_active",
        ]


class PlanListSerializer(serializers.ModelSerializer):
    """Simplified serializer for plan listing."""

    price_monthly_dollars = serializers.FloatField(read_only=True)
    price_yearly_dollars = serializers.FloatField(read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "tier",
            "description",
            "price_monthly_dollars",
            "price_yearly_dollars",
            "max_members",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model."""

    plan = PlanSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "status",
            "billing_interval",
            "is_active",
            "current_period_start",
            "current_period_end",
            "cancelled_at",
            "created_at",
        ]


class SubscriptionCreateSerializer(serializers.Serializer):
    """Serializer for creating/changing subscription."""

    plan_id = serializers.UUIDField()
    billing_interval = serializers.ChoiceField(
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
    )


class CheckoutSessionSerializer(serializers.Serializer):
    """Serializer for creating Stripe checkout session."""

    plan_id = serializers.UUIDField()
    billing_interval = serializers.ChoiceField(
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
    )
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()


class PortalSessionSerializer(serializers.Serializer):
    """Serializer for creating Stripe portal session."""

    return_url = serializers.URLField()


class UsageRecordSerializer(serializers.ModelSerializer):
    """Serializer for UsageRecord model."""

    class Meta:
        model = UsageRecord
        fields = [
            "id",
            "metric",
            "quantity",
            "period_start",
            "period_end",
            "created_at",
        ]


class BillingOverviewSerializer(serializers.Serializer):
    """Serializer for billing overview response."""

    subscription = SubscriptionSerializer(allow_null=True)
    current_plan = PlanSerializer(allow_null=True)
    usage = UsageRecordSerializer(many=True)
    upcoming_invoice_amount = serializers.IntegerField(allow_null=True)
