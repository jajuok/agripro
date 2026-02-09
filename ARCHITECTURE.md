# AgriScheme Pro - Architecture & Technology Stack

**Version:** 2.0.0
**Last Updated:** 2026-02-09
**Architecture:** Microservices with Unified API Gateway

---

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mobile Application                        │
│                   React Native + Expo (Android)                  │
│                  API URL: http://213.32.19.116:8888/api/v1      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Nginx API Gateway (Port 8888)                │
│          Unified Entry Point for External Access                 │
│     Routes requests to services via Docker network IPs           │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Auth Service │    │Farmer Service│    │  GIS Service │
│  10.0.1.28   │    │  10.0.1.41   │    │  10.0.1.34   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                    │
       └───────────────────┼────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  PostgreSQL Database    │
              │  (per-service schemas)  │
              └────────────────────────┘
```

---

## 📦 Technology Stack

### Frontend Layer

#### Mobile Application
- **Framework:** React Native 0.73
- **Build Tool:** Expo SDK 50
- **Language:** TypeScript
- **State Management:** Zustand
- **HTTP Client:** Axios
- **Navigation:** Expo Router (file-based routing)
- **UI Components:** React Native Paper
- **Maps:** React Native Maps
- **Platform:** Android (APK Release Build)

**Key Libraries:**
- `@react-navigation/native` - Navigation
- `expo-location` - GPS & Geolocation
- `expo-image-picker` - Camera & Gallery
- `expo-secure-store` - Secure token storage
- `react-native-maps` - Map visualization

### Backend Layer

#### API Gateway
- **Technology:** Nginx 1.29.5 (Alpine)
- **Port:** 8888
- **Network:** Docker bridge (coolify)
- **Routing:** Direct IP-based proxy to containers
- **Features:**
  - Path-based routing (`/api/v1/{service}/*`)
  - Health checks
  - Request forwarding with headers
  - Gzip compression
  - Access logging

#### Microservices (15 Services)

**Language:** Python 3.11
**Framework:** FastAPI
**ASGI Server:** Uvicorn
**Database ORM:** SQLAlchemy (AsyncIO)
**Migrations:** Alembic
**Dependency Manager:** uv (Astral)

**Services:**

| Service | Port | IP | Responsibilities |
|---------|------|-----|-----------------|
| **Auth** | 8000 | 10.0.1.28 | Authentication, Authorization, User Management |
| **Farmer** | 8000 | 10.0.1.41 | Farmer profiles, Farms, KYC, Documents |
| **GIS** | 8000 | 10.0.1.34 | Geospatial data, Mapping, Location services |
| **Financial** | 8000 | 10.0.1.42 | Loans, Payments, Financial transactions |
| **Market** | 8000 | 10.0.1.36 | Marketplace, Product listings |
| **AI** | 8000 | 10.0.1.58 | ML models, Predictions, Recommendations |
| **IoT** | 8000 | 10.0.1.40 | Sensor data, Device management |
| **Livestock** | 8000 | 10.0.1.33 | Livestock tracking, Health records |
| **Task** | 8000 | 10.0.1.37 | Task management, Scheduling |
| **Inventory** | 8000 | 10.0.1.29 | Stock management, Supplies |
| **Notification** | 8000 | 10.0.1.57 | Push notifications, Alerts, Messaging |
| **Traceability** | 8000 | 10.0.1.31 | Product tracing, Supply chain |
| **Compliance** | 8000 | 10.0.1.59 | Regulatory compliance, Certifications |
| **Integration** | 8000 | 10.0.1.39 | External API integrations |
| **Farm** | 8000 | 10.0.1.43 | Farm operations, Asset management |

### Data Layer

#### Primary Database
- **Technology:** PostgreSQL 16 (Alpine)
- **Deployment:** Dedicated instance per service
- **Schema Design:** Multi-tenant (tenant_id isolation)
- **Connection:** AsyncPG (Python async driver)
- **Pooling:** SQLAlchemy async connection pool

**Database Schemas:**
- `agrischeme_auth` - User accounts, roles, permissions
- `agrischeme_farmer` - Farmer profiles, farms, KYC data
- `agrischeme_gis` - Geospatial data, boundaries
- (Additional schemas per service)

#### Caching Layer (Future)
- Redis (planned for session storage, rate limiting)

### Infrastructure Layer

#### Container Platform
- **Technology:** Docker + Docker Compose
- **Orchestration:** Coolify v4.0.0-beta.462
- **Network:** Bridge network (`coolify`)
- **Registry:** GitHub Container Registry (ghcr.io)

#### Reverse Proxy
- **External:** Traefik v3.6 (coolify-proxy)
  - Handles port 80/443 for Coolify services
  - NOT used for our API gateway
- **Internal:** Nginx (agrischeme-nginx-gateway)
  - Dedicated gateway on port 8888
  - Direct container IP routing

#### CI/CD
- **Source Control:** GitHub (jajuok/agripro)
- **Deployment:** Coolify auto-deploy on push to main
- **Build:** Multi-stage Docker builds with uv
- **Health Checks:** curl-based HTTP checks

---

## 🔄 Request Flow

### External Request (Mobile App → Backend)

```
1. Mobile App makes request:
   POST http://213.32.19.116:8888/api/v1/auth/login

2. Request hits Nginx Gateway (port 8888)

3. Nginx matches location rule:
   location /api/v1/auth/ {
       proxy_pass http://10.0.1.28:8000/api/v1/auth/;
   }

4. Proxies to Auth Service container:
   POST http://10.0.1.28:8000/api/v1/auth/login

5. Auth Service processes request:
   - Validates credentials
   - Queries PostgreSQL database
   - Generates JWT tokens

6. Response flows back through Nginx to Mobile App
```

### Internal Service Communication (Service-to-Service)

```
Example: Farmer Service needs to validate user token

1. Farmer Service makes direct HTTP call:
   GET http://10.0.1.28:8000/api/v1/users/{id}

2. Auth Service responds with user data

Note: Services communicate directly via Docker network IPs
No gateway involved for internal communication
```

---

## 🚀 Deployment Architecture

### Server Environment
- **Provider:** VPS (213.32.19.116)
- **OS:** Ubuntu 22.04 LTS
- **Docker:** 24.x
- **Network:** 10.0.1.0/24 (Docker bridge)

### Container Orchestration
```yaml
# Example structure (simplified)
networks:
  coolify:
    external: true

services:
  auth-service:
    image: ghcr.io/jajuok/agripro/auth:latest
    networks:
      - coolify
    environment:
      - DATABASE_URL=postgresql+asyncpg://...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Health Monitoring
- **Gateway Health:** `http://213.32.19.116:8888/health`
- **Service Health:** Each service exposes `/health` endpoint
- **Coolify Integration:** Automatic health checks every 30s
- **Failure Handling:** Automatic container restart on unhealthy

---

## 🔐 Security Architecture

### Authentication Flow
1. User registers/logs in via mobile app
2. Credentials validated by Auth Service
3. JWT access token (30 min) + refresh token (7 days) issued
4. Mobile app stores tokens in Expo SecureStore
5. All subsequent requests include: `Authorization: Bearer {token}`

### Authorization
- Role-Based Access Control (RBAC)
- Roles: farmer, admin, agent, etc.
- Permissions checked at service level

### Network Security
- Services isolated on Docker network
- Only Nginx gateway exposed externally (port 8888)
- Coolify proxy handles SSL/TLS (future: HTTPS)
- Database not exposed externally

### Data Security
- Passwords hashed with bcrypt (version 3.2.2)
- JWT tokens signed with HS256
- Tenant isolation via tenant_id in database

---

## 📊 Data Models (Key Entities)

### Auth Service
- **User:** id, email, password_hash, first_name, last_name, phone
- **Role:** id, name, permissions
- **UserRole:** user_id, role_id (many-to-many)

### Farmer Service
- **Farmer:** id, user_id, national_id, date_of_birth
- **Farm:** id, farmer_id, name, location, size_hectares
- **KYC:** id, farmer_id, status, verification_data

### GIS Service
- **FarmBoundary:** id, farm_id, geometry (PostGIS)
- **Location:** id, latitude, longitude, altitude

---

## 🔧 Development Workflow

### Local Development
```bash
# Start individual service
cd services/auth
python -m uvicorn app.main:app --reload --port 9000

# Run migrations
alembic upgrade head

# Run tests
pytest
```

### Building Mobile App
```bash
cd apps/mobile
bash build-release.sh
adb install android/app/build/outputs/apk/release/app-release.apk
```

### Deployment
```bash
# Commit changes
git add .
git commit -m "feat: add new feature"
git push origin main

# Coolify auto-deploys on push
# Or manual redeploy via Coolify UI
```

---

## 📈 Scaling Considerations

### Current Limitations
- Single server deployment
- Container IPs hardcoded in nginx config
- No load balancing
- No horizontal scaling

### Future Improvements
1. **Service Discovery:** Use Docker DNS or Consul
2. **Load Balancing:** Multiple instances per service
3. **Database Scaling:** Read replicas, connection pooling
4. **Caching:** Redis for sessions, frequently accessed data
5. **Message Queue:** RabbitMQ/Kafka for async operations
6. **Monitoring:** Prometheus + Grafana
7. **Logging:** ELK stack (Elasticsearch, Logstash, Kibana)

---

## 🐛 Known Issues & Fixes

### Resolved in v2.0.0
- ✅ Bcrypt 4.x compatibility → Downgraded to 3.2.2
- ✅ Missing curl in Dockerfiles → Added to all 15 services
- ✅ FastAPI route ordering → Specific routes before generic
- ✅ sslip.io DNS resolution → Switched to direct container IPs
- ✅ Mobile app production mode detection → Prioritize unified gateway
- ✅ Alembic migration conflicts → Auto-stamp existing tables

### Current Limitations
- Container IPs are static (change on redeploy requires nginx update)
- No HTTPS (using HTTP on port 8888)
- No rate limiting
- No request caching

---

## 📝 Configuration Management

### Environment Variables

#### Mobile App (.env.production)
```bash
EXPO_PUBLIC_API_URL=http://213.32.19.116:8888/api/v1
```

#### Backend Services (example)
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/agrischeme_auth
DEBUG=false
LOG_LEVEL=INFO
JWT_SECRET_KEY=<secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 🎯 API Endpoint Structure

### Gateway Routes
```
http://213.32.19.116:8888/api/v1/

/auth/*              → Auth Service (10.0.1.28)
  /register          POST - User registration
  /login             POST - User authentication
  /logout            POST - Logout
  /refresh           POST - Refresh access token

/farmers/*           → Farmer Service (10.0.1.41)
  /                  GET  - List farmers
  /{farmer_id}       GET  - Get farmer details
  /by-user/{user_id} GET  - Get farmer by user ID

/farms/*             → Farmer Service (10.0.1.41)
  /                  POST - Create farm
  /{farm_id}         GET  - Get farm details
  /user/{user_id}    GET  - List user's farms
  /farmer/{farmer_id} GET  - List farmer's farms

/gis/*               → GIS Service (10.0.1.34)
  /reverse-geocode   POST - Get address from coordinates
  /boundaries        GET  - Get farm boundaries

/market/*            → Market Service (10.0.1.36)
/tasks/*             → Task Service (10.0.1.37)
/notifications/*     → Notification Service (10.0.1.57)
...
```

---

## 🔄 Version History

### v2.0.0 (2026-02-09) - Major Architectural Update
**Breaking Changes:**
- Switched from individual sslip.io URLs to unified API gateway
- Changed from Traefik routing to Nginx direct IP routing

**New Features:**
- ✅ Unified API Gateway on port 8888
- ✅ Direct container IP routing (no external DNS)
- ✅ Mobile app with single API endpoint
- ✅ Comprehensive health checks with curl
- ✅ Fixed FastAPI route ordering for /farms/user endpoint

**Bug Fixes:**
- Fixed bcrypt compatibility (downgraded to 3.2.2)
- Fixed Alembic migration conflicts with existing tables
- Fixed mobile app environment variable detection
- Fixed 404 errors on farms endpoints

**Infrastructure:**
- Added curl to all 15 service Dockerfiles
- Nginx gateway with direct IP proxy configuration
- Updated mobile app to prioritize unified gateway mode

### v1.0.0 (2026-02-03) - Initial Deployment
- 15 microservices deployed on Coolify
- Individual service exposure via Traefik
- Mobile app with multi-client architecture

---

## 📞 Support & Maintenance

### Monitoring
- **Gateway Status:** `curl http://213.32.19.116:8888/health`
- **Service Logs:** `docker logs <container-name>`
- **Gateway Logs:** `docker logs agrischeme-nginx-gateway`

### Common Operations

**Restart Gateway:**
```bash
docker restart agrischeme-nginx-gateway
```

**Check Service Health:**
```bash
curl http://10.0.1.41:8000/health  # Farmer service
```

**View Service Logs:**
```bash
docker logs fswk00skcko8wgkcs840o4ok-183545809290 -f
```

---

## 🎓 Key Architectural Decisions

### Why Nginx Gateway?
1. **Single Entry Point:** Simplified mobile app configuration
2. **Direct IP Routing:** Faster, no DNS overhead
3. **Independence:** Not reliant on Coolify's Traefik configuration
4. **Flexibility:** Easy to add SSL, rate limiting, caching

### Why Docker Network IPs?
1. **Reliability:** No dependency on external DNS (sslip.io)
2. **Performance:** Direct container-to-container communication
3. **Simplicity:** No complex Traefik label configuration

### Why Per-Service Databases?
1. **Isolation:** Service independence
2. **Scalability:** Can scale databases independently
3. **Security:** Tenant data segregation

---

**Document Version:** 2.0.0
**Last Modified:** 2026-02-09
**Maintained By:** AgriScheme Pro Development Team
