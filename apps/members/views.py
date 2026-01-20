"""API views for members module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.members.models import Invitation, Member
from apps.members.serializers import (
    InvitationCreateSerializer,
    InvitationPublicSerializer,
    InvitationSerializer,
    MemberSerializer,
    MemberUpdateSerializer,
)
from apps.members.services import InvitationService, MemberService
from apps.shared.middleware import get_current_tenant
from apps.shared.permissions import CanManageMembers, IsTenantMember
from apps.shared.roles import Role

if TYPE_CHECKING:
    from rest_framework.request import Request


class MemberViewSet(viewsets.ModelViewSet):
    """ViewSet for member CRUD operations within a tenant."""

    serializer_class = MemberSerializer

    def get_queryset(self):  # noqa: ANN201
        """Return members for current tenant."""
        tenant = get_current_tenant()
        if not tenant:
            return Member.objects.none()
        return Member.objects.filter(tenant=tenant).select_related("user")

    def get_serializer_class(self):  # noqa: ANN201
        """Return appropriate serializer based on action."""
        if self.action in ("update", "partial_update"):
            return MemberUpdateSerializer
        return MemberSerializer

    def get_permissions(self):  # noqa: ANN201
        """Return permissions based on action."""
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), IsTenantMember()]
        return [IsAuthenticated(), CanManageMembers()]

    def update(self, request: Request, *args, **kwargs) -> Response:  # noqa: ANN002, ANN003, ARG002
        """Update member details.

        Args:
            request: HTTP request with update data.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Updated member data.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Convert role string to enum if present
        role = None
        if "role" in serializer.validated_data:
            role = Role(serializer.validated_data.pop("role"))

        member = MemberService.update_member(
            member_id=instance.id,
            role=role,
            **serializer.validated_data,
        )

        output_serializer = MemberSerializer(member)
        return Response(output_serializer.data)

    def destroy(self, request: Request, *args, **kwargs) -> Response:  # noqa: ANN002, ANN003, ARG002
        """Remove a member.

        Args:
            request: HTTP request.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Empty response.
        """
        instance = self.get_object()
        MemberService.remove_member(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationViewSet(viewsets.ModelViewSet):
    """ViewSet for invitation operations within a tenant."""

    serializer_class = InvitationSerializer

    def get_queryset(self):  # noqa: ANN201
        """Return invitations for current tenant."""
        tenant = get_current_tenant()
        if not tenant:
            return Invitation.objects.none()
        return Invitation.objects.filter(tenant=tenant).select_related("invited_by")

    def get_serializer_class(self):  # noqa: ANN201
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return InvitationCreateSerializer
        return InvitationSerializer

    def get_permissions(self):  # noqa: ANN201
        """Return permissions based on action."""
        return [IsAuthenticated(), CanManageMembers()]

    def create(self, request: Request) -> Response:
        """Create a new invitation.

        Args:
            request: HTTP request with invitation data.

        Returns:
            Created invitation data.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get inviter's role for validation
        membership = MemberService.get_user_membership(tenant, request.user)
        inviter_role = membership.role if membership else None

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
                "inviter_role": inviter_role,
            },
        )
        serializer.is_valid(raise_exception=True)

        invitation = InvitationService.create_invitation(
            tenant=tenant,
            email=serializer.validated_data["email"],
            role=Role(serializer.validated_data["role"]),
            invited_by=request.user,
        )

        output_serializer = InvitationSerializer(invitation)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def revoke(self, request: Request, pk: str | None = None) -> Response:  # noqa: ARG002
        """Revoke a pending invitation.

        Args:
            request: HTTP request.
            pk: Invitation primary key.

        Returns:
            Updated invitation data.
        """
        instance = self.get_object()
        invitation = InvitationService.revoke_invitation(instance.id)

        serializer = InvitationSerializer(invitation)
        return Response(serializer.data)


class InvitationAcceptView(APIView):
    """Public endpoint for accepting invitations."""

    permission_classes = [AllowAny]

    def get(self, request: Request, token: str) -> Response:  # noqa: ARG002
        """Get invitation details by token.

        Args:
            request: HTTP request.
            token: Invitation token.

        Returns:
            Invitation details.
        """
        invitation = InvitationService.get_invitation_by_token(token)
        serializer = InvitationPublicSerializer(invitation)
        return Response(serializer.data)

    def post(self, request: Request, token: str) -> Response:
        """Accept an invitation.

        Args:
            request: HTTP request.
            token: Invitation token.

        Returns:
            Created membership data.
        """
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required to accept invitation"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        member = InvitationService.accept_invitation(token, request.user)
        serializer = MemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyMembershipsView(APIView):
    """View for listing current user's memberships."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Get all tenants user is a member of.

        Args:
            request: HTTP request.

        Returns:
            List of memberships with tenant info.
        """
        memberships = MemberService.get_user_tenants(request.user)

        # Include tenant info in response
        data = []
        for member in memberships:
            member_data = MemberSerializer(member).data
            member_data["tenant"] = {
                "id": str(member.tenant.id),
                "name": member.tenant.name,
                "slug": member.tenant.slug,
            }
            data.append(member_data)

        return Response(data)
