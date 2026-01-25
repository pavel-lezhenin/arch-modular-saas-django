"""Custom DRF exception handler for application errors."""

from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from apps.shared.exceptions import (
    AppError,
    ConflictError,
    LimitExceededError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """Handle application-specific exceptions.

    Converts AppError subclasses to appropriate HTTP responses.

    Args:
        exc: The exception that was raised.
        context: The context for the exception.

    Returns:
        Response object or None (for unhandled exceptions).
    """
    # Handle application-specific errors
    if isinstance(exc, NotFoundError):
        return Response(
            {"error": exc.code, "detail": str(exc)},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, PermissionDeniedError):
        return Response(
            {"error": exc.code, "detail": str(exc)},
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, ValidationError):
        return Response(
            {"error": exc.code, "detail": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, ConflictError):
        return Response(
            {"error": exc.code, "detail": str(exc)},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, LimitExceededError):
        return Response(
            {"error": exc.code, "detail": str(exc)},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    if isinstance(exc, AppError):
        return Response(
            {"error": exc.code, "detail": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Let DRF handle the rest
    return drf_exception_handler(exc, context)
