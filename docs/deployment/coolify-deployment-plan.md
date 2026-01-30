# Coolify Deployment Plan for AgriScheme Pro

## Overview

This document outlines the deployment strategy for AgriScheme Pro using **Coolify**, an open-source, self-hosted PaaS (Platform-as-a-Service) alternative to Heroku/Vercel/Netlify.

---

## Project Summary

| Component | Technology | Count |
|-----------|------------|-------|
| Mobile App | React Native + Expo | 1 |
| Backend Services | Python FastAPI | 15 |
| Database | PostgreSQL 16 | 1 (multiple DBs) |
| Cache | Redis 7 | 1 |
| Message Broker | Kafka | 1 |

### Services to Deploy

1. auth-service
2. farmer-service
3. farm-service
4. financial-service
5. gis-service
6. market-service
7. ai-service
8. iot-service
9. livestock-service
10. task-service
11. inventory-service
12. notification-service
13. traceability-service
14. compliance-service
15. integration-service

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OVHcloud VPS/Dedicated                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        Coolify Instance                            │  │
│  │                                                                    │  │
│  │  ┌──────────────────────────────────────────────────────────────┐ │  │
│  │  │                   Application Services                        │ │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │  │
│  │  │  │auth-service │  │farmer-service│ │ farm-service│          │ │  │
│  │  │  │   :8000     │  │    :8001    │  │    :8002    │          │ │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │ │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │  │
│  │  │  │ gis-service │  │market-service│ │financial-svc│          │ │  │
│  │  │  │   :8003     │  │    :8004    │  │    :8005    │          │ │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │ │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │  │
│  │  │  │ ai-service  │  │ iot-service │  │livestock-svc│          │ │  │
│  │  │  │   :8006     │  │    :8007    │  │    :8008    │          │ │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │ │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │  │
│  │  │  │ task-service│  │inventory-svc│  │notification │          │ │  │
│  │  │  │   :8009     │  │    :8010    │  │    :8011    │          │ │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │ │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │  │
│  │  │  │traceability │  │compliance-svc│ │integration  │          │ │  │
│  │  │  │   :8012     │  │    :8013    │  │    :8014    │          │ │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │ │  │
│  │  └──────────────────────────────────────────────────────────────┘ │  │
│  │                                                                    │  │
│  │  ┌──────────────────────────────────────────────────────────────┐ │  │
│  │  │                   Infrastructure Services                     │ │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │  │
│  │  │  │ PostgreSQL  │  │    Redis    │  │    Kafka    │          │ │  │
│  │  │  │    :5432    │  │    :6379    │  │    :9092    │          │ │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │ │  │
│  │  └──────────────────────────────────────────────────────────────┘ │  │
│  │                                                                    │  │
│  │  ┌──────────────────────────────────────────────────────────────┐ │  │
│  │  │              Traefik Reverse Proxy (Built-in)                 │ │  │
│  │  │           Auto SSL via Let's Encrypt + Load Balancing         │ │  │
│  │  └──────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │     Mobile App (Expo)         │
                    │  Connects via HTTPS APIs      │
                    └───────────────────────────────┘
```

---

## Server Requirements

### Minimum Specifications (Development/Staging)

| Resource | Specification |
|----------|---------------|
| CPU | 4 vCPUs |
| RAM | 8 GB |
| Storage | 100 GB SSD |
| OS | Ubuntu 22.04 LTS |
| Estimated Cost | ~€30-50/month |

### Recommended Specifications (Production)

| Resource | Specification |
|----------|---------------|
| CPU | 8 vCPUs |
| RAM | 16-32 GB |
| Storage | 200-500 GB NVMe SSD |
| OS | Ubuntu 22.04 LTS |
| Estimated Cost | ~€80-150/month |

### OVHcloud Server Options

| Server Type | vCPUs | RAM | Storage | Price/Month |
|-------------|-------|-----|---------|-------------|
| VPS Comfort | 4 | 8 GB | 160 GB | ~€26 |
| VPS Elite | 8 | 16 GB | 320 GB | ~€52 |
| Dedicated Essential | 8 | 32 GB | 500 GB | ~€90 |

---

## Implementation Plan

### Phase 1: Server & Coolify Setup (Day 1)

#### Step 1.1: Provision OVHcloud Server

1. Log in to OVHcloud Control Panel
2. Navigate to **Bare Metal Cloud** → **Virtual Private Servers**
3. Select region (recommended: **Gravelines** or **Strasbourg** for EU)
4. Choose **VPS Elite** or higher
5. Select **Ubuntu 22.04 LTS**
6. Configure SSH keys
7. Complete purchase

#### Step 1.2: Initial Server Configuration

```bash
# Connect to server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y curl wget git

# Configure firewall
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

#### Step 1.3: Install Coolify

```bash
# One-line installation
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

After installation:
- Access Coolify UI at `http://your-server-ip:8000`
- Create admin account
- Complete initial setup wizard

#### Step 1.4: Configure Domain & DNS

1. **Add DNS Records** (in your domain registrar):

```
Type    Name                    Value               TTL
A       coolify                 your-server-ip      300
A       api                     your-server-ip      300
A       auth                    your-server-ip      300
A       *.api                   your-server-ip      300
CNAME   www                     @                   300
```

2. **Configure in Coolify**:
   - Go to **Settings** → **Configuration**
   - Set instance domain: `coolify.yourdomain.com`
   - Enable **Auto SSL** via Let's Encrypt

---

### Phase 2: Infrastructure Services (Day 2)

#### Step 2.1: Deploy PostgreSQL

1. In Coolify, go to **Projects** → **Create New Project** → Name: `agrischeme-infra`
2. Click **+ New** → **Database** → **PostgreSQL**
3. Configure:
   - **Name**: `agrischeme-postgres`
   - **Version**: `16-alpine`
   - **Default Database**: `agrischeme_auth`
   - **Username**: `agrischeme_admin`
   - **Password**: (generate secure password)
4. Click **Deploy**

5. **Create additional databases** (connect via terminal or GUI):

```sql
CREATE DATABASE agrischeme_farmer;
CREATE DATABASE agrischeme_farm;
CREATE DATABASE agrischeme_financial;
CREATE DATABASE agrischeme_gis;
CREATE DATABASE agrischeme_market;
CREATE DATABASE agrischeme_ai;
CREATE DATABASE agrischeme_iot;
CREATE DATABASE agrischeme_livestock;
CREATE DATABASE agrischeme_task;
CREATE DATABASE agrischeme_inventory;
CREATE DATABASE agrischeme_notification;
CREATE DATABASE agrischeme_traceability;
CREATE DATABASE agrischeme_compliance;
CREATE DATABASE agrischeme_integration;
```

#### Step 2.2: Deploy Redis

1. In `agrischeme-infra` project, click **+ New** → **Database** → **Redis**
2. Configure:
   - **Name**: `agrischeme-redis`
   - **Version**: `7-alpine`
   - **Password**: (generate secure password)
3. Click **Deploy**

#### Step 2.3: Deploy Kafka (via Docker Compose)

1. Click **+ New** → **Docker Compose**
2. Name: `agrischeme-kafka`
3. Paste the following:

```yaml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    volumes:
      - kafka-data:/var/lib/kafka/data

volumes:
  zookeeper-data:
  kafka-data:
```

4. Click **Deploy**

---

### Phase 3: Deploy Microservices (Days 3-5)

#### Step 3.1: Connect GitHub Repository

1. Go to **Sources** → **Add GitHub App**
2. Authorize Coolify to access your repository
3. Select `agripro` repository

#### Step 3.2: Create Application Project

1. Create new project: `agrischeme-services`
2. Create environment: `production`

#### Step 3.3: Deploy Each Service

Repeat for each service (auth, farmer, farm, etc.):

1. Click **+ New** → **Application** → **GitHub**
2. Select repository and branch (`main`)
3. Configure:

**Auth Service Example:**

| Setting | Value |
|---------|-------|
| **Name** | `auth-service` |
| **Build Pack** | Dockerfile |
| **Base Directory** | `services/auth` |
| **Dockerfile Location** | `Dockerfile` |
| **Domain** | `auth.api.yourdomain.com` |
| **Port** | `8000` |
| **Health Check Path** | `/health` |

4. **Add Environment Variables**:

```env
# Database
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-postgres:5432/agrischeme_auth

# Redis
REDIS_URL=redis://:PASSWORD@agrischeme-redis:6379/0

# JWT Configuration
JWT_SECRET_KEY=your-secure-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Service Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://yourdomain.com"]
```

5. Click **Deploy**

#### Service Configuration Reference

| Service | Base Directory | Port | Domain | Database |
|---------|---------------|------|--------|----------|
| auth-service | `services/auth` | 8000 | auth.api.yourdomain.com | agrischeme_auth |
| farmer-service | `services/farmer` | 8000 | farmer.api.yourdomain.com | agrischeme_farmer |
| farm-service | `services/farm` | 8000 | farm.api.yourdomain.com | agrischeme_farm |
| financial-service | `services/financial` | 8000 | financial.api.yourdomain.com | agrischeme_financial |
| gis-service | `services/gis` | 8000 | gis.api.yourdomain.com | agrischeme_gis |
| market-service | `services/market` | 8000 | market.api.yourdomain.com | agrischeme_market |
| ai-service | `services/ai` | 8000 | ai.api.yourdomain.com | agrischeme_ai |
| iot-service | `services/iot` | 8000 | iot.api.yourdomain.com | agrischeme_iot |
| livestock-service | `services/livestock` | 8000 | livestock.api.yourdomain.com | agrischeme_livestock |
| task-service | `services/task` | 8000 | task.api.yourdomain.com | agrischeme_task |
| inventory-service | `services/inventory` | 8000 | inventory.api.yourdomain.com | agrischeme_inventory |
| notification-service | `services/notification` | 8000 | notification.api.yourdomain.com | agrischeme_notification |
| traceability-service | `services/traceability` | 8000 | traceability.api.yourdomain.com | agrischeme_traceability |
| compliance-service | `services/compliance` | 8000 | compliance.api.yourdomain.com | agrischeme_compliance |
| integration-service | `services/integration` | 8000 | integration.api.yourdomain.com | agrischeme_integration |

---

### Phase 4: Database Migrations (Day 5)

Run Alembic migrations for each service:

```bash
# SSH into Coolify server
ssh root@your-server-ip

# Execute migration in auth-service container
docker exec -it auth-service alembic upgrade head

# Repeat for each service
docker exec -it farmer-service alembic upgrade head
docker exec -it farm-service alembic upgrade head
# ... etc.
```

Or configure a **post-deployment hook** in Coolify:

```bash
#!/bin/bash
alembic upgrade head
```

---

### Phase 5: API Gateway Setup (Day 6)

#### Option A: Use Traefik (Built-in)

Coolify uses Traefik by default. Configure path-based routing:

```yaml
# In each service's Traefik labels (via Coolify UI)
- traefik.http.routers.auth.rule=Host(`api.yourdomain.com`) && PathPrefix(`/auth`)
- traefik.http.routers.farmer.rule=Host(`api.yourdomain.com`) && PathPrefix(`/farmer`)
```

#### Option B: Deploy Kong/Nginx API Gateway

1. Create new Docker Compose application in Coolify
2. Deploy Kong or Nginx as central API gateway
3. Route `/api/v1/auth/*` → auth-service
4. Route `/api/v1/farmer/*` → farmer-service
5. etc.

---

### Phase 6: Mobile App Configuration (Day 6)

#### Step 6.1: Update API Configuration

Edit `apps/mobile/src/services/api.ts`:

```typescript
const API_BASE_URL = __DEV__
  ? 'http://localhost:9000'
  : 'https://api.yourdomain.com';
```

Or use environment variables in `app.json`:

```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://api.yourdomain.com"
    }
  }
}
```

#### Step 6.2: Build Production App

```bash
# Install EAS CLI
npm install -g eas-cli

# Configure EAS
eas build:configure

# Build for production
eas build --platform all --profile production
```

---

### Phase 7: Monitoring & Observability (Day 7)

#### Step 7.1: Deploy Prometheus & Grafana via Coolify

1. Create project: `agrischeme-monitoring`
2. Deploy **Prometheus**:
   - Use Docker Compose with your existing `infrastructure/docker/prometheus.yml`
3. Deploy **Grafana**:
   - Use Coolify's built-in Grafana option
   - Configure Prometheus as data source

#### Step 7.2: Configure Service Metrics

Each FastAPI service already has OpenTelemetry configured. Update environment variables:

```env
OTEL_EXPORTER_OTLP_ENDPOINT=http://prometheus:9090
OTEL_SERVICE_NAME=auth-service
```

---

## Auto-Deployment Configuration

### GitHub Webhooks (Automatic)

Coolify automatically configures GitHub webhooks. On every push to `main`:

1. Coolify receives webhook
2. Pulls latest code
3. Builds Docker image
4. Deploys with zero-downtime
5. Runs health checks
6. Routes traffic to new container

### Branch Preview Deployments

Enable preview deployments in Coolify:

1. Go to Application → **Settings**
2. Enable **Preview Deployments**
3. Each PR gets a unique URL: `pr-123.auth.api.yourdomain.com`

---

## Backup Strategy

### Database Backups

Configure in Coolify:

1. Go to **PostgreSQL** → **Backups**
2. Enable **Scheduled Backups**
3. Set schedule: Daily at 2:00 AM
4. Retention: 7 days
5. Optional: Configure S3-compatible storage for off-site backups

### Application Backups

Coolify stores:
- Docker volumes
- Environment variables
- Configuration

Export via:
```bash
# SSH to server
cd /data/coolify
tar -czvf coolify-backup-$(date +%Y%m%d).tar.gz .
```

---

## Security Checklist

- [ ] SSH key authentication only (disable password auth)
- [ ] Firewall configured (UFW)
- [ ] SSL certificates active (Let's Encrypt)
- [ ] Database passwords are strong (32+ characters)
- [ ] JWT secrets are secure
- [ ] Environment variables not exposed
- [ ] Regular security updates (`unattended-upgrades`)
- [ ] Fail2ban installed for brute-force protection
- [ ] Database not exposed publicly (internal network only)

---

## Benefits of Coolify Approach

| Benefit | Description |
|---------|-------------|
| **Self-Hosted** | Full control over infrastructure, no vendor lock-in |
| **Cost Effective** | Single VPS (~€50-100/mo) vs. multiple cloud services |
| **Data Sovereignty** | Data stays in EU (GDPR compliance) |
| **Automatic SSL** | Let's Encrypt integration, zero configuration |
| **Git Integration** | Auto-deploy on push, branch previews |
| **Built-in Databases** | PostgreSQL, Redis, MongoDB one-click setup |
| **Docker Native** | Uses existing Dockerfiles, no changes needed |
| **Zero-Downtime Deploys** | Rolling updates with health checks |
| **Monitoring** | Built-in logs, metrics, and container health |
| **Rollbacks** | One-click rollback to previous deployments |
| **Secrets Management** | Encrypted environment variable storage |
| **Team Access** | Multi-user support with role-based permissions |
| **Simple UI** | No Kubernetes complexity, intuitive interface |

---

## Cost Comparison

| Approach | Monthly Cost (Est.) |
|----------|---------------------|
| **Coolify on OVHcloud VPS** | €50-100 |
| **AWS (ECS + RDS + ElastiCache)** | €300-500 |
| **Heroku (15 dynos + addons)** | €400-700 |
| **Render/Railway** | €200-400 |

**Coolify provides 70-80% cost savings** compared to managed PaaS alternatives.

---

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
docker logs auth-service

# Check resource usage
docker stats
```

**Database connection failed:**
- Verify DATABASE_URL is correct
- Check PostgreSQL is running
- Ensure service is on same Docker network

**SSL certificate not working:**
- Verify DNS is pointing to server
- Check Traefik logs: `docker logs coolify-proxy`
- Wait for DNS propagation (up to 48 hours)

**Out of memory:**
- Upgrade server RAM
- Add swap space:
  ```bash
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  ```

---

## Next Steps

1. [ ] Provision OVHcloud server
2. [ ] Install Coolify
3. [ ] Configure DNS
4. [ ] Deploy infrastructure services (PostgreSQL, Redis, Kafka)
5. [ ] Deploy all 15 microservices
6. [ ] Run database migrations
7. [ ] Configure API gateway routing
8. [ ] Update mobile app API endpoints
9. [ ] Set up monitoring (Prometheus + Grafana)
10. [ ] Configure automated backups
11. [ ] Security hardening
12. [ ] Production testing
13. [ ] Go live!

---

## Resources

- [Coolify Documentation](https://coolify.io/docs)
- [OVHcloud VPS Guide](https://docs.ovh.com/gb/en/vps/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

*Document created: January 2026*
*Last updated: January 2026*
