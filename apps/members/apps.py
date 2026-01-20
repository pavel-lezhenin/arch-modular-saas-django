"""Django app configuration for members."""
from __future__ import annotations

from django.apps import AppConfig


class MembersConfig(AppConfig):
    """Configuration for the members app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.members"
    verbose_name = "Members"

    def ready(self) -> None:
        """Initialize app when Django starts."""
        # Import signals to register handlers
        from apps.members import signals  # noqa: F401
