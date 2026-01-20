"""Development settings."""

from __future__ import annotations

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]  # noqa: S104

# CORS - allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Email - use console backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Logging - more verbose in development
LOGGING["root"]["level"] = "DEBUG"  # type: ignore[index]  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # type: ignore[index]  # noqa: F405
