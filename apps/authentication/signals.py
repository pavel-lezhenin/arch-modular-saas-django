"""Django signals for authentication module."""

from __future__ import annotations

import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from apps.authentication.services import SessionService

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def on_user_logged_in(
    sender,  # noqa: ANN001, ARG001
    request,  # noqa: ANN001
    user,  # noqa: ANN001
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Handle user login event.

    Creates a session record for tracking.

    Args:
        sender: The class that sent the signal.
        request: The current HTTP request.
        user: The user who logged in.
        **kwargs: Additional signal arguments.
    """
    if request and hasattr(request, "session"):
        # Get client info
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        SessionService.create_session(
            user=user,
            session_key=request.session.session_key,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info("User logged in: %s from %s", user.email, ip_address)


@receiver(user_logged_out)
def on_user_logged_out(
    sender,  # noqa: ANN001, ARG001
    request,  # noqa: ANN001
    user,  # noqa: ANN001
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Handle user logout event.

    Marks the session as inactive.

    Args:
        sender: The class that sent the signal.
        request: The current HTTP request.
        user: The user who logged out.
        **kwargs: Additional signal arguments.
    """
    if request and hasattr(request, "session") and user:
        from apps.authentication.models import UserSession

        UserSession.objects.filter(
            user=user,
            session_key=request.session.session_key,
        ).update(is_active=False)

        logger.info("User logged out: %s", user.email)


def get_client_ip(request) -> str | None:  # noqa: ANN001
    """Extract client IP from request.

    Handles both direct connections and proxied requests.

    Args:
        request: Django HTTP request.

    Returns:
        Client IP address or None.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
