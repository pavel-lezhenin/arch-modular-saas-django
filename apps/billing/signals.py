"""Django signals for billing module."""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.billing.models import Subscription

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Subscription)
def subscription_post_save(
    sender,  # noqa: ANN001, ARG001
    instance: Subscription,
    created: bool,
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Handle subscription creation/update events.

    Args:
        sender: The model class (Subscription).
        instance: The actual Subscription instance.
        created: True if this is a new record.
        **kwargs: Additional signal arguments.
    """
    if created:
        logger.info(
            "Signal: Subscription created for %s - plan: %s",
            instance.tenant.slug,
            instance.plan.name,
        )
    else:
        logger.info(
            "Signal: Subscription updated for %s - status: %s",
            instance.tenant.slug,
            instance.status,
        )

        # Could trigger notifications or other actions based on status changes
        # e.g., send email when subscription is past_due
