# arch-modular-saas-django

**Modular Monolith SaaS Backend** - Django reference implementation showcasing module boundaries, inter-module communication via signals, and graceful service degradation.

## 🎯 What This Project Demonstrates

This is a **reference architecture** for building multi-tenant SaaS applications using **Modular Monolith** pattern with Django. It shows:

| Pattern | Implementation |
|---------|----------------|
| **Module Boundaries** | Each Django app is a self-contained module with clear API |
| **Inter-Module Communication** | Django signals for loose coupling between modules |
| **Graceful Degradation** | Works without Stripe, OAuth, external email |
| **Multi-Tenancy** | Tenant context via middleware, scoped queries |
| **RBAC** | Role-based access control (Owner → Admin → Member) |
| **Feature Flags** | Per-tenant feature toggles with plan-based restrictions |

## 📁 Architecture Overview

```
apps/
├── shared/           # Cross-cutting concerns
│   ├── models.py     # BaseModel (UUID, timestamps)
│   ├── roles.py      # Role & Permission enums, RBAC
│   ├── permissions.py # DRF permission classes
│   ├── middleware.py # Tenant context middleware
│   └── email.py      # Graceful email backend
│
├── tenants/          # Multi-tenancy core
│   ├── models.py     # Tenant, TenantSettings
│   ├── services.py   # Business logic
│   └── signals.py    # Tenant events
│
├── authentication/   # User identity
│   ├── models.py     # Custom User (email-based), UserSession
│   └── services.py   # Registration, sessions
│
├── members/          # User-Tenant association
│   ├── models.py     # Member, Invitation
│   └── services.py   # Membership, invitations
│
├── billing/          # Subscription management
│   ├── models.py     # Plan, Subscription, UsageRecord
│   └── services.py   # Stripe integration (optional)
│
└── features/         # Feature flags
    ├── models.py     # Feature, TenantFeature
    └── services.py   # Flag evaluation with caching
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd packages/arch-modular-saas-django

# Create virtual environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
uv pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
```

### 2. Start Infrastructure

```bash
docker compose up -d
```

This starts:
- **PostgreSQL** (5432) - Primary database
- **Redis** (6379) - Cache & sessions
- **MinIO** (9000/9001) - S3-compatible storage
- **MailHog** (1025/8025) - Email testing
- **Grafana** (3000) - Observability

### 3. Run Migrations & Start Server

```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### 4. Access

- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/
- **API Docs**: http://localhost:8000/api/docs/
- **MailHog**: http://localhost:8025
- **Grafana**: http://localhost:3000 (admin/admin)

## 🔧 Configuration

All services are **optional** and degrade gracefully:

| Service | Without Config | With Config |
|---------|---------------|-------------|
| **Email** | Console output | Resend API / SMTP |
| **OAuth** | Disabled | Google, GitHub login |
| **Billing** | Mock subscriptions | Stripe integration |
| **Storage** | Local filesystem | S3 / MinIO |

See `.env.example` for all configuration options.

## 📚 Module Details

### Tenants Module

Core multi-tenancy implementation:

```python
# Create tenant
tenant = TenantService.create_tenant(name="Acme Inc", slug="acme")

# Tenant context via middleware (automatic from X-Tenant-ID header)
tenant = get_current_tenant()
```

### Members Module

User-to-tenant relationships with RBAC:

```python
# Add member
member = MemberService.add_member(tenant, user, role=Role.ADMIN)

# Check permission
if has_permission(member.role_enum, Permission.MEMBER_MANAGE):
    # Can manage members
```

### Billing Module

Subscription management with Stripe (or mock):

```python
# Create subscription (works with or without Stripe)
subscription = SubscriptionService.change_plan(
    tenant=tenant,
    new_plan=plan,
    billing_interval=BillingInterval.MONTHLY,
)
```

### Features Module

Per-tenant feature flags:

```python
# Check feature
is_enabled, reason = FeatureService.is_feature_enabled(tenant, "advanced_analytics")

# Set override
FeatureService.set_tenant_feature(tenant, "beta_ui", is_enabled=True)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Unit tests only (fast, no DB)
pytest tests/unit

# Integration tests (requires Docker)
pytest tests/integration

# With coverage
pytest --cov=apps --cov-report=html
```

## 🛠️ Development

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy apps

# All checks
make lint
```

## 📋 API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `GET/PATCH /api/auth/me/` - Current user profile
- `POST /api/auth/password/change/` - Change password
- `GET /api/auth/sessions/` - List active sessions

### Tenants
- `GET/POST /api/tenants/` - List/create tenants
- `GET/PATCH/DELETE /api/tenants/{id}/` - Tenant CRUD
- `GET/PATCH /api/tenants/{id}/settings/` - Tenant settings

### Members
- `GET /api/members/my-memberships/` - User's memberships
- `GET/POST /api/members/members/` - List/add members
- `POST /api/members/invitations/` - Create invitation
- `GET/POST /api/members/invite/{token}/` - Accept invitation

### Billing
- `GET /api/billing/` - Billing overview
- `GET/POST/DELETE /api/billing/subscription/` - Manage subscription
- `GET /api/billing/plans/` - Available plans
- `POST /api/billing/checkout/` - Stripe checkout session

### Features
- `GET /api/features/` - All features
- `GET /api/features/tenant/` - Tenant feature flags
- `GET /api/features/check/{code}/` - Check specific feature

## 🏗️ Why Modular Monolith?

This architecture demonstrates the **evolutionary path**:

```
Layered Architecture → Modular Monolith → Microservices
        ↑                    ↑                  ↑
    Simple apps      Most SaaS projects    At scale only
```

**Modular Monolith advantages:**
- ✅ Clear module boundaries like microservices
- ✅ Single deployment, simple operations
- ✅ Refactoring across modules is easy
- ✅ Ready to extract modules when needed

## 📖 Further Reading

- [Django Apps as Modules](https://docs.djangoproject.com/en/5.1/ref/applications/)
- [Django Signals](https://docs.djangoproject.com/en/5.1/topics/signals/)
- [Modular Monolith Pattern](https://www.kamilgrzybek.com/blog/posts/modular-monolith-primer)

## 📋 Standards

- ✅ Strict typing (mypy strict + django-stubs)
- ✅ 80%+ test coverage
- ✅ Auto-formatting (ruff)
- ✅ Secret detection (bandit)
- ✅ Django best practices
