"""Django signals for members module."""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.members.models import Invitation, Member

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Member)
def member_post_save(
    sender,  # noqa: ANN001, ARG001
    instance: Member,
    created: bool,
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Handle member creation/update events.

    Args:
        sender: The model class (Member).
        instance: The actual Member instance.
        created: True if this is a new record.
        **kwargs: Additional signal arguments.
    """
    if created:
        logger.info(
            "Signal: Member added - %s joined %s as %s",
            instance.user.email,
            instance.tenant.slug,
            instance.role,
        )


@receiver(post_save, sender=Invitation)
def invitation_post_save(
    sender,  # noqa: ANN001, ARG001
    instance: Invitation,
    created: bool,
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Handle invitation creation/update events.

    Args:
        sender: The model class (Invitation).
        instance: The actual Invitation instance.
        created: True if this is a new record.
        **kwargs: Additional signal arguments.
    """
    if created:
        logger.info(
            "Signal: Invitation created - %s invited to %s",
            instance.email,
            instance.tenant.slug,
        )
