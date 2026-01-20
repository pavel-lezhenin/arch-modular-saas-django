"""Serializers for authentication module."""
from __future__ import annotations

from rest_framework import serializers

from apps.authentication.models import User, UserSession


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar_url",
            "is_active",
            "is_verified",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "email",
            "is_active",
            "is_verified",
            "date_joined",
            "last_login",
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar_url"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm", "first_name", "last_name"]

    def validate(self, attrs: dict) -> dict:
        """Validate passwords match.

        Args:
            attrs: Attribute dictionary.

        Returns:
            Validated attributes.

        Raises:
            ValidationError: If passwords don't match.
        """
        if attrs.get("password") != attrs.get("password_confirm"):
            msg = "Passwords do not match"
            raise serializers.ValidationError({"password_confirm": msg})
        return attrs

    def create(self, validated_data: dict) -> User:
        """Create new user.

        Args:
            validated_data: Validated user data.

        Returns:
            Created User instance.
        """
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        """Validate passwords.

        Args:
            attrs: Attribute dictionary.

        Returns:
            Validated attributes.

        Raises:
            ValidationError: If validation fails.
        """
        if attrs.get("new_password") != attrs.get("new_password_confirm"):
            msg = "New passwords do not match"
            raise serializers.ValidationError({"new_password_confirm": msg})
        return attrs


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for UserSession model."""

    is_expired = serializers.BooleanField(read_only=True)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            "id",
            "ip_address",
            "user_agent",
            "device_type",
            "is_active",
            "is_expired",
            "is_current",
            "created_at",
            "last_activity",
        ]

    def get_is_current(self, obj: UserSession) -> bool:
        """Check if this is the current session.

        Args:
            obj: UserSession instance.

        Returns:
            True if this is the requesting user's current session.
        """
        request = self.context.get("request")
        if request and hasattr(request, "session"):
            return obj.session_key == request.session.session_key
        return False
