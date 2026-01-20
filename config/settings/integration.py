"""Integration testing settings - uses real PostgreSQL via testcontainers.

These settings are used for true integration tests that:
- Run against real PostgreSQL (not SQLite)
- Can test database-specific features (JSON fields, full-text search, etc.)
- Verify that migrations work correctly
- Test multi-database queries and transactions

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.integration pytest tests/integration -v
"""

from __future__ import annotations

import os

from .base import *  # noqa: F401, F403

DEBUG = False

# Database settings for testcontainers
# These are overridden by conftest.py fixtures when using testcontainers
DATABASES = {  # noqa: F405
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "test_saas_db"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# Use local memory cache for tests (Redis optional)
# Set REDIS_URL env var to test with real Redis
REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    CACHES = {  # noqa: F405
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {  # noqa: F405
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Email - use in-memory backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Storage - use local filesystem for tests
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# Logging - minimal for tests
LOGGING = {  # noqa: F405
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": os.environ.get("SQL_LOG_LEVEL", "WARNING"),
            "propagate": False,
        },
    },
}
