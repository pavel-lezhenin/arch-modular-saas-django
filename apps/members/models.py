"""Member and Invitation models."""
from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.shared.models import BaseModel
from apps.shared.roles import Role


class Member(BaseModel):
    """Membership linking a user to a tenant with a specific role.

    This is the core entity that connects users to tenants and defines
    what they can do within that tenant.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=[(r.value, r.name.title()) for r in Role],
        default=Role.MEMBER.value,
    )

    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(default=timezone.now)

    # Optional metadata
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Member"
        verbose_name_plural = "Members"
        unique_together = [("tenant", "user")]
        ordering = ["-joined_at"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.user.email} @ {self.tenant.name} ({self.role})"

    @property
    def role_enum(self) -> Role:
        """Get role as enum."""
        return Role(self.role)


class InvitationStatus(models.TextChoices):
    """Invitation lifecycle status."""

    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"


def generate_invite_token() -> str:
    """Generate a secure random invitation token."""
    return secrets.token_urlsafe(32)


def default_expires_at():  # noqa: ANN201
    """Calculate default invitation expiration (7 days)."""
    return timezone.now() + timedelta(days=7)


class Invitation(BaseModel):
    """Invitation to join a tenant.

    Allows existing members to invite new users by email.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=20,
        choices=[(r.value, r.name.title()) for r in Role],
        default=Role.MEMBER.value,
    )

    # Invitation flow
    token = models.CharField(max_length=64, unique=True, default=generate_invite_token)
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )
    expires_at = models.DateTimeField(default=default_expires_at)

    # Tracking
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_invitations",
    )

    class Meta:
        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"Invite {self.email} to {self.tenant.name}"

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return (
            self.status == InvitationStatus.PENDING and timezone.now() > self.expires_at
        )

    @property
    def is_valid(self) -> bool:
        """Check if invitation can still be accepted."""
        return self.status == InvitationStatus.PENDING and not self.is_expired
