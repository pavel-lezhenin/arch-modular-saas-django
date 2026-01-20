"""Django admin configuration for features."""

from __future__ import annotations

from django.contrib import admin

from apps.features.models import Feature, TenantFeature


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    """Admin interface for Feature model."""

    list_display = ("code", "name", "is_active", "enabled_by_default", "requires_plan_tier")
    list_filter = ("is_active", "enabled_by_default", "requires_plan_tier")
    search_fields = ("code", "name", "description")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("id", "code", "name", "description")}),
        ("Behavior", {"fields": ("is_active", "enabled_by_default", "requires_plan_tier")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(TenantFeature)
class TenantFeatureAdmin(admin.ModelAdmin):
    """Admin interface for TenantFeature model."""

    list_display = ("tenant", "feature", "is_enabled")
    list_filter = ("is_enabled", "feature")
    search_fields = ("tenant__name", "feature__code")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("tenant", "feature")

    fieldsets = (
        (None, {"fields": ("id", "tenant", "feature", "is_enabled")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
