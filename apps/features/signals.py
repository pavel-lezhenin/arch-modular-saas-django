"""Django signals for features module."""
from __future__ import annotations

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.features.models import Feature, TenantFeature

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Feature)
def feature_changed(
    sender,  # noqa: ANN001, ARG001
    instance: Feature,
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Handle feature creation/update/delete events.

    Invalidates all tenant caches when a feature definition changes.

    Args:
        sender: The model class (Feature).
        instance: The actual Feature instance.
        **kwargs: Additional signal arguments.
    """
    from apps.tenants.models import Tenant

    # Invalidate cache for all tenants
    # In production, you might want to do this differently (e.g., via background task)
    logger.info("Feature %s changed, invalidating caches", instance.code)

    for tenant in Tenant.objects.all():
        cache_key = f"feature:{tenant.id}:{instance.code}"
        from django.core.cache import cache
        cache.delete(cache_key)


@receiver([post_save, post_delete], sender=TenantFeature)
def tenant_feature_changed(
    sender,  # noqa: ANN001, ARG001
    instance: TenantFeature,
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Handle tenant feature override changes.

    Args:
        sender: The model class (TenantFeature).
        instance: The actual TenantFeature instance.
        **kwargs: Additional signal arguments.
    """
    logger.info(
        "Signal: TenantFeature changed - %s for %s",
        instance.feature.code,
        instance.tenant.slug,
    )

    # Invalidate cache for this specific tenant/feature
    cache_key = f"feature:{instance.tenant.id}:{instance.feature.code}"
    from django.core.cache import cache
    cache.delete(cache_key)
