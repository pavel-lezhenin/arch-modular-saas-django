"""Business logic services for members module."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.members.models import Invitation, InvitationStatus, Member
from apps.shared.exceptions import (
    ConflictError,
    LimitExceededError,
    NotFoundError,
    ValidationError,
)
from apps.shared.roles import Role

if TYPE_CHECKING:
    from uuid import UUID

    from apps.authentication.models import User
    from apps.tenants.models import Tenant

logger = logging.getLogger(__name__)


class MemberService:
    """Service for member operations."""

    @staticmethod
    @transaction.atomic
    def add_member(
        tenant: Tenant,
        user: User,
        role: Role = Role.MEMBER,
        *,
        job_title: str = "",
        department: str = "",
    ) -> Member:
        """Add a user as a member to a tenant.

        Args:
            tenant: Tenant to add member to.
            user: User to add as member.
            role: Role for the member.
            job_title: Optional job title.
            department: Optional department.

        Returns:
            Created Member instance.

        Raises:
            ConflictError: If user is already a member.
            LimitExceededError: If tenant has reached member limit.
        """
        # Check if already a member
        if Member.objects.filter(tenant=tenant, user=user).exists():
            msg = f"User {user.email} is already a member of {tenant.name}"
            raise ConflictError(msg)

        # Check member limit
        current_count = Member.objects.filter(tenant=tenant, is_active=True).count()
        max_members = tenant.settings.max_members if hasattr(tenant, "settings") else 10

        if current_count >= max_members:
            msg = "members"
            raise LimitExceededError(msg, max_members)

        member = Member.objects.create(
            tenant=tenant,
            user=user,
            role=role.value,
            job_title=job_title,
            department=department,
        )

        logger.info(
            "Added member %s to tenant %s with role %s",
            user.email,
            tenant.slug,
            role.value,
        )
        return member

    @staticmethod
    def get_member(member_id: UUID) -> Member:
        """Get member by ID.

        Args:
            member_id: UUID of the member.

        Returns:
            Member instance.

        Raises:
            NotFoundError: If member not found.
        """
        try:
            return Member.objects.select_related("user", "tenant").get(id=member_id)
        except Member.DoesNotExist:
            msg = "Member"
            raise NotFoundError(msg, str(member_id)) from None

    @staticmethod
    def get_user_membership(tenant: Tenant, user: User) -> Member | None:
        """Get user's membership in a tenant.

        Args:
            tenant: Tenant to check.
            user: User to check.

        Returns:
            Member instance or None if not a member.
        """
        return Member.objects.filter(tenant=tenant, user=user).first()

    @staticmethod
    def get_tenant_members(tenant: Tenant, *, active_only: bool = True) -> list[Member]:
        """Get all members of a tenant.

        Args:
            tenant: Tenant to get members for.
            active_only: If True, return only active members.

        Returns:
            List of Member instances.
        """
        qs = Member.objects.filter(tenant=tenant).select_related("user")
        if active_only:
            qs = qs.filter(is_active=True)
        return list(qs.order_by("-joined_at"))

    @staticmethod
    def get_user_tenants(user: User, *, active_only: bool = True) -> list[Member]:
        """Get all tenants a user is a member of.

        Args:
            user: User to get memberships for.
            active_only: If True, return only active memberships.

        Returns:
            List of Member instances with tenant info.
        """
        qs = Member.objects.filter(user=user).select_related("tenant")
        if active_only:
            qs = qs.filter(is_active=True)
        return list(qs.order_by("-joined_at"))

    @staticmethod
    @transaction.atomic
    def update_member(
        member_id: UUID,
        *,
        role: Role | None = None,
        job_title: str | None = None,
        department: str | None = None,
        is_active: bool | None = None,
    ) -> Member:
        """Update member details.

        Args:
            member_id: UUID of the member to update.
            role: New role (optional).
            job_title: New job title (optional).
            department: New department (optional).
            is_active: New active status (optional).

        Returns:
            Updated Member instance.
        """
        member = MemberService.get_member(member_id)
        update_fields = []

        if role is not None:
            # Don't allow changing the last owner
            if member.role == Role.OWNER.value and role != Role.OWNER:
                owner_count = Member.objects.filter(
                    tenant=member.tenant, role=Role.OWNER.value, is_active=True
                ).count()
                if owner_count <= 1:
                    msg = "Cannot change role of the last owner"
                    raise ValidationError(msg)

            member.role = role.value
            update_fields.append("role")

        if job_title is not None:
            member.job_title = job_title
            update_fields.append("job_title")

        if department is not None:
            member.department = department
            update_fields.append("department")

        if is_active is not None:
            # Don't allow deactivating the last owner
            if member.role == Role.OWNER.value and not is_active:
                owner_count = Member.objects.filter(
                    tenant=member.tenant, role=Role.OWNER.value, is_active=True
                ).count()
                if owner_count <= 1:
                    msg = "Cannot deactivate the last owner"
                    raise ValidationError(msg)

            member.is_active = is_active
            update_fields.append("is_active")

        if update_fields:
            update_fields.append("updated_at")
            member.save(update_fields=update_fields)
            logger.info("Updated member %s: %s", member.id, update_fields)

        return member

    @staticmethod
    @transaction.atomic
    def remove_member(member_id: UUID) -> None:
        """Remove a member from tenant.

        Args:
            member_id: UUID of the member to remove.

        Raises:
            NotFoundError: If member not found.
            ValidationError: If trying to remove last owner.
        """
        member = MemberService.get_member(member_id)

        # Don't allow removing the last owner
        if member.role == Role.OWNER.value:
            owner_count = Member.objects.filter(
                tenant=member.tenant, role=Role.OWNER.value, is_active=True
            ).count()
            if owner_count <= 1:
                msg = "Cannot remove the last owner"
                raise ValidationError(msg)

        member.delete()
        logger.info("Removed member %s from tenant %s", member.user.email, member.tenant.slug)


class InvitationService:
    """Service for invitation operations."""

    @staticmethod
    @transaction.atomic
    def create_invitation(
        tenant: Tenant,
        email: str,
        role: Role,
        invited_by: User,
    ) -> Invitation:
        """Create an invitation to join a tenant.

        Args:
            tenant: Tenant to invite to.
            email: Email address to invite.
            role: Role to assign upon acceptance.
            invited_by: User creating the invitation.

        Returns:
            Created Invitation instance.

        Raises:
            ConflictError: If user is already a member or has pending invite.
            PermissionDeniedError: If inviter can't invite for this role.
        """
        from apps.authentication.models import User

        # Check if already a member
        existing_user = User.objects.filter(email=email).first()
        if existing_user and Member.objects.filter(tenant=tenant, user=existing_user).exists():
            msg = f"User {email} is already a member of {tenant.name}"
            raise ConflictError(msg)

        # Check for pending invitation
        pending = Invitation.objects.filter(
            tenant=tenant,
            email=email,
            status=InvitationStatus.PENDING,
        ).first()
        if pending and pending.is_valid:
            msg = f"Pending invitation already exists for {email}"
            raise ConflictError(msg)

        # Check member limit
        current_count = Member.objects.filter(tenant=tenant, is_active=True).count()
        pending_count = Invitation.objects.filter(
            tenant=tenant, status=InvitationStatus.PENDING
        ).count()
        max_members = tenant.settings.max_members if hasattr(tenant, "settings") else 10

        if current_count + pending_count >= max_members:
            msg = "members (including pending invitations)"
            raise LimitExceededError(msg, max_members)

        invitation = Invitation.objects.create(
            tenant=tenant,
            email=email,
            role=role.value,
            invited_by=invited_by,
        )

        # Send invitation email
        InvitationService._send_invitation_email(invitation)

        logger.info(
            "Created invitation for %s to join %s",
            email,
            tenant.slug,
        )
        return invitation

    @staticmethod
    def _send_invitation_email(invitation: Invitation) -> None:
        """Send invitation email.

        Args:
            invitation: Invitation to send email for.
        """
        try:
            # Build invitation URL
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            invite_url = f"{base_url}/invite/{invitation.token}"

            # Try to render template, fall back to simple message
            try:
                message = render_to_string(
                    "members/emails/invitation.txt",
                    {
                        "invitation": invitation,
                        "invite_url": invite_url,
                    },
                )
            except Exception:
                message = (
                    f"You've been invited to join {invitation.tenant.name}.\n\n"
                    f"Click here to accept: {invite_url}\n\n"
                    f"This invitation expires on {invitation.expires_at.strftime('%Y-%m-%d')}."
                )

            send_mail(
                subject=f"You've been invited to join {invitation.tenant.name}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                fail_silently=True,  # Don't fail if email doesn't work
            )
            logger.info("Sent invitation email to %s", invitation.email)
        except Exception:
            # Log but don't fail - email is best-effort
            logger.exception("Failed to send invitation email to %s", invitation.email)

    @staticmethod
    def get_invitation_by_token(token: str) -> Invitation:
        """Get invitation by token.

        Args:
            token: Invitation token.

        Returns:
            Invitation instance.

        Raises:
            NotFoundError: If invitation not found.
        """
        try:
            return Invitation.objects.select_related("tenant", "invited_by").get(token=token)
        except Invitation.DoesNotExist:
            msg = "Invitation"
            raise NotFoundError(msg, token) from None

    @staticmethod
    @transaction.atomic
    def accept_invitation(token: str, user: User) -> Member:
        """Accept an invitation and create membership.

        Args:
            token: Invitation token.
            user: User accepting the invitation.

        Returns:
            Created Member instance.

        Raises:
            NotFoundError: If invitation not found.
            ValidationError: If invitation is invalid or expired.
        """
        invitation = InvitationService.get_invitation_by_token(token)

        if not invitation.is_valid:
            if invitation.is_expired:
                msg = "This invitation has expired"
                raise ValidationError(msg)
            msg = f"This invitation is {invitation.status}"
            raise ValidationError(msg)

        # Create membership
        member = MemberService.add_member(
            tenant=invitation.tenant,
            user=user,
            role=Role(invitation.role),
        )

        # Update invitation status
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.accepted_by = user
        invitation.save(update_fields=["status", "accepted_at", "accepted_by", "updated_at"])

        logger.info(
            "User %s accepted invitation to %s",
            user.email,
            invitation.tenant.slug,
        )
        return member

    @staticmethod
    @transaction.atomic
    def revoke_invitation(invitation_id: UUID) -> Invitation:
        """Revoke a pending invitation.

        Args:
            invitation_id: UUID of the invitation.

        Returns:
            Updated Invitation instance.

        Raises:
            NotFoundError: If invitation not found.
            ValidationError: If invitation is not pending.
        """
        try:
            invitation = Invitation.objects.get(id=invitation_id)
        except Invitation.DoesNotExist:
            msg = "Invitation"
            raise NotFoundError(msg, str(invitation_id)) from None

        if invitation.status != InvitationStatus.PENDING:
            msg = f"Cannot revoke invitation with status {invitation.status}"
            raise ValidationError(msg)

        invitation.status = InvitationStatus.REVOKED
        invitation.save(update_fields=["status", "updated_at"])

        logger.info("Revoked invitation %s", invitation_id)
        return invitation

    @staticmethod
    def get_tenant_invitations(
        tenant: Tenant, *, pending_only: bool = True
    ) -> list[Invitation]:
        """Get all invitations for a tenant.

        Args:
            tenant: Tenant to get invitations for.
            pending_only: If True, return only pending invitations.

        Returns:
            List of Invitation instances.
        """
        qs = Invitation.objects.filter(tenant=tenant).select_related("invited_by")
        if pending_only:
            qs = qs.filter(status=InvitationStatus.PENDING)
        return list(qs.order_by("-created_at"))
