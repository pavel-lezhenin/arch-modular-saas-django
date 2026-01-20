"""Django admin configuration for members."""
from __future__ import annotations

from django.contrib import admin

from apps.members.models import Invitation, Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin interface for Member model."""

    list_display = ("user", "tenant", "role", "is_active", "joined_at")
    list_filter = ("role", "is_active", "tenant")
    search_fields = ("user__email", "tenant__name", "job_title")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user", "tenant")

    fieldsets = (
        (None, {"fields": ("id", "tenant", "user", "role")}),
        ("Status", {"fields": ("is_active", "joined_at")}),
        ("Profile", {"fields": ("job_title", "department")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """Admin interface for Invitation model."""

    list_display = ("email", "tenant", "role", "status", "expires_at", "invited_by")
    list_filter = ("status", "role", "tenant")
    search_fields = ("email", "tenant__name")
    readonly_fields = ("id", "token", "created_at", "updated_at", "accepted_at")
    autocomplete_fields = ("tenant", "invited_by")

    fieldsets = (
        (None, {"fields": ("id", "tenant", "email", "role")}),
        ("Invitation Details", {"fields": ("token", "status", "expires_at")}),
        ("Tracking", {"fields": ("invited_by", "accepted_at", "accepted_by")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
