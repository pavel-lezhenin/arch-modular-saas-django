"""Business logic services for tenants module."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.shared.exceptions import ConflictError, NotFoundError
from apps.tenants.models import Tenant, TenantSettings, TenantStatus

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)


class TenantService:
    """Service for tenant business operations."""

    @staticmethod
    @transaction.atomic
    def create_tenant(name: str, slug: str) -> Tenant:
        """Create a new tenant with default settings.

        Args:
            name: Display name for the tenant.
            slug: URL-safe identifier for the tenant.

        Returns:
            Created Tenant instance.

        Raises:
            ConflictError: If slug already exists.
        """
        if Tenant.objects.filter(slug=slug).exists():
            msg = f"Tenant with slug '{slug}' already exists"
            raise ConflictError(msg)

        # Calculate trial end date
        trial_days = getattr(settings, "TENANT_TRIAL_DAYS", 14)
        trial_ends_at = timezone.now() + timedelta(days=trial_days)

        tenant = Tenant.objects.create(
            name=name,
            slug=slug,
            status=TenantStatus.TRIAL,
            trial_ends_at=trial_ends_at,
        )

        # Create default settings
        TenantSettings.objects.create(tenant=tenant)

        logger.info("Created tenant: %s (slug=%s)", tenant.name, tenant.slug)
        return tenant

    @staticmethod
    def get_tenant(tenant_id: UUID) -> Tenant:
        """Get tenant by ID.

        Args:
            tenant_id: UUID of the tenant.

        Returns:
            Tenant instance.

        Raises:
            NotFoundError: If tenant not found.
        """
        try:
            return Tenant.objects.select_related("settings").get(id=tenant_id)
        except Tenant.DoesNotExist:
            msg = "Tenant"
            raise NotFoundError(msg, str(tenant_id)) from None

    @staticmethod
    def get_tenant_by_slug(slug: str) -> Tenant:
        """Get tenant by slug.

        Args:
            slug: URL-safe tenant identifier.

        Returns:
            Tenant instance.

        Raises:
            NotFoundError: If tenant not found.
        """
        try:
            return Tenant.objects.select_related("settings").get(slug=slug)
        except Tenant.DoesNotExist:
            msg = "Tenant"
            raise NotFoundError(msg, slug) from None

    @staticmethod
    @transaction.atomic
    def update_tenant(tenant_id: UUID, *, name: str | None = None) -> Tenant:
        """Update tenant details.

        Args:
            tenant_id: UUID of the tenant to update.
            name: New display name (optional).

        Returns:
            Updated Tenant instance.

        Raises:
            NotFoundError: If tenant not found.
        """
        tenant = TenantService.get_tenant(tenant_id)

        if name is not None:
            tenant.name = name
            tenant.save(update_fields=["name", "updated_at"])
            logger.info("Updated tenant name: %s -> %s", tenant.slug, name)

        return tenant

    @staticmethod
    @transaction.atomic
    def update_status(tenant_id: UUID, status: TenantStatus) -> Tenant:
        """Update tenant status.

        Args:
            tenant_id: UUID of the tenant.
            status: New status value.

        Returns:
            Updated Tenant instance.

        Raises:
            NotFoundError: If tenant not found.
        """
        tenant = TenantService.get_tenant(tenant_id)
        old_status = tenant.status

        tenant.status = status
        tenant.save(update_fields=["status", "updated_at"])

        logger.info(
            "Tenant %s status changed: %s -> %s",
            tenant.slug,
            old_status,
            status,
        )
        return tenant

    @staticmethod
    @transaction.atomic
    def update_settings(
        tenant_id: UUID,
        **kwargs,  # noqa: ANN003
    ) -> TenantSettings:
        """Update tenant settings.

        Args:
            tenant_id: UUID of the tenant.
            **kwargs: Settings fields to update.

        Returns:
            Updated TenantSettings instance.

        Raises:
            NotFoundError: If tenant not found.
        """
        tenant = TenantService.get_tenant(tenant_id)

        settings_obj, _ = TenantSettings.objects.get_or_create(tenant=tenant)

        allowed_fields = {
            "logo_url",
            "primary_color",
            "secondary_color",
            "allow_member_invites",
            "require_2fa",
            "email_notifications_enabled",
            "weekly_digest_enabled",
        }

        update_fields = []
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(settings_obj, field, value)
                update_fields.append(field)

        if update_fields:
            update_fields.append("updated_at")
            settings_obj.save(update_fields=update_fields)
            logger.info("Updated settings for tenant %s: %s", tenant.slug, update_fields)

        return settings_obj

    @staticmethod
    def check_trial_expiration() -> list[Tenant]:
        """Find tenants with expired trials.

        Returns:
            List of tenants with expired trials still in trial status.
        """
        now = timezone.now()
        return list(
            Tenant.objects.filter(
                status=TenantStatus.TRIAL,
                trial_ends_at__lt=now,
            )
        )

    @staticmethod
    @transaction.atomic
    def suspend_expired_trials() -> int:
        """Suspend all tenants with expired trials.

        Returns:
            Number of tenants suspended.
        """
        expired = TenantService.check_trial_expiration()
        count = 0

        for tenant in expired:
            tenant.status = TenantStatus.SUSPENDED
            tenant.save(update_fields=["status", "updated_at"])
            count += 1
            logger.info("Suspended expired trial tenant: %s", tenant.slug)

        return count
