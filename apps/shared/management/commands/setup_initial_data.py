"""Management command to setup initial data for development."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.authentication.models import User
from apps.billing.models import BillingInterval, Plan, PlanTier, Subscription, SubscriptionStatus
from apps.features.models import Feature
from apps.members.models import Member
from apps.shared.roles import Role
from apps.tenants.models import Tenant, TenantSettings, TenantStatus


class Command(BaseCommand):
    """Setup initial data for development environment."""

    help = "Create initial data for development: plans, features, demo tenant"

    def add_arguments(self, parser: Any) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--demo",
            action="store_true",
            help="Create demo tenant with test user",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Reset existing data",
        )

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: ARG002
        """Execute the command."""
        with transaction.atomic():
            self._create_plans(force=options["force"])
            self._create_features(force=options["force"])

            if options["demo"]:
                self._create_demo_tenant(force=options["force"])

        self.stdout.write(self.style.SUCCESS("✅ Initial data created successfully!"))

    def _create_plans(self, *, force: bool = False) -> None:
        """Create billing plans."""
        if force:
            Plan.objects.all().delete()
            self.stdout.write("  Deleted existing plans")

        plans = [
            {
                "code": "free",
                "name": "Free",
                "tier": PlanTier.FREE,
                "description": "Get started with basic features",
                "price_monthly": 0,
                "price_yearly": 0,
                "max_members": 3,
                "max_projects": 1,
                "features": {"storage_gb": 1, "api_calls_monthly": 1000},
                "is_active": True,
            },
            {
                "code": "starter",
                "name": "Starter",
                "tier": PlanTier.STARTER,
                "description": "For small teams getting started",
                "price_monthly": 1900,  # $19.00
                "price_yearly": 19000,  # $190.00
                "max_members": 10,
                "max_projects": 5,
                "features": {"storage_gb": 10, "api_calls_monthly": 10000},
                "is_active": True,
            },
            {
                "code": "professional",
                "name": "Professional",
                "tier": PlanTier.PROFESSIONAL,
                "description": "For growing teams with advanced needs",
                "price_monthly": 4900,  # $49.00
                "price_yearly": 49000,  # $490.00
                "max_members": 50,
                "max_projects": 25,
                "features": {
                    "storage_gb": 100,
                    "api_calls_monthly": 100000,
                    "advanced_analytics": True,
                },
                "is_active": True,
            },
            {
                "code": "enterprise",
                "name": "Enterprise",
                "tier": PlanTier.ENTERPRISE,
                "description": "For large organizations with custom needs",
                "price_monthly": 19900,  # $199.00
                "price_yearly": 199000,  # $1990.00
                "max_members": None,  # Unlimited
                "max_projects": None,  # Unlimited
                "features": {
                    "storage_gb": None,  # Unlimited
                    "api_calls_monthly": None,  # Unlimited
                    "advanced_analytics": True,
                    "sso": True,
                    "audit_log": True,
                    "priority_support": True,
                },
                "is_active": True,
            },
        ]

        for plan_data in plans:
            plan, created = Plan.objects.update_or_create(
                code=plan_data["code"],
                defaults=plan_data,
            )
            status = "created" if created else "updated"
            self.stdout.write(f"  Plan '{plan.name}' {status}")

    def _create_features(self, *, force: bool = False) -> None:
        """Create feature flags."""
        if force:
            Feature.objects.all().delete()
            self.stdout.write("  Deleted existing features")

        features = [
            {
                "code": "dark_mode",
                "name": "Dark Mode",
                "description": "Enable dark mode UI theme",
                "is_enabled_by_default": True,
                "min_plan_tier": None,
            },
            {
                "code": "advanced_analytics",
                "name": "Advanced Analytics",
                "description": "Access to advanced analytics dashboards",
                "is_enabled_by_default": False,
                "min_plan_tier": PlanTier.PROFESSIONAL,
            },
            {
                "code": "api_access",
                "name": "API Access",
                "description": "Access to REST API",
                "is_enabled_by_default": True,
                "min_plan_tier": PlanTier.STARTER,
            },
            {
                "code": "sso",
                "name": "Single Sign-On",
                "description": "SAML/OIDC single sign-on integration",
                "is_enabled_by_default": False,
                "min_plan_tier": PlanTier.ENTERPRISE,
            },
            {
                "code": "audit_log",
                "name": "Audit Log",
                "description": "Detailed audit trail of all actions",
                "is_enabled_by_default": False,
                "min_plan_tier": PlanTier.ENTERPRISE,
            },
            {
                "code": "custom_branding",
                "name": "Custom Branding",
                "description": "Custom logo and colors",
                "is_enabled_by_default": False,
                "min_plan_tier": PlanTier.PROFESSIONAL,
            },
            {
                "code": "beta_features",
                "name": "Beta Features",
                "description": "Access to experimental features",
                "is_enabled_by_default": False,
                "min_plan_tier": None,
            },
        ]

        for feature_data in features:
            feature, created = Feature.objects.update_or_create(
                code=feature_data["code"],
                defaults=feature_data,
            )
            status = "created" if created else "updated"
            self.stdout.write(f"  Feature '{feature.name}' {status}")

    def _create_demo_tenant(self, *, force: bool = False) -> None:
        """Create demo tenant with test user."""
        if force:
            User.objects.filter(email="demo@example.com").delete()
            Tenant.objects.filter(slug="demo").delete()
            self.stdout.write("  Deleted existing demo data")

        # Create demo user
        user, user_created = User.objects.get_or_create(
            email="demo@example.com",
            defaults={
                "first_name": "Demo",
                "last_name": "User",
                "is_active": True,
            },
        )
        if user_created:
            user.set_password("demo1234")
            user.save()
            self.stdout.write("  Created demo user (demo@example.com / demo1234)")
        else:
            self.stdout.write("  Demo user already exists")

        # Create demo tenant
        tenant, tenant_created = Tenant.objects.get_or_create(
            slug="demo",
            defaults={
                "name": "Demo Company",
                "status": TenantStatus.ACTIVE,
            },
        )
        if tenant_created:
            TenantSettings.objects.create(tenant=tenant)
            self.stdout.write("  Created demo tenant")
        else:
            self.stdout.write("  Demo tenant already exists")

        # Create membership
        member, member_created = Member.objects.get_or_create(
            tenant=tenant,
            user=user,
            defaults={
                "role": Role.OWNER.value,
            },
        )
        if member_created:
            self.stdout.write("  Created owner membership")
        else:
            self.stdout.write("  Membership already exists")

        # Create subscription (free plan)
        free_plan = Plan.objects.filter(tier=PlanTier.FREE).first()
        if free_plan:
            subscription, sub_created = Subscription.objects.get_or_create(
                tenant=tenant,
                defaults={
                    "plan": free_plan,
                    "status": SubscriptionStatus.ACTIVE,
                    "billing_interval": BillingInterval.MONTHLY,
                },
            )
            if sub_created:
                self.stdout.write("  Created free subscription")
            else:
                self.stdout.write("  Subscription already exists")

        self.stdout.write(
            self.style.SUCCESS(
                "\n  Demo credentials:\n"
                "    Email: demo@example.com\n"
                "    Password: demo1234\n"
                "    Tenant: demo"
            )
        )
