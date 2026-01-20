"""Business logic services for authentication module."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.authentication.models import User, UserSession
from apps.shared.exceptions import NotFoundError, PermissionDeniedError, ValidationError

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations."""

    @staticmethod
    @transaction.atomic
    def register_user(
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> User:
        """Register a new user.

        Args:
            email: User's email address.
            password: User's password.
            first_name: User's first name.
            last_name: User's last name.

        Returns:
            Created User instance.

        Raises:
            ValidationError: If email already exists.
        """
        if User.objects.filter(email=email).exists():
            msg = "User with this email already exists"
            raise ValidationError(msg, field="email")

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        logger.info("Registered new user: %s", user.email)
        return user

    @staticmethod
    def get_user(user_id: UUID) -> User:
        """Get user by ID.

        Args:
            user_id: UUID of the user.

        Returns:
            User instance.

        Raises:
            NotFoundError: If user not found.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            msg = "User"
            raise NotFoundError(msg, str(user_id)) from None

    @staticmethod
    def get_user_by_email(email: str) -> User:
        """Get user by email.

        Args:
            email: User's email address.

        Returns:
            User instance.

        Raises:
            NotFoundError: If user not found.
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            msg = "User"
            raise NotFoundError(msg, email) from None

    @staticmethod
    @transaction.atomic
    def update_profile(
        user_id: UUID,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """Update user profile.

        Args:
            user_id: UUID of the user.
            first_name: New first name (optional).
            last_name: New last name (optional).
            avatar_url: New avatar URL (optional).

        Returns:
            Updated User instance.
        """
        user = UserService.get_user(user_id)
        update_fields = []

        if first_name is not None:
            user.first_name = first_name
            update_fields.append("first_name")

        if last_name is not None:
            user.last_name = last_name
            update_fields.append("last_name")

        if avatar_url is not None:
            user.avatar_url = avatar_url
            update_fields.append("avatar_url")

        if update_fields:
            user.save(update_fields=update_fields)
            logger.info("Updated profile for user: %s", user.email)

        return user

    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> None:
        """Change user's password.

        Args:
            user: User instance.
            current_password: Current password for verification.
            new_password: New password to set.

        Raises:
            PermissionDeniedError: If current password is incorrect.
        """
        if not user.check_password(current_password):
            msg = "Incorrect current password"
            raise PermissionDeniedError(msg)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        logger.info("Password changed for user: %s", user.email)


class SessionService:
    """Service for session management."""

    @staticmethod
    def create_session(
        user: User,
        session_key: str,
        ip_address: str | None = None,
        user_agent: str = "",
    ) -> UserSession:
        """Create a new session record.

        Args:
            user: User instance.
            session_key: Django session key.
            ip_address: Client IP address.
            user_agent: Browser user agent string.

        Returns:
            Created UserSession instance.
        """
        # Parse device type from user agent (simplified)
        device_type = "desktop"
        user_agent_lower = user_agent.lower()
        if "mobile" in user_agent_lower or "android" in user_agent_lower:
            device_type = "mobile"
        elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
            device_type = "tablet"

        session_duration = getattr(settings, "SESSION_COOKIE_AGE", 1209600)  # 2 weeks
        expires_at = timezone.now() + timedelta(seconds=session_duration)

        session = UserSession.objects.create(
            user=user,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent[:500],  # Truncate long user agents
            device_type=device_type,
            expires_at=expires_at,
        )

        logger.info("Created session for user %s from %s", user.email, ip_address)
        return session

    @staticmethod
    def get_user_sessions(user: User, active_only: bool = True) -> list[UserSession]:
        """Get all sessions for a user.

        Args:
            user: User instance.
            active_only: If True, return only active sessions.

        Returns:
            List of UserSession instances.
        """
        qs = UserSession.objects.filter(user=user)
        if active_only:
            qs = qs.filter(is_active=True, expires_at__gt=timezone.now())
        return list(qs.order_by("-last_activity"))

    @staticmethod
    def revoke_session(session_id: UUID, user: User) -> None:
        """Revoke a specific session.

        Args:
            session_id: UUID of the session to revoke.
            user: User who owns the session (for verification).

        Raises:
            NotFoundError: If session not found.
            PermissionDeniedError: If session belongs to different user.
        """
        try:
            session = UserSession.objects.get(id=session_id)
        except UserSession.DoesNotExist:
            msg = "Session"
            raise NotFoundError(msg, str(session_id)) from None

        if session.user_id != user.id:
            msg = "revoke this session"
            raise PermissionDeniedError(msg)

        session.is_active = False
        session.save(update_fields=["is_active"])
        logger.info("Revoked session %s for user %s", session_id, user.email)

    @staticmethod
    def revoke_all_sessions(user: User, except_current: str | None = None) -> int:
        """Revoke all sessions for a user.

        Args:
            user: User instance.
            except_current: Session key to keep active (current session).

        Returns:
            Number of sessions revoked.
        """
        qs = UserSession.objects.filter(user=user, is_active=True)
        if except_current:
            qs = qs.exclude(session_key=except_current)

        count = qs.update(is_active=False)
        logger.info("Revoked %d sessions for user %s", count, user.email)
        return count

    @staticmethod
    def cleanup_expired_sessions() -> int:
        """Remove expired sessions from database.

        Returns:
            Number of sessions deleted.
        """
        count, _ = UserSession.objects.filter(expires_at__lt=timezone.now()).delete()
        if count > 0:
            logger.info("Cleaned up %d expired sessions", count)
        return count
