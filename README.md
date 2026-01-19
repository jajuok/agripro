# AgriScheme Pro

A comprehensive Farm Management Information System (FMIS) designed to digitize, centralize, and optimize agricultural scheme operations.

## Architecture

```
agrischeme-pro/
├── apps/
│   └── mobile/          # React Native + Expo mobile app
├── services/
│   ├── auth/            # Authentication & Authorization
│   ├── farmer/          # Farmer Onboarding & KYC
│   ├── farm/            # Farm Profile Management
│   ├── financial/       # Financial & Compliance
│   └── ...              # Other microservices
├── packages/            # Shared packages
├── infrastructure/
│   ├── kubernetes/      # K8s manifests
│   ├── terraform/       # Infrastructure as Code
│   └── docker/          # Docker configs
└── docs/                # Documentation
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0
- **Mobile**: React Native, Expo, TypeScript
- **Database**: PostgreSQL 16, Redis 7
- **Infrastructure**: Kubernetes, Docker, Terraform
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- uv (Python package manager)
- Yarn 4.x

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/agrischeme-pro.git
   cd agrischeme-pro
   ```

2. **Copy environment variables**
   ```bash
   cp .env.example .env
   ```

3. **Start development environment**
   ```bash
   make docker-up  # Start databases
   make install    # Install dependencies
   make dev        # Start services
   ```

4. **Start mobile app** (in a new terminal)
   ```bash
   make dev-mobile
   ```

### Development Commands

```bash
# Setup
make install        # Install all dependencies
make dev            # Start development servers

# Testing
make test           # Run all tests
make test-auth      # Test auth service only

# Linting
make lint           # Run linters
make format         # Format code

# Docker
make docker-up      # Start Docker services
make docker-down    # Stop Docker services
make docker-logs    # View logs

# Database
make migrate        # Run migrations
make migrate-new    # Create new migration
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Auth | 8000 | Authentication, Authorization, User Management |
| Farmer | 8001 | Farmer Onboarding, KYC, Farm Profiles |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache, sessions |
| Grafana | 3001 | Monitoring dashboards |
| Prometheus | 9090 | Metrics collection |

## API Documentation

When running locally, API docs are available at:
- Auth Service: http://localhost:8000/docs
- Farmer Service: http://localhost:8001/docs

## Mobile App

The mobile app is built with Expo and supports:
- iOS
- Android
- Web (PWA)

```bash
cd apps/mobile
npx expo start
```

## Deployment

### Staging
Push to `main` branch triggers automatic deployment to staging.

### Production
Use the manual workflow dispatch in GitHub Actions.

## Project Structure

### Backend Services
Each service follows the same structure:
```
services/auth/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Config, security, database
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   └── utils/         # Utilities
├── tests/             # Test files
├── migrations/        # Alembic migrations
├── Dockerfile
└── pyproject.toml
```

### Mobile App
```
apps/mobile/
├── app/               # Expo Router pages
│   ├── (auth)/        # Auth screens
│   └── (tabs)/        # Main app tabs
├── src/
│   ├── components/    # Reusable components
│   ├── hooks/         # Custom hooks
│   ├── services/      # API services
│   ├── store/         # Zustand stores
│   └── utils/         # Utilities
└── assets/            # Images, fonts
```

## License

Proprietary - All rights reserved
