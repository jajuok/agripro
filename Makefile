.PHONY: help install dev test lint format build clean docker-up docker-down migrate

# Default target
help:
	@echo "AgriScheme Pro - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install all dependencies"
	@echo "  make dev            Start development environment"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run all tests"
	@echo "  make lint           Run linters"
	@echo "  make format         Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up      Start Docker services"
	@echo "  make docker-down    Stop Docker services"
	@echo "  make docker-logs    View Docker logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        Run database migrations"
	@echo "  make migrate-new    Create new migration"

# ===================
# Setup
# ===================
install:
	@echo "Installing Python dependencies..."
	cd services/auth && uv pip install -e ".[dev]"
	cd services/farmer && uv pip install -e ".[dev]"
	@echo "Installing Node.js dependencies..."
	yarn install
	@echo "Done!"

# ===================
# Development
# ===================
dev:
	@echo "Starting development environment..."
	docker compose up -d postgres redis
	@echo "Waiting for databases..."
	sleep 5
	@echo "Running services..."
	make -j2 dev-auth dev-farmer

dev-auth:
	cd services/auth && uvicorn app.main:app --reload --port 8000

dev-farmer:
	cd services/farmer && uvicorn app.main:app --reload --port 8001

dev-mobile:
	cd apps/mobile && npx expo start

# ===================
# Testing
# ===================
test:
	@echo "Running backend tests..."
	cd services/auth && pytest tests/ -v
	cd services/farmer && pytest tests/ -v
	@echo "Running mobile tests..."
	yarn workspace @agrischeme/mobile test

test-auth:
	cd services/auth && pytest tests/ -v --cov=app

test-farmer:
	cd services/farmer && pytest tests/ -v --cov=app

# ===================
# Linting & Formatting
# ===================
lint:
	@echo "Linting Python..."
	cd services/auth && ruff check app/
	cd services/farmer && ruff check app/
	@echo "Linting TypeScript..."
	yarn lint

format:
	@echo "Formatting Python..."
	cd services/auth && ruff format app/
	cd services/farmer && ruff format app/
	@echo "Formatting TypeScript..."
	yarn lint:fix

# ===================
# Docker
# ===================
docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-build:
	docker compose build

docker-clean:
	docker compose down -v --rmi local

# ===================
# Database
# ===================
migrate:
	cd services/auth && alembic upgrade head
	cd services/farmer && alembic upgrade head

migrate-new:
	@read -p "Service (auth/farmer): " service; \
	read -p "Migration message: " msg; \
	cd services/$$service && alembic revision --autogenerate -m "$$msg"

# ===================
# Build
# ===================
build:
	@echo "Building Docker images..."
	docker compose build
	@echo "Building mobile app..."
	cd apps/mobile && npx expo export --platform web

# ===================
# Clean
# ===================
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name node_modules -exec rm -rf {} +
	find . -type d -name .expo -exec rm -rf {} +
