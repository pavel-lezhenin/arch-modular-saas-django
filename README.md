# arch-modular-saas-django

Multi-tenant SaaS backend with Django modular monolith architecture

## 📦 Installation

```bash
# From GitHub
pip install git+https://github.com/yourname/arch-modular-saas-django.git

# For development
git clone https://github.com/yourname/arch-modular-saas-django.git
cd arch-modular-saas-django
pip install -e ".[dev]"
pre-commit install
```

## 🚀 Usage

```python
from arch_modular_saas_django import Client

async with Client() as client:
    result = await client.request()
```

## 🛠️ Development

```bash
ruff check .      # Linting
ruff format .     # Formatting
mypy src          # Type checking
pytest            # Tests
```

## 📋 Standards

- ✅ Strict typing (mypy strict)
- ✅ 80%+ test coverage
- ✅ Auto-formatting (ruff)
- ✅ Secret detection
