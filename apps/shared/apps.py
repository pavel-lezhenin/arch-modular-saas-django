"""Shared app configuration."""
from __future__ import annotations

from django.apps import AppConfig


class SharedConfig(AppConfig):
    """Configuration for the shared app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.shared"
    verbose_name = "Shared"
