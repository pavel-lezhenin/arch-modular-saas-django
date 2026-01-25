"""URL configuration for billing module."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.billing.views import (
    BillingView,
    CheckoutView,
    PlanViewSet,
    PortalView,
    StripeWebhookView,
    SubscriptionView,
    UsageView,
)

app_name = "billing"

router = DefaultRouter()
router.register("plans", PlanViewSet, basename="plan")

urlpatterns = [
    # Plan listing (public)
    path("", include(router.urls)),
    # Billing overview
    path("overview/", BillingView.as_view(), name="overview"),
    # Subscription management
    path("subscription/", SubscriptionView.as_view(), name="subscription"),
    # Stripe integration
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("portal/", PortalView.as_view(), name="portal"),
    path("webhook/", StripeWebhookView.as_view(), name="webhook"),
    # Usage tracking
    path("usage/", UsageView.as_view(), name="usage"),
]
