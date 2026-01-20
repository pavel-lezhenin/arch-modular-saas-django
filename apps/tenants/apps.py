"""Django app configuration for tenants."""
from __future__ import annotations

from django.apps import AppConfig


class TenantsConfig(AppConfig):
    """Configuration for the tenants app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tenants"
    verbose_name = "Tenants"

    def ready(self) -> None:
        """Initialize app when Django starts."""
        # Import signals to register handlers
        from apps.tenants import signals  # noqa: F401
