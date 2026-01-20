"""Business logic services for features module."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.cache import cache
from django.db import transaction

from apps.features.models import Feature, TenantFeature
from apps.shared.exceptions import NotFoundError

if TYPE_CHECKING:
    from apps.tenants.models import Tenant

logger = logging.getLogger(__name__)

CACHE_TTL = 300  # 5 minutes


class FeatureService:
    """Service for feature flag operations."""

    @staticmethod
    def get_feature(code: str) -> Feature:
        """Get feature by code.

        Args:
            code: Feature code.

        Returns:
            Feature instance.

        Raises:
            NotFoundError: If feature not found.
        """
        try:
            return Feature.objects.get(code=code)
        except Feature.DoesNotExist:
            msg = "Feature"
            raise NotFoundError(msg, code) from None

    @staticmethod
    def get_all_features(*, active_only: bool = True) -> list[Feature]:
        """Get all features.

        Args:
            active_only: If True, return only active features.

        Returns:
            List of Feature instances.
        """
        qs = Feature.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        return list(qs.order_by("code"))

    @staticmethod
    def is_feature_enabled(tenant: Tenant, feature_code: str) -> tuple[bool, str]:
        """Check if a feature is enabled for a tenant.

        Args:
            tenant: Tenant to check.
            feature_code: Feature code to check.

        Returns:
            Tuple of (is_enabled, reason).
        """
        # Check cache first
        cache_key = f"feature:{tenant.id}:{feature_code}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            feature = Feature.objects.get(code=feature_code)
        except Feature.DoesNotExist:
            result = (False, "Feature not found")
            cache.set(cache_key, result, CACHE_TTL)
            return result

        # Check global kill switch
        if not feature.is_active:
            result = (False, "Feature is globally disabled")
            cache.set(cache_key, result, CACHE_TTL)
            return result

        # Check plan tier requirement
        if feature.requires_plan_tier:
            tenant_tier = FeatureService._get_tenant_tier(tenant)
            tier_order = ["free", "starter", "professional", "enterprise"]

            try:
                required_idx = tier_order.index(feature.requires_plan_tier)
                tenant_idx = tier_order.index(tenant_tier)

                if tenant_idx < required_idx:
                    result = (False, f"Requires {feature.requires_plan_tier} plan or higher")
                    cache.set(cache_key, result, CACHE_TTL)
                    return result
            except ValueError:
                logger.warning(
                    "Invalid plan tier: required=%s, tenant=%s",
                    feature.requires_plan_tier,
                    tenant_tier,
                )

        # Check tenant-specific override
        tenant_override = TenantFeature.objects.filter(
            tenant=tenant, feature=feature
        ).first()

        if tenant_override:
            status = "enabled" if tenant_override.is_enabled else "disabled"
            result = (tenant_override.is_enabled, f"Tenant override: {status}")
            cache.set(cache_key, result, CACHE_TTL)
            return result

        # Fall back to default
        status = "enabled" if feature.enabled_by_default else "disabled"
        result = (feature.enabled_by_default, f"Default: {status}")
        cache.set(cache_key, result, CACHE_TTL)
        return result

    @staticmethod
    def _get_tenant_tier(tenant: Tenant) -> str:
        """Get tenant's current plan tier.

        Args:
            tenant: Tenant to check.

        Returns:
            Plan tier string.
        """
        try:
            if hasattr(tenant, "subscription") and tenant.subscription:
                return tenant.subscription.plan.tier
        except Exception:  # noqa: BLE001  # nosec B110 - graceful fallback to free tier
            pass
        return "free"

    @staticmethod
    def get_tenant_features(tenant: Tenant) -> list[dict]:
        """Get all feature statuses for a tenant.

        Args:
            tenant: Tenant to get features for.

        Returns:
            List of feature status dictionaries.
        """
        features = FeatureService.get_all_features(active_only=True)
        result = []

        for feature in features:
            is_enabled, reason = FeatureService.is_feature_enabled(tenant, feature.code)
            result.append({
                "code": feature.code,
                "name": feature.name,
                "is_enabled": is_enabled,
                "reason": reason,
            })

        return result

    @staticmethod
    @transaction.atomic
    def set_tenant_feature(
        tenant: Tenant, feature_code: str, is_enabled: bool
    ) -> TenantFeature:
        """Set feature flag for a tenant.

        Args:
            tenant: Tenant to set feature for.
            feature_code: Feature code.
            is_enabled: Whether feature should be enabled.

        Returns:
            TenantFeature instance.

        Raises:
            NotFoundError: If feature not found.
        """
        feature = FeatureService.get_feature(feature_code)

        tenant_feature, created = TenantFeature.objects.update_or_create(
            tenant=tenant,
            feature=feature,
            defaults={"is_enabled": is_enabled},
        )

        # Invalidate cache
        cache_key = f"feature:{tenant.id}:{feature_code}"
        cache.delete(cache_key)

        action = "enabled" if is_enabled else "disabled"
        logger.info("Feature %s %s for tenant %s", feature_code, action, tenant.slug)

        return tenant_feature

    @staticmethod
    def reset_tenant_feature(tenant: Tenant, feature_code: str) -> None:
        """Remove tenant override, reverting to default.

        Args:
            tenant: Tenant to reset feature for.
            feature_code: Feature code.

        Raises:
            NotFoundError: If feature not found.
        """
        feature = FeatureService.get_feature(feature_code)

        TenantFeature.objects.filter(tenant=tenant, feature=feature).delete()

        # Invalidate cache
        cache_key = f"feature:{tenant.id}:{feature_code}"
        cache.delete(cache_key)

        logger.info("Reset feature %s to default for tenant %s", feature_code, tenant.slug)

    @staticmethod
    def invalidate_tenant_cache(tenant: Tenant) -> None:
        """Invalidate all feature cache for a tenant.

        Args:
            tenant: Tenant to invalidate cache for.
        """
        features = FeatureService.get_all_features(active_only=False)
        for feature in features:
            cache_key = f"feature:{tenant.id}:{feature.code}"
            cache.delete(cache_key)
