"""Custom User model and related models."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from django.db.models import Manager


class UserManager(BaseUserManager):
    """Custom manager for User model."""

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,  # noqa: ANN003
    ) -> User:
        """Create and save a regular user.

        Args:
            email: User's email address.
            password: User's password (optional for OAuth).
            **extra_fields: Additional user fields.

        Returns:
            Created User instance.
        """
        if not email:
            msg = "Email is required"
            raise ValueError(msg)

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        **extra_fields,  # noqa: ANN003
    ) -> User:
        """Create and save a superuser.

        Args:
            email: User's email address.
            password: User's password.
            **extra_fields: Additional user fields.

        Returns:
            Created superuser instance.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            msg = "Superuser must have is_staff=True"
            raise ValueError(msg)
        if extra_fields.get("is_superuser") is not True:
            msg = "Superuser must have is_superuser=True"
            raise ValueError(msg)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model using email as username.

    This model stores user identity only - no tenant association here.
    A user can be a member of multiple tenants (see members app).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)

    # Profile info
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar_url = models.URLField(blank=True, null=True)

    # Status flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    # Type hints for related managers
    memberships: Manager

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        """Return string representation."""
        return self.email

    @property
    def full_name(self) -> str:
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.email


class UserSession(models.Model):
    """Track user sessions for security and analytics.

    This allows:
    - See all active sessions
    - Revoke sessions remotely
    - Track login history
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    session_key = models.CharField(max_length=40, unique=True)

    # Session metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # mobile, desktop, tablet

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        ordering = ["-last_activity"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"Session for {self.user.email}"

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return timezone.now() > self.expires_at
