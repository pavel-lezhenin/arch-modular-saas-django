# Quick Start Guide

This guide will get you up and running with the Modular Monolith SaaS Backend in 5 minutes.

## Prerequisites

- Python 3.14+ (or 3.12+ with minor adjustments)
- Docker & Docker Compose
- uv (recommended) or pip

## Step 1: Install Dependencies

```bash
cd packages/arch-modular-saas-django

# Create virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package with dev dependencies
uv pip install -e ".[dev]"
```

## Step 2: Configure Environment

```bash
# Copy example config
cp .env.example .env

# (Optional) Edit .env to customize settings
# Default settings work out of the box with Docker
```

## Step 3: Start Infrastructure

```bash
# Start all services
docker compose up -d

# Verify services are running
docker compose ps
```

Expected output:
```
NAME                    STATUS
postgres                running (healthy)
redis                   running (healthy)
minio                   running
mailhog                 running
loki                    running
grafana                 running
```

## Step 4: Initialize Database

```bash
# Apply migrations
python manage.py migrate

# Create initial data (plans, features)
python manage.py setup_initial_data

# (Optional) Create demo tenant with test user
python manage.py setup_initial_data --demo
```

## Step 5: Start Development Server

```bash
python manage.py runserver
```

## Step 6: Explore!

### Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| API | http://localhost:8000/api/ | - |
| Admin | http://localhost:8000/admin/ | superuser |
| API Docs | http://localhost:8000/api/docs/ | - |
| MailHog | http://localhost:8025 | - |
| Grafana | http://localhost:3000 | admin / admin |
| MinIO | http://localhost:9001 | minioadmin / minioadmin |

### API Quick Test

```bash
# Register new user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "first_name": "Test", "last_name": "User"}'

# Login (get session cookie)
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}' \
  -c cookies.txt

# Get current user
curl http://localhost:8000/api/auth/me/ \
  -b cookies.txt

# Create tenant
curl -X POST http://localhost:8000/api/tenants/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"name": "My Company", "slug": "my-company"}'
```

### Demo User (if created)

If you ran `setup_initial_data --demo`:

- **Email:** demo@example.com
- **Password:** demo1234
- **Tenant:** demo

## Common Commands

```bash
# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy apps

# Create superuser
python manage.py createsuperuser

# Reset database
python manage.py flush
python manage.py migrate
python manage.py setup_initial_data --demo

# View logs
docker compose logs -f

# Stop infrastructure
docker compose down

# Stop and remove all data
docker compose down -v
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
netstat -tulpn | grep :8000  # Linux
lsof -i :8000                # macOS
netstat -ano | findstr :8000 # Windows

# Kill process or use different port
python manage.py runserver 8001
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres
```

### Migration Errors

```bash
# Reset migrations (development only!)
python manage.py migrate apps_tenants zero
python manage.py migrate apps_authentication zero
# ... repeat for other apps

# Re-run migrations
python manage.py migrate
```

## Next Steps

1. **Explore the Admin Panel** - http://localhost:8000/admin/
2. **Read Module Documentation** - See README.md for architecture details
3. **Check API Endpoints** - http://localhost:8000/api/docs/
4. **Run Tests** - `pytest tests/` to see how modules are tested
5. **Customize** - Add your own modules following the patterns shown
