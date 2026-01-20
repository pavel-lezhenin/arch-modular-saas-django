"""Base exceptions for the application."""
from __future__ import annotations


class AppError(Exception):
    """Base exception for application errors."""

    def __init__(self, message: str, code: str | None = None) -> None:
        """Initialize exception.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code.
        """
        self.message = message
        self.code = code or "APP_ERROR"
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str | None = None) -> None:
        """Initialize exception.

        Args:
            resource: Name of the resource that was not found.
            identifier: Optional identifier that was searched for.
        """
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(message, "NOT_FOUND")


class PermissionDeniedError(AppError):
    """User does not have required permission."""

    def __init__(self, action: str | None = None) -> None:
        """Initialize exception.

        Args:
            action: The action that was denied.
        """
        message = "Permission denied"
        if action:
            message = f"Permission denied: cannot {action}"
        super().__init__(message, "PERMISSION_DENIED")


class ValidationError(AppError):
    """Validation error."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize exception.

        Args:
            message: Description of validation error.
            field: Field that failed validation.
        """
        if field:
            message = f"{field}: {message}"
        super().__init__(message, "VALIDATION_ERROR")


class ConflictError(AppError):
    """Resource conflict (e.g., duplicate)."""

    def __init__(self, message: str) -> None:
        """Initialize exception.

        Args:
            message: Description of the conflict.
        """
        super().__init__(message, "CONFLICT")


class LimitExceededError(AppError):
    """Resource limit exceeded."""

    def __init__(self, resource: str, limit: int) -> None:
        """Initialize exception.

        Args:
            resource: Name of the limited resource.
            limit: The limit that was exceeded.
        """
        message = f"{resource} limit of {limit} exceeded"
        super().__init__(message, "LIMIT_EXCEEDED")
