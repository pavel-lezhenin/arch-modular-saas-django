"""Django app configuration for billing."""

from __future__ import annotations

from django.apps import AppConfig


class BillingConfig(AppConfig):
    """Configuration for the billing app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"
    verbose_name = "Billing"

    def ready(self) -> None:
        """Initialize app when Django starts."""
        # Import signals to register handlers
        from apps.billing import signals  # noqa: F401
