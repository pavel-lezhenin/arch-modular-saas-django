"""Seed database with initial data.

Usage:
    python manage.py seed_data                    # Create all seed data
    python manage.py seed_data --reset            # Reset and recreate all data
    python manage.py seed_data --tenants          # Only create tenants
    python manage.py seed_data --users            # Only create users
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

if TYPE_CHECKING:
    from argparse import ArgumentParser

User = get_user_model()


class Command(BaseCommand):
    """Seed database with demo data for development."""

    help = "Seed database with demo data"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset data before seeding",
        )
        parser.add_argument(
            "--tenants",
            action="store_true",
            help="Only seed tenants",
        )
        parser.add_argument(
            "--users",
            action="store_true",
            help="Only seed users",
        )
        parser.add_argument(
            "--plans",
            action="store_true",
            help="Only seed billing plans",
        )
        parser.add_argument(
            "--features",
            action="store_true",
            help="Only seed feature flags",
        )

    @transaction.atomic
    def handle(self, *args: str, **options: bool) -> None:  # noqa: ARG002
        """Execute the command."""
        reset = options["reset"]
        seed_all = not any(
            [options["tenants"], options["users"], options["plans"], options["features"]]
        )

        if reset:
            self._reset_data()

        if seed_all or options["plans"]:
            self._seed_plans()

        if seed_all or options["features"]:
            self._seed_features()

        if seed_all or options["users"]:
            self._seed_users()

        if seed_all or options["tenants"]:
            self._seed_tenants()

        self.stdout.write(self.style.SUCCESS("\n✅ Database seeded successfully!"))
        self._print_summary()

    def _reset_data(self) -> None:
        """Reset all seeded data."""
        from apps.billing.models import Plan, Subscription
        from apps.features.models import Feature, TenantFeature
        from apps.members.models import Member
        from apps.tenants.models import Tenant

        self.stdout.write("🗑️  Resetting data...")
        TenantFeature.objects.all().delete()
        Subscription.objects.all().delete()
        Member.objects.all().delete()
        Tenant.objects.all().delete()
        Feature.objects.all().delete()
        Plan.objects.all().delete()
        User.objects.filter(email__endswith="@demo.saas.local").delete()

    def _seed_plans(self) -> None:
        """Create billing plans."""
        from apps.billing.models import Plan, PlanTier

        self.stdout.write("💰 Creating billing plans...")

        plans_data = [
            {
                "name": "Free",
                "tier": PlanTier.FREE,
                "description": "Perfect for getting started",
                "price_monthly": 0,  # cents
                "price_yearly": 0,
                "max_members": 2,
                "max_storage_gb": 1,
                "is_active": True,
                "is_public": True,
            },
            {
                "name": "Starter",
                "tier": PlanTier.STARTER,
                "description": "For small teams and projects",
                "price_monthly": 1900,  # $19.00
                "price_yearly": 19000,  # $190.00
                "max_members": 5,
                "max_storage_gb": 10,
                "is_active": True,
                "is_public": True,
            },
            {
                "name": "Professional",
                "tier": PlanTier.PROFESSIONAL,
                "description": "For growing teams with advanced needs",
                "price_monthly": 4900,  # $49.00
                "price_yearly": 49000,  # $490.00
                "max_members": 20,
                "max_storage_gb": 50,
                "is_active": True,
                "is_public": True,
            },
            {
                "name": "Enterprise",
                "tier": PlanTier.ENTERPRISE,
                "description": "For large organizations with custom requirements",
                "price_monthly": 19900,  # $199.00
                "price_yearly": 199000,  # $1990.00
                "max_members": 100,
                "max_storage_gb": 500,
                "is_active": True,
                "is_public": True,
            },
        ]

        for plan_data in plans_data:
            plan, created = Plan.objects.update_or_create(
                tier=plan_data["tier"],
                defaults=plan_data,
            )
            status = "✨ Created" if created else "📝 Updated"
            self.stdout.write(f"  {status}: {plan.name} (${plan.price_monthly_dollars:.2f}/mo)")

    def _seed_features(self) -> None:
        """Create feature flags."""
        from apps.features.models import Feature

        self.stdout.write("🚩 Creating feature flags...")

        features_data = [
            {
                "code": "new_dashboard",
                "name": "New Dashboard",
                "description": "Enable the redesigned dashboard UI",
                "is_active": True,
                "enabled_by_default": False,
                "requires_plan_tier": None,
            },
            {
                "code": "ai_assistant",
                "name": "AI Assistant",
                "description": "AI-powered assistant for users",
                "is_active": True,
                "enabled_by_default": False,
                "requires_plan_tier": "professional",
            },
            {
                "code": "dark_mode",
                "name": "Dark Mode",
                "description": "Dark theme support",
                "is_active": True,
                "enabled_by_default": True,
                "requires_plan_tier": None,
            },
            {
                "code": "advanced_analytics",
                "name": "Advanced Analytics",
                "description": "Advanced analytics and reporting",
                "is_active": True,
                "enabled_by_default": False,
                "requires_plan_tier": "professional",
            },
            {
                "code": "api_v2",
                "name": "API v2",
                "description": "Access to new API v2 endpoints",
                "is_active": True,
                "enabled_by_default": False,
                "requires_plan_tier": "starter",
            },
            {
                "code": "sso",
                "name": "Single Sign-On",
                "description": "SAML/SSO authentication support",
                "is_active": True,
                "enabled_by_default": False,
                "requires_plan_tier": "enterprise",
            },
            {
                "code": "audit_logs",
                "name": "Audit Logs",
                "description": "Detailed audit logging for compliance",
                "is_active": True,
                "enabled_by_default": False,
                "requires_plan_tier": "professional",
            },
        ]

        for feature_data in features_data:
            feature, created = Feature.objects.update_or_create(
                code=feature_data["code"],
                defaults=feature_data,
            )
            status = "✨ Created" if created else "📝 Updated"
            tier = feature.requires_plan_tier or "all"
            self.stdout.write(f"  {status}: {feature.code} (min tier: {tier})")

    def _seed_users(self) -> None:
        """Create demo users."""
        self.stdout.write("👤 Creating users...")

        users_data = [
            {
                "email": "admin@demo.saas.local",
                "password": "admin123",
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "owner@demo.saas.local",
                "password": "owner123",
                "first_name": "Owner",
                "last_name": "Demo",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "manager@demo.saas.local",
                "password": "manager123",
                "first_name": "Manager",
                "last_name": "Demo",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "member@demo.saas.local",
                "password": "member123",
                "first_name": "Member",
                "last_name": "Demo",
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        for user_data in users_data:
            password = user_data.pop("password")
            user, created = User.objects.get_or_create(
                email=user_data["email"],
                defaults=user_data,
            )
            if created:
                user.set_password(password)
                user.save()
                status = "✨ Created"
            else:
                status = "⏭️  Exists"
            role = "superuser" if user.is_superuser else "staff" if user.is_staff else "user"
            self.stdout.write(f"  {status}: {user.email} ({role})")

    def _seed_tenants(self) -> None:
        """Create demo tenants with members."""
        from apps.billing.models import Plan, PlanTier, Subscription, SubscriptionStatus
        from apps.features.models import Feature, TenantFeature
        from apps.members.models import Member
        from apps.shared.roles import Role
        from apps.tenants.models import Tenant, TenantSettings

        self.stdout.write("🏢 Creating tenants...")

        # Get plans
        try:
            free_plan = Plan.objects.get(tier=PlanTier.FREE)
            pro_plan = Plan.objects.get(tier=PlanTier.PROFESSIONAL)
            enterprise_plan = Plan.objects.get(tier=PlanTier.ENTERPRISE)
        except Plan.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠️  Plans not found. Run with --plans first."))
            return

        # Get users
        try:
            owner = User.objects.get(email="owner@demo.saas.local")
            manager = User.objects.get(email="manager@demo.saas.local")
            member = User.objects.get(email="member@demo.saas.local")
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING("  ⚠️  Users not found. Run with --users first."))
            return

        tenants_data = [
            {
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "status": "active",
                "plan": pro_plan,
                "subscription_status": SubscriptionStatus.ACTIVE,
                "members": [
                    (owner, Role.OWNER),
                    (manager, Role.ADMIN),
                    (member, Role.MEMBER),
                ],
                "settings": {
                    "max_members": 20,
                },
                "features": ["dark_mode", "advanced_analytics"],
            },
            {
                "name": "Startup Inc",
                "slug": "startup-inc",
                "status": "trial",
                "plan": free_plan,
                "subscription_status": SubscriptionStatus.TRIALING,
                "members": [
                    (owner, Role.OWNER),
                ],
                "settings": {
                    "max_members": 2,
                },
                "features": ["dark_mode", "new_dashboard"],
            },
            {
                "name": "Enterprise Global",
                "slug": "enterprise-global",
                "status": "active",
                "plan": enterprise_plan,
                "subscription_status": SubscriptionStatus.ACTIVE,
                "members": [
                    (owner, Role.OWNER),
                    (manager, Role.ADMIN),
                ],
                "settings": {
                    "max_members": 100,
                },
                "features": [
                    "dark_mode",
                    "ai_assistant",
                    "advanced_analytics",
                    "api_v2",
                    "sso",
                    "audit_logs",
                ],
            },
        ]

        for tenant_data in tenants_data:
            # Create tenant
            tenant, created = Tenant.objects.update_or_create(
                slug=tenant_data["slug"],
                defaults={
                    "name": tenant_data["name"],
                    "status": tenant_data["status"],
                },
            )
            status_icon = "✨ Created" if created else "📝 Updated"
            self.stdout.write(f"  {status_icon}: {tenant.name}")

            # Create settings
            settings_data = tenant_data.get("settings", {})
            TenantSettings.objects.update_or_create(
                tenant=tenant,
                defaults=settings_data,
            )

            # Create subscription
            Subscription.objects.update_or_create(
                tenant=tenant,
                defaults={
                    "plan": tenant_data["plan"],
                    "status": tenant_data["subscription_status"],
                },
            )
            self.stdout.write(f"    💳 Plan: {tenant_data['plan'].name}")

            # Create members
            for user, role in tenant_data["members"]:
                Member.objects.update_or_create(
                    tenant=tenant,
                    user=user,
                    defaults={"role": role.value},
                )
            self.stdout.write(f"    👥 Members: {len(tenant_data['members'])}")

            # Enable features
            for feature_code in tenant_data.get("features", []):
                try:
                    feature = Feature.objects.get(code=feature_code)
                    TenantFeature.objects.update_or_create(
                        tenant=tenant,
                        feature=feature,
                        defaults={"is_enabled": True},
                    )
                except Feature.DoesNotExist:
                    pass
            self.stdout.write(f"    🚩 Features: {len(tenant_data.get('features', []))}")

    def _print_summary(self) -> None:
        """Print summary of seeded data."""
        from apps.billing.models import Plan, Subscription
        from apps.features.models import Feature
        from apps.members.models import Member
        from apps.tenants.models import Tenant

        self.stdout.write("\n📊 Summary:")
        self.stdout.write(f"  Users: {User.objects.count()}")
        self.stdout.write(f"  Tenants: {Tenant.objects.count()}")
        self.stdout.write(f"  Members: {Member.objects.count()}")
        self.stdout.write(f"  Plans: {Plan.objects.count()}")
        self.stdout.write(f"  Subscriptions: {Subscription.objects.count()}")
        self.stdout.write(f"  Features: {Feature.objects.count()}")

        self.stdout.write("\n🔐 Demo Credentials:")
        self.stdout.write("  Admin: admin@demo.saas.local / admin123")
        self.stdout.write("  Owner: owner@demo.saas.local / owner123")
        self.stdout.write("  Manager: manager@demo.saas.local / manager123")
        self.stdout.write("  Member: member@demo.saas.local / member123")
