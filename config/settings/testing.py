"""Testing settings."""

from __future__ import annotations

from .base import *  # noqa: F401, F403

DEBUG = False

# Use SQLite for faster tests
# pytest-django will automatically create a test database
DATABASES = {  # noqa: F405
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",  # noqa: F405
    }
}

# Use local memory cache for tests
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

# Disable logging during tests
LOGGING = {  # noqa: F405
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}
