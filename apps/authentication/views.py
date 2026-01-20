"""API views for authentication module."""
from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import User, UserSession
from apps.authentication.serializers import (
    PasswordChangeSerializer,
    UserProfileUpdateSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserSessionSerializer,
)
from apps.authentication.services import SessionService, UserService

if TYPE_CHECKING:
    from rest_framework.request import Request


class RegistrationView(APIView):
    """User registration endpoint."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Register a new user.

        Args:
            request: HTTP request with registration data.

        Returns:
            Created user data.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        output_serializer = UserSerializer(user)

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """Current user profile endpoint."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Get current user profile.

        Args:
            request: HTTP request.

        Returns:
            Current user data.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request: Request) -> Response:
        """Update current user profile.

        Args:
            request: HTTP request with profile data.

        Returns:
            Updated user data.
        """
        serializer = UserProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user = UserService.update_profile(
            user_id=request.user.id,
            **serializer.validated_data,
        )

        output_serializer = UserSerializer(user)
        return Response(output_serializer.data)


class PasswordChangeView(APIView):
    """Password change endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Change current user's password.

        Args:
            request: HTTP request with password data.

        Returns:
            Success message.
        """
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        UserService.change_password(
            user=request.user,
            current_password=serializer.validated_data["current_password"],
            new_password=serializer.validated_data["new_password"],
        )

        return Response({"detail": "Password changed successfully"})


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing and revoking sessions."""

    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # noqa: ANN201
        """Return sessions for current user."""
        return UserSession.objects.filter(user=self.request.user).order_by("-last_activity")

    @action(detail=True, methods=["post"])
    def revoke(self, request: Request, pk: str | None = None) -> Response:  # noqa: ARG002
        """Revoke a specific session.

        Args:
            request: HTTP request.
            pk: Session primary key.

        Returns:
            Success message.
        """
        session = self.get_object()
        SessionService.revoke_session(session.id, request.user)
        return Response({"detail": "Session revoked"})

    @action(detail=False, methods=["post"], url_path="revoke-all")
    def revoke_all(self, request: Request) -> Response:
        """Revoke all sessions except current.

        Args:
            request: HTTP request.

        Returns:
            Number of revoked sessions.
        """
        current_session_key = request.session.session_key if hasattr(request, "session") else None
        count = SessionService.revoke_all_sessions(
            request.user,
            except_current=current_session_key,
        )
        return Response({"detail": f"Revoked {count} sessions"})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing users (admin only)."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # noqa: ANN201
        """Filter users based on permissions."""
        if self.request.user.is_staff:
            return User.objects.all()
        # Regular users can only see themselves
        return User.objects.filter(id=self.request.user.id)
