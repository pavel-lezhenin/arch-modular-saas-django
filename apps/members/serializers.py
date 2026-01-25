"""Serializers for members module."""

from __future__ import annotations

from rest_framework import serializers

from apps.authentication.serializers import UserSerializer
from apps.members.models import Invitation, Member
from apps.shared.roles import Role


class MemberSerializer(serializers.ModelSerializer):
    """Serializer for Member model."""

    user = UserSerializer(read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Member
        fields = [
            "id",
            "user",
            "role",
            "role_display",
            "is_active",
            "joined_at",
            "job_title",
            "department",
            "created_at",
        ]
        read_only_fields = ["id", "user", "joined_at", "created_at"]


class MemberCreateSerializer(serializers.Serializer):
    """Serializer for creating a member (via invitation or directly)."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[(r.value, r.name.title()) for r in Role],
        default=Role.MEMBER.value,
    )


class MemberUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating member details."""

    class Meta:
        model = Member
        fields = ["role", "job_title", "department", "is_active"]


class InvitationSerializer(serializers.ModelSerializer):
    """Serializer for Invitation model."""

    invited_by_email = serializers.EmailField(source="invited_by.email", read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invitation
        fields = [
            "id",
            "email",
            "role",
            "status",
            "token",
            "expires_at",
            "invited_by_email",
            "is_valid",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "token",
            "status",
            "expires_at",
            "invited_by_email",
            "created_at",
        ]


class InvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an invitation."""

    class Meta:
        model = Invitation
        fields = ["email", "role"]

    def validate_role(self, value: str) -> str:
        """Validate that user can invite for this role.

        Args:
            value: The role value to validate.

        Returns:
            Validated role.

        Raises:
            ValidationError: If user can't invite for this role.
        """
        # Only owners can invite admins/owners
        inviter_role = self.context.get("inviter_role")

        if (
            inviter_role
            and value in (Role.OWNER.value, Role.ADMIN.value)
            and inviter_role != Role.OWNER.value
        ):
            msg = "Only owners can invite admins or owners"
            raise serializers.ValidationError(msg)

        return value


class InvitationAcceptSerializer(serializers.Serializer):
    """Serializer for accepting an invitation."""

    token = serializers.CharField()


class InvitationPublicSerializer(serializers.ModelSerializer):
    """Public serializer for invitation details (used when accepting)."""

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    invited_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = [
            "email",
            "role",
            "tenant_name",
            "invited_by_name",
            "is_valid",
            "expires_at",
        ]

    def get_invited_by_name(self, obj: Invitation) -> str:
        """Get the name of who sent the invitation."""
        if obj.invited_by:
            return obj.invited_by.full_name
        return "Unknown"
