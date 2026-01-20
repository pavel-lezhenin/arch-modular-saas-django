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

- **Python 3.12+** — [Download](https://www.python.org/downloads/)
- **Docker & Docker Compose** — [Download](https://www.docker.com/products/docker-desktop/)
- **uv** (recommended) — `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 1. Clone & Setup Environment

```bash
cd packages/arch-modular-saas-django

# Create virtual environment
uv venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
uv pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
```

### 2. Start Infrastructure (Docker)

```bash
# Start PostgreSQL, Redis, MailHog, MinIO, Grafana, Loki
docker compose up -d

# Verify services are running
docker compose ps
```

**Services started:**

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & sessions |
| MailHog | 8025 | Email testing UI |
| MinIO | 9000/9001 | S3-compatible storage |
| Grafana | 3000 | Monitoring dashboards |
| Loki | 3100 | Log aggregation |

### 3. Initialize Database

```bash
# Apply all migrations
python manage.py migrate

# Seed database with demo data
python manage.py seed_data

# Or just create superuser manually
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
# or with auto-reload disabled (more stable on Windows)
python manage.py runserver --noreload
```

### 5. Access Application

| Service | URL | Credentials |
|---------|-----|-------------|
| **API Docs (Swagger)** | http://localhost:8000/api/docs/ | — |
| **API Docs (ReDoc)** | http://localhost:8000/api/redoc/ | — |
| **OpenAPI Schema** | http://localhost:8000/api/schema/ | — |
| **Django Admin** | http://localhost:8000/admin/ | admin@demo.saas.local / admin123 |
| **MailHog** | http://localhost:8025 | — |
| **Grafana** | http://localhost:3000 | admin / admin |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |

## 🌱 Seed Data

The `seed_data` command creates demo data for development:

```bash
# Create all seed data
python manage.py seed_data

# Reset and recreate all data
python manage.py seed_data --reset

# Seed specific entities
python manage.py seed_data --plans      # Billing plans only
python manage.py seed_data --features   # Feature flags only
python manage.py seed_data --users      # Users only
python manage.py seed_data --tenants    # Tenants only
```

### Demo Credentials

| User | Email | Password | Role |
|------|-------|----------|------|
| **Superuser** | admin@demo.saas.local | admin123 | Django admin |
| **Owner** | owner@demo.saas.local | owner123 | Tenant owner |
| **Manager** | manager@demo.saas.local | manager123 | Tenant admin |
| **Member** | member@demo.saas.local | member123 | Regular member |

### Demo Tenants

| Tenant | Slug | Plan | Status |
|--------|------|------|--------|
| Acme Corporation | acme-corp | Professional | Active |
| Startup Inc | startup-inc | Free | Trial |
| Enterprise Global | enterprise-global | Enterprise | Active |

### Billing Plans

| Plan | Price/month | Max Members | Features |
|------|-------------|-------------|----------|
| Free | $0 | 2 | Basic |
| Starter | $19 | 5 | API access |
| Professional | $49 | 20 | Priority support, Custom domain |
| Enterprise | $199 | 100 | SSO, Audit logs, Dedicated support |

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
python manage.py seed_data

# Reset and recreate all demo data:
python manage.py seed_data --reset

# Demo credentials:
# Email: admin@demo.saas.local
# Password: admin123
# Tenant: acme-corp
```

## 🧪 Testing

### Test Strategy

| Type | Location | Database | Speed | Purpose |
|------|----------|----------|-------|---------|
| **Unit** | `tests/unit/` | None | Fast | Business logic, services |
| **Integration** | `tests/integration/` | SQLite | Medium | API endpoints, ORM |
| **Integration + PostgreSQL** | `tests/integration/` | PostgreSQL | Slow | DB-specific features |

### Running Tests

```bash
# All tests (SQLite - fast)
pytest

# Unit tests only (no database)
pytest tests/unit -v

# Integration tests (SQLite)
pytest tests/integration -v

# Integration tests with real PostgreSQL (requires Docker)
pytest tests/integration -v --use-postgres

# With coverage report
pytest --cov=apps --cov-report=html
open htmlcov/index.html

# Parallel execution
pytest -n auto
```

### Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
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
