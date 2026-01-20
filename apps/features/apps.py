"""Django app configuration for features."""
from __future__ import annotations

from django.apps import AppConfig


class FeaturesConfig(AppConfig):
    """Configuration for the features app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.features"
    verbose_name = "Features"

    def ready(self) -> None:
        """Initialize app when Django starts."""
        # Import signals to register handlers
        from apps.features import signals  # noqa: F401
