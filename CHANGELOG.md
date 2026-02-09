# Changelog

All notable changes to AgriScheme Pro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-09

### 🚀 Major Changes

#### Added
- **Unified API Gateway** - Single entry point for all microservices on port 8888
- **Direct IP Routing** - Nginx proxies directly to container IPs (10.0.1.x)
- **Comprehensive Health Checks** - Added curl to all 15 service Dockerfiles
- **Architecture Documentation** - Detailed system architecture and tech stack docs
- **Version Tracking** - VERSION file and CHANGELOG for release management

#### Changed
- **Breaking:** Mobile app now uses unified gateway URL (`http://213.32.19.116:8888/api/v1`)
- **Breaking:** Nginx gateway routes directly to container IPs instead of sslip.io URLs
- Downgraded bcrypt from 4.x to 3.2.2 for passlib compatibility
- Reordered FastAPI routes in Farmer service (specific before generic)
- Mobile app mode detection now prioritizes unified gateway over production mode

#### Fixed
- **Auth Service**
  - Fixed bcrypt 4.x incompatibility causing login failures
  - Fixed Alembic migration conflicts when tables already exist
  - Added automatic database stamping for out-of-sync migrations
  - Added curl for Coolify healthchecks

- **Farmer Service**
  - Fixed route ordering: `/user/{id}` and `/farmer/{id}` now match before `/{farm_id}`
  - This resolved 404 errors on `/api/v1/farms/user/{user_id}` endpoint
  - Added curl for Coolify healthchecks

- **All Services (13 services)**
  - Added curl to Dockerfiles for healthcheck support
  - Services: ai, compliance, farm, financial, gis, integration, inventory, iot, livestock, market, notification, task, traceability

- **Mobile App**
  - Fixed environment variable detection logic
  - Removed old individual service URLs from .env file
  - Fixed API interceptor to respect unified gateway mode
  - Removed hardcoded sslip.io URLs from bundle

- **Gateway**
  - Fixed Docker DNS resolution issues with sslip.io URLs
  - Switched to direct container IP addressing
  - Fixed 404 errors for all service endpoints

### 🏗️ Architecture Changes

#### Before (v1.0.0)
```
Mobile App → Multiple sslip.io URLs → Traefik → Services
```

#### After (v2.0.0)
```
Mobile App → Nginx Gateway (8888) → Direct IP → Services
```

### 📝 Technical Details

#### Container IP Assignments
- Auth: 10.0.1.28
- Farmer: 10.0.1.41
- GIS: 10.0.1.34
- Financial: 10.0.1.42
- Market: 10.0.1.36
- AI: 10.0.1.58
- IoT: 10.0.1.40
- Livestock: 10.0.1.33
- Task: 10.0.1.37
- Inventory: 10.0.1.29
- Notification: 10.0.1.57
- Traceability: 10.0.1.31
- Compliance: 10.0.1.59
- Integration: 10.0.1.39
- Farm: 10.0.1.43

#### Deployment Platform
- **Coolify:** v4.0.0-beta.462
- **Docker Network:** coolify (bridge)
- **Proxy:** Traefik v3.6 (coolify-proxy) + Nginx (agrischeme-nginx-gateway)

### 🐛 Known Issues
- Container IPs are static; changing on redeploy requires nginx config update
- No HTTPS/SSL (using HTTP on port 8888)
- No rate limiting implemented
- No request caching layer

### 🔧 Commits in This Release
- `b98c68b` - fix(docker): add curl to all service Dockerfiles for healthchecks
- `5fada14` - fix(farmer): fix farms route ordering and add curl for healthchecks
- `c2c7e03` - fix(mobile): prioritize unified gateway over production mode
- `0e84e56` - feat(gateway): implement nginx API gateway on port 8888
- `1caaad1` - fix(gateway): use direct container IPs instead of sslip.io URLs
- `728604a` - fix(auth): handle migration conflicts with existing tables
- `7fe5ed3` - fix(auth): downgrade bcrypt to 3.2.2 for passlib compatibility

---

## [1.0.0] - 2026-02-03

### Added
- Initial deployment of 15 microservices on Coolify
- FastAPI backend services with PostgreSQL databases
- React Native mobile app with Expo
- Individual service exposure via Traefik
- Multi-tenant database architecture
- JWT authentication system

### Services Deployed
1. Auth Service - Authentication & authorization
2. Farmer Service - Farmer profiles & farms management
3. GIS Service - Geospatial services
4. Financial Service - Financial transactions
5. Market Service - Marketplace functionality
6. AI Service - ML models & predictions
7. IoT Service - Sensor data management
8. Livestock Service - Livestock tracking
9. Task Service - Task management
10. Inventory Service - Stock management
11. Notification Service - Push notifications
12. Traceability Service - Product tracing
13. Compliance Service - Regulatory compliance
14. Integration Service - External integrations
15. Farm Service - Farm operations

### Initial Features
- User registration and authentication
- Farmer profile management
- KYC (Know Your Customer) workflow
- Farm registration
- Document upload
- Basic mobile app navigation

---

## [Unreleased]

### Planned Features
- HTTPS/SSL certificate installation
- Rate limiting middleware
- Redis caching layer
- Horizontal service scaling
- Service discovery (replace hardcoded IPs)
- Load balancing
- Monitoring dashboard (Prometheus + Grafana)
- Centralized logging (ELK stack)
- Message queue (RabbitMQ/Kafka)
- API documentation (Swagger UI)
- Mobile app push notifications
- Offline mode support

### Under Consideration
- GraphQL API layer
- WebSocket support for real-time updates
- Multi-language support (i18n)
- Dark mode for mobile app
- Biometric authentication
- QR code scanning for traceability

---

[2.0.0]: https://github.com/jajuok/agripro/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/jajuok/agripro/releases/tag/v1.0.0
