"""Base Django settings for arch-modular-saas-django project.

This module contains settings shared across all environments.
Environment-specific settings should go in development.py, production.py, or testing.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Django
    SECRET_KEY: str = "django-insecure-change-me-in-production"
    DEBUG: bool = False
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

    # Database
    DATABASE_URL: str = "postgres://saas:saas@localhost:5432/saas"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OAuth (optional - graceful degradation)
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None

    # Stripe (optional - graceful degradation)
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    # Email (graceful degradation: resend -> smtp -> console)
    RESEND_API_KEY: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 1025
    EMAIL_FROM: str = "noreply@example.com"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "saas-storage"
    MINIO_USE_SSL: bool = False


env = AppSettings()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = env.SECRET_KEY
DEBUG = env.DEBUG
ALLOWED_HOSTS = env.ALLOWED_HOSTS

# Application definition
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "corsheaders",
    "django_filters",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "storages",
    "drf_spectacular",
    # Local apps (modules)
    "apps.shared",
    "apps.tenants",
    "apps.authentication",
    "apps.members",
    "apps.billing",
    "apps.features",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "apps.shared.middleware.TenantContextMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES: dict[str, Any] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "saas",
        "USER": "saas",
        "PASSWORD": "saas",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# Try to parse DATABASE_URL if dj-database-url is available
try:
    import dj_database_url

    DATABASES["default"] = dj_database_url.parse(
        env.DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
except ImportError:
    pass

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.REDIS_URL,
    }
}

# Session
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Custom user model
AUTH_USER_MODEL = "authentication.User"

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Sites framework (required by allauth)
SITE_ID = 1

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.shared.exception_handler.custom_exception_handler",
}

# DRF Spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    "TITLE": "SaaS Backend API",
    "DESCRIPTION": "Multi-tenant SaaS Backend API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "auth", "description": "Authentication (login, logout, password)"},
        {"name": "registration", "description": "User registration"},
        {"name": "users", "description": "User profile and sessions"},
        {"name": "tenants", "description": "Tenant (workspace) management"},
        {"name": "members", "description": "Team members and invitations"},
        {"name": "billing", "description": "Plans, subscriptions, usage"},
        {"name": "features", "description": "Feature flags management"},
        {"name": "health", "description": "Health checks"},
    ],
}

# CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Allauth (v0.63+ settings)
ACCOUNT_LOGIN_METHODS = {"email"}  # Login by email only
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]  # Required signup fields
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = "optional"  # "mandatory", "optional", or "none"
SOCIALACCOUNT_AUTO_SIGNUP = True

# OAuth providers configuration (graceful degradation)
SOCIALACCOUNT_PROVIDERS: dict[str, Any] = {}

if env.GOOGLE_CLIENT_ID and env.GOOGLE_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS["google"] = {
        "APP": {
            "client_id": env.GOOGLE_CLIENT_ID,
            "secret": env.GOOGLE_CLIENT_SECRET,
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }

if env.GITHUB_CLIENT_ID and env.GITHUB_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS["github"] = {
        "APP": {
            "client_id": env.GITHUB_CLIENT_ID,
            "secret": env.GITHUB_CLIENT_SECRET,
        },
        "SCOPE": ["user:email"],
    }


# Email configuration (graceful degradation)
def _get_email_backend() -> str:
    """Determine email backend based on available configuration."""
    if env.RESEND_API_KEY:
        return "apps.shared.email.ResendEmailBackend"
    if env.SMTP_HOST:
        return "django.core.mail.backends.smtp.EmailBackend"
    return "django.core.mail.backends.console.EmailBackend"


EMAIL_BACKEND = _get_email_backend()
EMAIL_HOST = env.SMTP_HOST or "localhost"
EMAIL_PORT = env.SMTP_PORT
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = env.EMAIL_FROM

# Stripe (dj-stripe)
if env.STRIPE_SECRET_KEY:
    STRIPE_LIVE_SECRET_KEY = env.STRIPE_SECRET_KEY
    STRIPE_TEST_SECRET_KEY = env.STRIPE_SECRET_KEY
    STRIPE_LIVE_MODE = not env.STRIPE_SECRET_KEY.startswith("sk_test_")
    DJSTRIPE_WEBHOOK_SECRET = env.STRIPE_WEBHOOK_SECRET
    DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
    DJSTRIPE_USE_NATIVE_JSONFIELD = True

# Storage (MinIO / S3)
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_S3_ENDPOINT_URL = f"http{'s' if env.MINIO_USE_SSL else ''}://{env.MINIO_ENDPOINT}"
AWS_ACCESS_KEY_ID = env.MINIO_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = env.MINIO_SECRET_KEY
AWS_STORAGE_BUCKET_NAME = env.MINIO_BUCKET
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True

# Logging
LOG_LEVEL = env.LOG_LEVEL

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.utils.autoreload": {
            "handlers": ["console"],
            "level": "WARNING",  # Suppress autoreload spam
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",  # Suppress SQL query logs
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
