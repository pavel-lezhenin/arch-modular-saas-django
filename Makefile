.PHONY: help install dev up down logs migrate setup test lint format typecheck check clean

PYTHON := python
MANAGE := $(PYTHON) manage.py

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv pip install -e ".[dev]"

dev:  ## Start development server
	$(MANAGE) runserver

up:  ## Start infrastructure (Docker)
	docker compose up -d

down:  ## Stop infrastructure
	docker compose down

down-v:  ## Stop infrastructure and remove volumes
	docker compose down -v

logs:  ## View Docker logs
	docker compose logs -f

migrate:  ## Run database migrations
	$(MANAGE) migrate

makemigrations:  ## Create new migrations
	$(MANAGE) makemigrations

setup:  ## Setup initial data (plans, features)
	$(MANAGE) setup_initial_data

setup-demo:  ## Setup initial data with demo tenant
	$(MANAGE) setup_initial_data --demo

superuser:  ## Create superuser
	$(MANAGE) createsuperuser

shell:  ## Open Django shell
	$(MANAGE) shell_plus

test:  ## Run all tests
	pytest

test-unit:  ## Run unit tests only
	pytest tests/unit -v

test-integration:  ## Run integration tests only
	pytest tests/integration -v

test-cov:  ## Run tests with coverage
	pytest --cov=apps --cov-report=html --cov-report=term

lint:  ## Run linting
	ruff check .

format:  ## Format code
	ruff format .

typecheck:  ## Run type checking
	mypy apps

check: lint typecheck test  ## Run all checks

clean:  ## Clean cache and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage*" -exec rm -f {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -exec rm -f {} + 2>/dev/null || true

reset-db:  ## Reset database (development only!)
	$(MANAGE) flush --no-input
	$(MANAGE) migrate
	$(MANAGE) setup_initial_data --demo --force
