# arch-modular-saas-django

**Modular Monolith SaaS Backend** — Django reference implementation showcasing module boundaries, inter-module communication, and evolutionary architecture.

## 🎯 Purpose

This project demonstrates how to build a **production-ready SaaS backend** using the **Modular Monolith** pattern. It serves as:

1. **Learning resource** — understand MM principles with real code
2. **Starting template** — fork and build your SaaS product
3. **Architecture reference** — patterns for team discussions

## 📐 Modular Monolith Principles

### What is Modular Monolith?

```
┌─────────────────────────────────────────────────────────────┐
│                    SINGLE DEPLOYMENT                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Tenants  │  │   Auth   │  │ Members  │  │ Billing  │   │
│  │  Module  │←→│  Module  │←→│  Module  │←→│  Module  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       ↓              ↓              ↓              ↓        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SHARED DATABASE                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key difference from Layered Architecture:**
- Layered: horizontal slices (controllers → services → repositories)
- Modular Monolith: vertical slices (each module owns its full stack)

### Core Rules

| Rule | Description | This Project |
|------|-------------|--------------|
| **Module = Bounded Context** | Each module owns its domain | 5 Django apps with clear boundaries |
| **Public API only** | Modules communicate via defined interfaces | Services + Signals |
| **No cross-module DB queries** | Don't join tables across modules | Each module queries only its models |
| **Loose coupling** | Modules can be extracted to microservices | Django signals for events |
| **High cohesion** | Related code stays together | models + services + views per module |

### Anti-Patterns to Avoid

```python
# ❌ BAD: Direct model import across modules
from apps.billing.models import Subscription
subscription = Subscription.objects.filter(tenant=tenant).first()

# ✅ GOOD: Use service layer
from apps.billing.services import SubscriptionService
subscription = SubscriptionService.get_subscription(tenant)

# ❌ BAD: Circular imports between modules
# members/services.py imports billing/services.py
# billing/services.py imports members/services.py

# ✅ GOOD: Use signals for reverse communication
# billing emits signal → members listens and reacts
```

## 🏗️ Architecture

### Module Structure

Each module follows the same pattern:

```
apps/<module>/
├── __init__.py      # Module initialization
├── apps.py          # Django AppConfig with signal registration
├── models.py        # Domain models (Django ORM)
├── services.py      # Business logic (stateless functions)
├── serializers.py   # API serialization (DRF)
├── views.py         # API endpoints (DRF ViewSets/Views)
├── urls.py          # URL routing
├── signals.py       # Event emission and handling
└── admin.py         # Django Admin configuration
```

### Module Responsibilities

| Module | Domain | Key Models | Public API |
|--------|--------|------------|------------|
| **tenants** | Multi-tenancy | Tenant, TenantSettings | TenantService |
| **authentication** | Identity | User, UserSession | UserService, SessionService |
| **members** | Membership | Member, Invitation | MemberService, InvitationService |
| **billing** | Subscriptions | Plan, Subscription | SubscriptionService, PlanService |
| **features** | Feature flags | Feature, TenantFeature | FeatureService |
| **shared** | Cross-cutting | BaseModel | Middleware, Permissions, Exceptions |

### Inter-Module Communication

**Rule:** Modules communicate via **Services** (sync) and **Signals** (async/events).

```python
# Synchronous: Service call
# members/services.py
from apps.tenants.services import TenantService

class MemberService:
    @staticmethod
    def add_member(tenant_id: UUID, user: User, role: Role) -> Member:
        tenant = TenantService.get_tenant(tenant_id)  # ← Service call
        # ... create member
```

```python
# Asynchronous: Signal emission
# billing/signals.py
from django.dispatch import Signal

subscription_changed = Signal()  # Custom signal

# When subscription changes:
subscription_changed.send(
    sender=Subscription,
    tenant=tenant,
    old_plan=old_plan,
    new_plan=new_plan,
)
```

```python
# Signal handling in another module
# features/apps.py
def ready(self):
    from apps.billing.signals import subscription_changed
    subscription_changed.connect(handle_plan_change)

def handle_plan_change(sender, tenant, new_plan, **kwargs):
    # Update feature flags based on new plan
    FeatureService.sync_plan_features(tenant, new_plan)
```

## 🔐 RBAC System

### Roles Hierarchy

```
OWNER (все права)
  ↓
ADMIN (управление, но не удаление tenant)
  ↓
MEMBER (только чтение)
```

### Permissions

```python
class Permission(str, Enum):
    # Tenant
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"  # Owner only
    
    # Members
    MEMBERS_INVITE = "members:invite"
    MEMBERS_REMOVE = "members:remove"
    MEMBERS_CHANGE_ROLE = "members:change_role"
    
    # Billing
    BILLING_READ = "billing:read"
    BILLING_MANAGE = "billing:manage"
    
    # Features
    FEATURES_READ = "features:read"
    FEATURES_OVERRIDE = "features:override"
```

### Usage Example

```python
from apps.shared.roles import has_permission, Role, Permission

# In view
if has_permission(member.role, Permission.MEMBERS_INVITE):
    # Can invite new members
    
# Or use DRF permission class
from apps.shared.permissions import CanManageMembers

class MemberViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageMembers]
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- uv (recommended) or pip

### Installation

```bash
cd packages/arch-modular-saas-django

# Create virtual environment
uv venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
uv pip install -e ".[dev]"

# Copy environment
cp .env.example .env
```

### Start Services

```bash
# Start infrastructure
docker compose up -d

# Apply migrations
python manage.py migrate

# Create initial data (plans, features)
python manage.py setup_initial_data

# Create superuser for admin
python manage.py createsuperuser
```

### Run Server

```bash
python manage.py runserver
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8000/api/ | — |
| **Django Admin** | http://localhost:8000/admin/ | superuser credentials |
| **API Docs** | http://localhost:8000/api/docs/ | — |
| **MailHog** | http://localhost:8025 | — |
| **Grafana** | http://localhost:3000 | admin / admin |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |

## 🖥️ Django Admin

Django Admin is pre-configured for all modules:

### Accessing Admin

1. Create superuser: `python manage.py createsuperuser`
2. Go to http://localhost:8000/admin/
3. Login with superuser credentials

### What You Can Manage

| Section | Models | Actions |
|---------|--------|---------|
| **Tenants** | Tenant, TenantSettings | Create/edit tenants, configure settings |
| **Authentication** | User, UserSession | Manage users, view sessions |
| **Members** | Member, Invitation | Assign roles, manage invitations |
| **Billing** | Plan, Subscription, UsageRecord | Configure plans, view subscriptions |
| **Features** | Feature, TenantFeature | Toggle features, set overrides |

### Demo Data

```bash
# Create demo tenant with test user
python manage.py setup_initial_data --demo

# Demo credentials:
# Email: demo@example.com
# Password: demo1234
# Tenant: demo
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Unit tests only (no DB required)
pytest tests/unit -v

# Integration tests (requires Docker)
pytest tests/integration -v

# With coverage
pytest --cov=apps --cov-report=html
```

## 📊 Code Statistics

| Metric | Value |
|--------|-------|
| Python files | 59 |
| Lines of code | ~4,500 |
| Test files | 10 |
| Test lines | ~380 |
| Django apps | 6 (5 modules + shared) |
| API endpoints | ~25 |

## 🔧 Configuration

All external services are **optional** with graceful degradation:

| Service | Environment Variable | Default Behavior |
|---------|---------------------|------------------|
| **Email** | `RESEND_API_KEY` | Console output |
| **OAuth Google** | `GOOGLE_CLIENT_ID` | Disabled |
| **OAuth GitHub** | `GITHUB_CLIENT_ID` | Disabled |
| **Stripe** | `STRIPE_SECRET_KEY` | Mock mode |
| **S3 Storage** | `AWS_ACCESS_KEY_ID` | Local filesystem |

## 🏛️ Why Modular Monolith?

### Evolution Path

```
Layered Monolith → Modular Monolith → Microservices
       ↑                  ↑                 ↑
   Start here      Most projects      Only at scale
                   should stay here
```

### When to Use

✅ **Use Modular Monolith when:**
- Building new SaaS product
- Team size: 2-20 developers
- Need clear module boundaries
- Want option to extract services later

❌ **Don't use when:**
- Simple CRUD app (use layered)
- Already at massive scale (consider microservices)
- Team can't maintain discipline

### Benefits

| Benefit | Description |
|---------|-------------|
| **Simple deployment** | Single artifact, no service mesh |
| **Easy refactoring** | IDE support, compile-time checks |
| **Clear boundaries** | Modules can be extracted when needed |
| **Shared infrastructure** | One DB, one cache, one deployment |

## 📚 Further Reading

- [Modular Monolith Primer](https://www.kamilgrzybek.com/blog/posts/modular-monolith-primer)
- [Django Apps as Modules](https://docs.djangoproject.com/en/5.1/ref/applications/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

## 📋 Standards

- ✅ Strict typing (mypy + django-stubs)
- ✅ Linting (ruff)
- ✅ Security scanning (bandit)
- ✅ Pre-commit hooks
- ✅ Django best practices
