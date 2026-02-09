# Coolify UI - Microservices Deployment Guide

Complete guide for deploying AgriScheme Pro microservices through the Coolify web interface.

## Prerequisites

Before starting:

- ✅ Coolify is installed and accessible at `http://YOUR_IP:8000`
- ✅ PostgreSQL databases are deployed (10 containers)
- ✅ Redis and Kafka are running
- ✅ You have completed Coolify setup wizard

---

## Phase 1: Connect GitHub Repository

### Step 1: Add GitHub Source

1. Open Coolify UI: `http://213.32.19.116:8000`
2. Login with your admin account
3. Click on **Sources** in the left sidebar
4. Click **+ Add** button
5. Select **GitHub App**

### Step 2: Authorize GitHub

1. You'll be redirected to GitHub
2. Click **Install & Authorize**
3. Select your account/organization
4. Choose **Only select repositories**
5. Select: `jajuok/agripro`
6. Click **Install**

### Step 3: Verify Connection

Back in Coolify:

- You should see your GitHub connection listed
- Status should show as **Connected**

---

## Phase 2: Create Project

### Step 1: Create Infrastructure Project

1. Go to **Projects** in the left sidebar
2. Click **+ New Project**
3. Fill in details:
   - **Name:** `agrischeme-infra`
   - **Description:** `AgriScheme Pro Infrastructure and Services`
4. Click **Save**

### Step 2: Create Environment

1. Inside the project, click **+ New Environment**
2. Name: `production`
3. Click **Save**

---

## Phase 3: Deploy Services

You'll deploy 15 services. Here's the detailed process for each:

### Service List

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

## Detailed Deployment Steps (Repeat for Each Service)

### Example: Deploying Auth Service

#### Step 1: Create Application

1. Navigate to: **Projects** → **agrischeme-infra** → **production**
2. Click **+ New Resource**
3. Select **Application**
4. Choose **Public Repository** (or your connected GitHub source)

#### Step 2: Configure Repository

**Repository Settings:**

- **Repository:** `jajuok/agripro`
- **Branch:** `main`
- **Build Pack:** Dockerfile
- **Base Directory:** `services/auth`
- **Dockerfile Location:** `Dockerfile`

#### Step 3: Basic Configuration

**Application Settings:**

- **Name:** `auth-service`
- **Description:** `Authentication and authorization service`
- **Port:** `8000`
- **Domain:** Leave empty (for IP-only deployment)

#### Step 4: Add Environment Variables

Click on **Environment Variables** tab and add the following:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:P4fzWbXHbnODNUUKQkC1LbZy20ZMzNW6BKUSqozGnz8bbXS94peDj2WBoMb5N1oo@agrischeme-auth-db:5432/agrischeme_auth

# Redis Configuration
REDIS_URL=redis://:REDIS_PASSWORD@agrischeme-redis:6379/0

# JWT Configuration
JWT_SECRET_KEY=<from .secrets/deployment.secrets>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Service Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# CORS Configuration
CORS_ORIGINS=["*"]

# Service URLs (for inter-service communication)
FARMER_SERVICE_URL=http://farmer-service:8000
FARM_SERVICE_URL=http://farm-service:8000
```

#### Step 5: Deploy

1. Click **Save**
2. Click **Deploy**
3. Monitor the build logs in real-time
4. Wait for status to show **Running** and **Healthy**

---

## Environment Variables Reference

### Common Variables (All Services)

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
CORS_ORIGINS=["*"]
```

### Service-Specific Database URLs

**Note:** Replace `PASSWORD` with your actual password from `.secrets/deployment.secrets`

```bash
# Auth Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-auth-db:5432/agrischeme_auth

# Farmer Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-farmer-db:5432/agrischeme_farmer

# Farm Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-farm-db:5432/agrischeme_farm

# Financial Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-financial-db:5432/agrischeme_financial

# GIS Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-gis-db:5432/agrischeme_gis

# Market Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-market-db:5432/agrischeme_market

# AI Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-ai-db:5432/agrischeme_ai

# IoT Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-iot-db:5432/agrischeme_iot

# Livestock Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-livestock-db:5432/agrischeme_livestock

# Task Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-task-db:5432/agrischeme_task

# Inventory Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-inventory-db:5432/agrischeme_inventory

# Notification Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-notification-db:5432/agrischeme_notification

# Traceability Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-traceability-db:5432/agrischeme_traceability

# Compliance Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-compliance-db:5432/agrischeme_compliance

# Integration Service
DATABASE_URL=postgresql+asyncpg://agrischeme_admin:PASSWORD@agrischeme-integration-db:5432/agrischeme_integration
```

### Redis Configuration

```bash
REDIS_URL=redis://:REDIS_PASSWORD@agrischeme-redis:6379/0
```

**Note:** Replace `REDIS_PASSWORD` with the actual Redis password from `.secrets/deployment.secrets`

### Kafka Configuration

```bash
KAFKA_BOOTSTRAP_SERVERS=agrischeme-kafka:9092
```

---

## Quick Deployment Checklist

For each of the 15 services, follow this checklist:

### ✅ Auth Service

- [ ] Create application
- [ ] Set base directory: `services/auth`
- [ ] Configure DATABASE_URL for `agrischeme_auth`
- [ ] Add JWT secrets
- [ ] Deploy and verify

### ✅ Farmer Service

- [ ] Create application
- [ ] Set base directory: `services/farmer`
- [ ] Configure DATABASE_URL for `agrischeme_farmer`
- [ ] Deploy and verify

### ✅ Farm Service

- [ ] Create application
- [ ] Set base directory: `services/farm`
- [ ] Configure DATABASE_URL for `agrischeme_farm`
- [ ] Deploy and verify

### ✅ Financial Service

- [ ] Create application
- [ ] Set base directory: `services/financial`
- [ ] Configure DATABASE_URL for `agrischeme_financial`
- [ ] Deploy and verify

### ✅ GIS Service

- [ ] Create application
- [ ] Set base directory: `services/gis`
- [ ] Configure DATABASE_URL for `agrischeme_gis`
- [ ] Deploy and verify

### ✅ Market Service

- [ ] Create application
- [ ] Set base directory: `services/market`
- [ ] Configure DATABASE_URL for `agrischeme_market`
- [ ] Deploy and verify

### ✅ AI Service

- [ ] Create application
- [ ] Set base directory: `services/ai`
- [ ] Configure DATABASE_URL for `agrischeme_ai`
- [ ] Deploy and verify

### ✅ IoT Service

- [ ] Create application
- [ ] Set base directory: `services/iot`
- [ ] Configure DATABASE_URL for `agrischeme_iot`
- [ ] Deploy and verify

### ✅ Livestock Service

- [ ] Create application
- [ ] Set base directory: `services/livestock`
- [ ] Configure DATABASE_URL for `agrischeme_livestock`
- [ ] Deploy and verify

### ✅ Task Service

- [ ] Create application
- [ ] Set base directory: `services/task`
- [ ] Configure DATABASE_URL for `agrischeme_task`
- [ ] Deploy and verify

### ✅ Inventory Service

- [ ] Create application
- [ ] Set base directory: `services/inventory`
- [ ] Configure DATABASE_URL for `agrischeme_inventory`
- [ ] Deploy and verify

### ✅ Notification Service

- [ ] Create application
- [ ] Set base directory: `services/notification`
- [ ] Configure DATABASE_URL for `agrischeme_notification`
- [ ] Deploy and verify

### ✅ Traceability Service

- [ ] Create application
- [ ] Set base directory: `services/traceability`
- [ ] Configure DATABASE_URL for `agrischeme_traceability`
- [ ] Deploy and verify

### ✅ Compliance Service

- [ ] Create application
- [ ] Set base directory: `services/compliance`
- [ ] Configure DATABASE_URL for `agrischeme_compliance`
- [ ] Deploy and verify

### ✅ Integration Service

- [ ] Create application
- [ ] Set base directory: `services/integration`
- [ ] Configure DATABASE_URL for `agrischeme_integration`
- [ ] Deploy and verify

---

## Verification Steps

### Check Service Health

After deploying each service:

1. **In Coolify UI:**
   - Status should show green "Running"
   - Health check should show "Healthy"
   - Logs should show "Uvicorn running on..."

2. **Check Service Endpoint:**
   - Find the assigned port in Coolify UI
   - Test: `http://YOUR_IP:PORT/health`
   - Should return: `{"status": "healthy"}`

3. **Check Logs:**
   - Click on the service in Coolify
   - Go to **Logs** tab
   - Should see no errors
   - Look for: "Application startup complete"

---

## Common Issues & Solutions

### Issue: Build Failed

**Symptoms:**

- Build logs show errors
- Status shows "Failed"

**Solutions:**

1. Check the build logs for specific errors
2. Verify the base directory is correct
3. Ensure Dockerfile exists in the service directory
4. Check if dependencies are available

### Issue: Container Exits Immediately

**Symptoms:**

- Service starts but immediately stops
- Status cycles between "Starting" and "Exited"

**Solutions:**

1. Check application logs for errors
2. Verify DATABASE_URL is correct
3. Ensure database container is running
4. Check for missing environment variables

### Issue: Database Connection Failed

**Symptoms:**

- Logs show "Connection refused" or "No route to host"
- Service can't connect to database

**Solutions:**

1. Verify database container name is correct
2. Check if database is on the same Docker network
3. Ensure database is healthy: `docker ps | grep agrischeme-*-db`
4. Test database connection manually

### Issue: Port Already in Use

**Symptoms:**

- Error: "Port is already allocated"

**Solutions:**

1. Coolify auto-assigns ports, this shouldn't happen
2. If it does, go to service settings and clear the port field
3. Let Coolify auto-assign a new port

---

## Post-Deployment Tasks

### 1. Run Database Migrations

For each service with database migrations:

```bash
ssh ubuntu@213.32.19.116
docker exec -it <service-container> alembic upgrade head
```

Example:

```bash
docker exec -it auth-service alembic upgrade head
docker exec -it farmer-service alembic upgrade head
```

### 2. Test Service Communication

Test that services can communicate:

```bash
# Test auth service
curl http://213.32.19.116:PORT/health

# Test with authentication
curl -X POST http://213.32.19.116:PORT/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

### 3. Configure Mobile App

Update mobile app with service URLs:

```typescript
// apps/mobile/src/services/api.ts
const API_BASE_URL = "http://213.32.19.116";

// Service ports (check in Coolify UI for actual ports)
const AUTH_SERVICE_PORT = "<from Coolify>";
const FARMER_SERVICE_PORT = "<from Coolify>";
```

---

## Monitoring & Maintenance

### View All Services

In Coolify UI:

1. Go to **Projects** → **agrischeme-infra**
2. You should see all 15 services listed
3. All should show green "Running" status

### Check Resource Usage

```bash
ssh ubuntu@213.32.19.116
docker stats
```

### View Service Logs

In Coolify UI:

1. Click on any service
2. Go to **Logs** tab
3. Real-time logs will stream

Or via command line:

```bash
docker logs -f <service-name>
```

### Restart a Service

In Coolify UI:

1. Click on the service
2. Click **Restart** button
3. Wait for health check to pass

---

## Next Steps

After all services are deployed:

1. **✅ Configure API Gateway** (Optional)
   - Set up Traefik routing
   - Configure path-based routing

2. **✅ Set Up Monitoring**
   - Deploy Grafana
   - Configure Prometheus
   - Set up alerts

3. **✅ Configure Backups**
   - Set up database backup schedule
   - Configure backup retention

4. **✅ Update Mobile App**
   - Configure API endpoints
   - Test all features

5. **✅ Production Testing**
   - Test user registration/login
   - Test farmer workflows
   - Test all microservice endpoints

---

## Support

For issues:

- Check Coolify logs: **Service** → **Logs**
- Check container status: `docker ps`
- Check service health: `http://IP:PORT/health`
- GitHub Issues: https://github.com/jajuok/agripro/issues

---

**Estimated Time:** 2-3 hours for all 15 services

**Pro Tip:** Deploy and verify one service at a time. Don't move to the next until the current one is healthy and responding to health checks.
