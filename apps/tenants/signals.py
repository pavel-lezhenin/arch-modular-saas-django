"""Django signals for tenants module.

This module demonstrates inter-module communication via signals.
When a tenant is created/modified, other modules can react accordingly.
"""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.tenants.models import Tenant, TenantSettings

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Tenant)
def tenant_post_save(
    sender,  # noqa: ANN001, ARG001
    instance: Tenant,
    created: bool,
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Handle tenant creation/update events.

    This signal can trigger actions in other modules:
    - Create initial admin member
    - Set up default features
    - Initialize billing

    Args:
        sender: The model class (Tenant).
        instance: The actual Tenant instance.
        created: True if this is a new record.
        **kwargs: Additional signal arguments.
    """
    if created:
        logger.info("Signal: Tenant created - %s", instance.slug)
        # Other modules can listen to this signal or we can emit custom events
        # Example: Create owner membership, initialize feature flags, etc.


@receiver(post_save, sender=TenantSettings)
def tenant_settings_post_save(
    sender,  # noqa: ANN001, ARG001
    instance: TenantSettings,
    created: bool,  # noqa: ARG001
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Handle tenant settings changes.

    Args:
        sender: The model class (TenantSettings).
        instance: The actual TenantSettings instance.
        created: True if this is a new record.
        **kwargs: Additional signal arguments.
    """
    logger.debug("Signal: TenantSettings updated for %s", instance.tenant.slug)
