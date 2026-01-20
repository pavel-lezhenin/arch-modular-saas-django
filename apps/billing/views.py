"""API views for billing module."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import BillingInterval, Plan
from apps.billing.serializers import (
    BillingOverviewSerializer,
    CheckoutSessionSerializer,
    PlanListSerializer,
    PlanSerializer,
    PortalSessionSerializer,
    SubscriptionCreateSerializer,
    SubscriptionSerializer,
    UsageRecordSerializer,
)
from apps.billing.services import (
    PlanService,
    StripeService,
    SubscriptionService,
    UsageService,
)
from apps.shared.middleware import get_current_tenant
from apps.shared.permissions import CanManageBilling, IsTenantOwner

if TYPE_CHECKING:
    from rest_framework.request import Request


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing plans (public)."""

    permission_classes = [AllowAny]
    serializer_class = PlanSerializer

    def get_queryset(self):  # noqa: ANN201
        """Return active public plans."""
        return Plan.objects.filter(is_active=True, is_public=True).order_by("price_monthly")

    def get_serializer_class(self):  # noqa: ANN201
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return PlanListSerializer
        return PlanSerializer


class BillingView(APIView):
    """Billing overview for current tenant."""

    permission_classes = [IsAuthenticated, CanManageBilling]

    def get(self, request: Request) -> Response:  # noqa: ARG002
        """Get billing overview for current tenant.

        Args:
            request: HTTP request.

        Returns:
            Billing overview data.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription = SubscriptionService.get_subscription(tenant)
        usage = UsageService.get_current_usage(tenant)

        data = {
            "subscription": subscription,
            "current_plan": subscription.plan if subscription else None,
            "usage": usage,
            "upcoming_invoice_amount": None,  # Would come from Stripe
        }

        serializer = BillingOverviewSerializer(data)
        return Response(serializer.data)


class SubscriptionView(APIView):
    """Manage subscription for current tenant."""

    permission_classes = [IsAuthenticated, IsTenantOwner]

    def get(self, request: Request) -> Response:  # noqa: ARG002
        """Get current subscription.

        Args:
            request: HTTP request.

        Returns:
            Subscription data.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription = SubscriptionService.get_subscription(tenant)
        if not subscription:
            return Response(
                {"detail": "No active subscription"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        """Create or change subscription.

        Args:
            request: HTTP request with plan data.

        Returns:
            Updated subscription data.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SubscriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = PlanService.get_plan(serializer.validated_data["plan_id"])
        billing_interval = BillingInterval(serializer.validated_data["billing_interval"])

        subscription = SubscriptionService.change_plan(
            tenant=tenant,
            new_plan=plan,
            billing_interval=billing_interval,
        )

        output_serializer = SubscriptionSerializer(subscription)
        return Response(output_serializer.data)

    def delete(self, request: Request) -> Response:
        """Cancel subscription.

        Args:
            request: HTTP request.

        Returns:
            Updated subscription data.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        immediate = request.query_params.get("immediate", "").lower() == "true"
        subscription = SubscriptionService.cancel_subscription(tenant, immediate=immediate)

        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)


class CheckoutView(APIView):
    """Create Stripe Checkout session."""

    permission_classes = [IsAuthenticated, IsTenantOwner]

    def post(self, request: Request) -> Response:
        """Create checkout session for subscription.

        Args:
            request: HTTP request with checkout data.

        Returns:
            Checkout session URL.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = PlanService.get_plan(serializer.validated_data["plan_id"])
        billing_interval = BillingInterval(serializer.validated_data["billing_interval"])

        checkout_url = StripeService.create_checkout_session(
            tenant=tenant,
            plan=plan,
            billing_interval=billing_interval,
            success_url=serializer.validated_data["success_url"],
            cancel_url=serializer.validated_data["cancel_url"],
        )

        if not checkout_url:
            # Stripe not configured - create subscription directly (for development)
            subscription = SubscriptionService.change_plan(
                tenant=tenant,
                new_plan=plan,
                billing_interval=billing_interval,
            )
            return Response({
                "subscription": SubscriptionSerializer(subscription).data,
                "message": "Stripe not configured - subscription created directly",
            })

        return Response({"checkout_url": checkout_url})


class PortalView(APIView):
    """Create Stripe Customer Portal session."""

    permission_classes = [IsAuthenticated, IsTenantOwner]

    def post(self, request: Request) -> Response:
        """Create portal session.

        Args:
            request: HTTP request with portal data.

        Returns:
            Portal session URL.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PortalSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        portal_url = StripeService.create_portal_session(
            tenant=tenant,
            return_url=serializer.validated_data["return_url"],
        )

        if not portal_url:
            return Response(
                {"detail": "Billing portal not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"portal_url": portal_url})


class UsageView(APIView):
    """View usage records for current tenant."""

    permission_classes = [IsAuthenticated, CanManageBilling]

    def get(self, request: Request) -> Response:
        """Get usage records.

        Args:
            request: HTTP request.

        Returns:
            Usage records.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        months = int(request.query_params.get("months", 6))
        usage = UsageService.get_usage_history(tenant, months=months)

        serializer = UsageRecordSerializer(usage, many=True)
        return Response(serializer.data)


class StripeWebhookView(APIView):
    """Handle Stripe webhook events."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Process Stripe webhook.

        Args:
            request: HTTP request with webhook payload.

        Returns:
            Webhook processing result.
        """
        # Verify webhook signature if configured
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)

        if webhook_secret:
            import stripe

            sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
            try:
                event = stripe.Webhook.construct_event(
                    request.body, sig_header, webhook_secret
                )
            except ValueError:
                return Response({"error": "Invalid payload"}, status=400)
            except stripe.error.SignatureVerificationError:
                return Response({"error": "Invalid signature"}, status=400)
        else:
            event = request.data

        # Handle the event
        event_type = event.get("type", "")

        if event_type == "customer.subscription.updated":
            sub_data = event["data"]["object"]
            SubscriptionService.update_subscription_from_stripe(
                stripe_subscription_id=sub_data["id"],
                status=sub_data["status"],
                current_period_start=sub_data["current_period_start"],
                current_period_end=sub_data["current_period_end"],
            )
        elif event_type == "customer.subscription.deleted":
            sub_data = event["data"]["object"]
            SubscriptionService.update_subscription_from_stripe(
                stripe_subscription_id=sub_data["id"],
                status="canceled",
                current_period_start=sub_data["current_period_start"],
                current_period_end=sub_data["current_period_end"],
            )

        return Response({"received": True})
