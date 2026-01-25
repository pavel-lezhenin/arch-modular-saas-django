"""Django admin configuration for authentication."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.authentication.models import User, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""

    list_display = ("email", "full_name", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser", "is_verified")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name", "avatar_url")}),
        (
            "Status",
            {"fields": ("is_active", "is_verified", "is_staff", "is_superuser")},
        ),
        ("Permissions", {"fields": ("groups", "user_permissions"), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("date_joined", "last_login"), "classes": ("collapse",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin interface for UserSession model."""

    list_display = ("user", "ip_address", "device_type", "is_active", "last_activity")
    list_filter = ("is_active", "device_type")
    search_fields = ("user__email", "ip_address")
    readonly_fields = ("id", "session_key", "created_at", "last_activity")

    fieldsets = (
        (None, {"fields": ("id", "user", "session_key")}),
        ("Location", {"fields": ("ip_address", "user_agent", "device_type")}),
        ("Status", {"fields": ("is_active", "expires_at")}),
        ("Timestamps", {"fields": ("created_at", "last_activity"), "classes": ("collapse",)}),
    )
