"""Django admin configuration for billing."""
from __future__ import annotations

from django.contrib import admin

from apps.billing.models import Plan, Subscription, UsageRecord


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Admin interface for Plan model."""

    list_display = (
        "name",
        "tier",
        "price_monthly_dollars",
        "max_members",
        "is_active",
        "is_public",
    )
    list_filter = ("tier", "is_active", "is_public")
    search_fields = ("name", "description")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("id", "name", "tier", "description")}),
        (
            "Pricing",
            {"fields": ("price_monthly", "price_yearly")},
        ),
        (
            "Stripe",
            {
                "fields": ("stripe_price_id_monthly", "stripe_price_id_yearly"),
                "classes": ("collapse",),
            },
        ),
        ("Limits", {"fields": ("max_members", "max_storage_gb")}),
        ("Status", {"fields": ("is_active", "is_public")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for Subscription model."""

    list_display = ("tenant", "plan", "status", "billing_interval", "current_period_end")
    list_filter = ("status", "billing_interval", "plan")
    search_fields = ("tenant__name", "stripe_subscription_id")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("tenant", "plan")

    fieldsets = (
        (None, {"fields": ("id", "tenant", "plan")}),
        ("Subscription Details", {"fields": ("status", "billing_interval")}),
        (
            "Period",
            {"fields": ("current_period_start", "current_period_end", "cancelled_at")},
        ),
        (
            "Stripe",
            {"fields": ("stripe_subscription_id",), "classes": ("collapse",)},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    """Admin interface for UsageRecord model."""

    list_display = ("tenant", "metric", "quantity", "period_start", "period_end")
    list_filter = ("metric",)
    search_fields = ("tenant__name",)
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("tenant",)

    fieldsets = (
        (None, {"fields": ("id", "tenant", "metric")}),
        ("Usage", {"fields": ("quantity", "period_start", "period_end")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
