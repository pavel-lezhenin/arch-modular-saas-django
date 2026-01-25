"""Graceful email backend with fallback support."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


class GracefulEmailBackend(BaseEmailBackend):
    """Email backend with graceful degradation.

    Tries Resend API first, falls back to SMTP, then to console output.
    This allows the application to work without email configuration
    while still being ready for production email setup.
    """

    def __init__(self, fail_silently: bool = False, **kwargs) -> None:  # noqa: ANN003
        """Initialize the backend.

        Args:
            fail_silently: If True, suppress all exceptions.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(fail_silently=fail_silently, **kwargs)
        self._active_backend: BaseEmailBackend | None = None

    def _get_backend(self) -> BaseEmailBackend:
        """Get the appropriate email backend based on configuration.

        Returns:
            Configured email backend instance.
        """
        if self._active_backend is not None:
            return self._active_backend

        # Try Resend if API key is configured
        resend_api_key = getattr(settings, "RESEND_API_KEY", None)
        if resend_api_key:
            try:
                self._active_backend = ResendEmailBackend(
                    api_key=resend_api_key,
                    fail_silently=self.fail_silently,
                )
                logger.info("Using Resend email backend")
                return self._active_backend
            except ImportError:
                logger.warning("Resend package not installed, falling back to SMTP")

        # Try SMTP if host is configured
        smtp_host = getattr(settings, "EMAIL_HOST", None)
        if smtp_host:
            self._active_backend = SMTPEmailBackend(
                host=smtp_host,
                port=getattr(settings, "EMAIL_PORT", 587),
                username=getattr(settings, "EMAIL_HOST_USER", ""),
                password=getattr(settings, "EMAIL_HOST_PASSWORD", ""),
                use_tls=getattr(settings, "EMAIL_USE_TLS", True),
                use_ssl=getattr(settings, "EMAIL_USE_SSL", False),
                fail_silently=self.fail_silently,
            )
            logger.info("Using SMTP email backend: %s:%s", smtp_host, settings.EMAIL_PORT)
            return self._active_backend

        # Fall back to console
        self._active_backend = ConsoleEmailBackend(fail_silently=self.fail_silently)
        logger.info("Using console email backend (emails will be printed to stdout)")
        return self._active_backend

    def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        """Send one or more EmailMessage objects.

        Args:
            email_messages: List of email messages to send.

        Returns:
            Number of messages sent successfully.
        """
        backend = self._get_backend()
        return backend.send_messages(email_messages)

    def open(self) -> bool | None:
        """Open connection to the mail server.

        Returns:
            True if a new connection was opened, None if reusing existing.
        """
        backend = self._get_backend()
        return backend.open()

    def close(self) -> None:
        """Close connection to the mail server."""
        if self._active_backend is not None:
            self._active_backend.close()


class ResendEmailBackend(BaseEmailBackend):
    """Email backend using Resend API.

    Requires the 'resend' package to be installed:
        uv add resend
    """

    def __init__(
        self,
        api_key: str,
        fail_silently: bool = False,
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Initialize Resend backend.

        Args:
            api_key: Resend API key.
            fail_silently: If True, suppress all exceptions.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = api_key
        self._client: Any = None  # resend module

    def _get_client(self) -> Any:  # Returns resend module
        """Get or create Resend client.

        Returns:
            Resend client instance.
        """
        if self._client is None:
            import resend

            resend.api_key = self.api_key
            self._client = resend
        return self._client

    def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        """Send messages via Resend API.

        Args:
            email_messages: List of email messages to send.

        Returns:
            Number of messages sent successfully.
        """
        if not email_messages:
            return 0

        sent_count = 0
        client = self._get_client()

        for message in email_messages:
            try:
                params = {
                    "from_": message.from_email or settings.DEFAULT_FROM_EMAIL,
                    "to": list(message.to),
                    "subject": message.subject,
                }

                # Handle HTML and plain text content
                if hasattr(message, "alternatives") and message.alternatives:
                    # EmailMultiAlternatives with HTML
                    for content, mimetype in message.alternatives:
                        if mimetype == "text/html":
                            params["html"] = content
                            break
                    params["text"] = message.body
                else:
                    params["text"] = message.body

                if message.cc:
                    params["cc"] = list(message.cc)
                if message.bcc:
                    params["bcc"] = list(message.bcc)
                if message.reply_to:
                    params["reply_to"] = message.reply_to[0]

                client.Emails.send(params)
                sent_count += 1
                logger.debug("Sent email to %s via Resend", message.to)

            except Exception:
                logger.exception("Failed to send email to %s via Resend", message.to)
                if not self.fail_silently:
                    raise

        return sent_count
