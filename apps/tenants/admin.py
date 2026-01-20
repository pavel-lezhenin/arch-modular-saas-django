"""Django admin configuration for tenants."""

from __future__ import annotations

from django.contrib import admin

from apps.tenants.models import Tenant, TenantSettings


class TenantSettingsInline(admin.StackedInline):
    """Inline admin for tenant settings."""

    model = TenantSettings
    can_delete = False
    verbose_name_plural = "Settings"


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin interface for Tenant model."""

    list_display = ("name", "slug", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "slug")
    readonly_fields = ("id", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TenantSettingsInline]

    fieldsets = (
        (None, {"fields": ("id", "name", "slug", "status")}),
        (
            "Billing",
            {
                "fields": (
                    "stripe_customer_id",
                    "stripe_subscription_id",
                    "trial_ends_at",
                    "subscription_ends_at",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    """Admin interface for TenantSettings model."""

    list_display = ("tenant", "max_members", "require_2fa")
    list_filter = ("require_2fa", "allow_member_invites")
    search_fields = ("tenant__name",)
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("id", "tenant")}),
        ("Branding", {"fields": ("logo_url", "primary_color", "secondary_color")}),
        (
            "Features",
            {"fields": ("allow_member_invites", "max_members", "require_2fa")},
        ),
        (
            "Notifications",
            {"fields": ("email_notifications_enabled", "weekly_digest_enabled")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
