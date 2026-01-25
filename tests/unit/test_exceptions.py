"""Unit tests for shared exceptions module."""

from __future__ import annotations

from apps.shared.exceptions import (
    AppError,
    ConflictError,
    LimitExceededError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


class TestAppError:
    """Tests for base AppError."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = AppError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.code == "APP_ERROR"

    def test_error_with_code(self):
        """Test error with custom code."""
        error = AppError("Something went wrong", code="CUSTOM_ERROR")
        assert error.code == "CUSTOM_ERROR"


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_without_identifier(self):
        """Test error without identifier."""
        error = NotFoundError("User")
        assert "User not found" in str(error)
        assert error.code == "NOT_FOUND"

    def test_with_identifier(self):
        """Test error with identifier."""
        error = NotFoundError("User", "123")
        assert "User with id '123' not found" in str(error)


class TestPermissionDeniedError:
    """Tests for PermissionDeniedError."""

    def test_without_action(self):
        """Test generic permission denied."""
        error = PermissionDeniedError()
        assert str(error) == "Permission denied"
        assert error.code == "PERMISSION_DENIED"

    def test_with_action(self):
        """Test permission denied with specific action."""
        error = PermissionDeniedError("delete this resource")
        assert "cannot delete this resource" in str(error)


class TestValidationError:
    """Tests for ValidationError."""

    def test_without_field(self):
        """Test validation error without field."""
        error = ValidationError("Invalid value")
        assert str(error) == "Invalid value"
        assert error.code == "VALIDATION_ERROR"

    def test_with_field(self):
        """Test validation error with field."""
        error = ValidationError("must be positive", field="amount")
        assert "amount: must be positive" in str(error)


class TestConflictError:
    """Tests for ConflictError."""

    def test_conflict(self):
        """Test conflict error."""
        error = ConflictError("Resource already exists")
        assert str(error) == "Resource already exists"
        assert error.code == "CONFLICT"


class TestLimitExceededError:
    """Tests for LimitExceededError."""

    def test_limit_exceeded(self):
        """Test limit exceeded error."""
        error = LimitExceededError("members", 10)
        assert "members limit of 10 exceeded" in str(error)
        assert error.code == "LIMIT_EXCEEDED"
