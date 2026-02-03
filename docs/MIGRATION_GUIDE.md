# Migration Guide: From Multi-Endpoint to API Gateway

This guide explains how to migrate from the old multi-endpoint architecture to the new unified API gateway architecture.

## Architecture Changes

### Before (Old Architecture)

```
Mobile App
├── Auth Client     → http://server:9001/api/v1
├── Farmer Client   → http://server:9002/api/v1
├── GIS Client      → http://server:9003/api/v1
├── Financial Client → http://server:9004/api/v1
└── ... (15 different endpoints)

Services
├── auth-service (port 9001)
├── farmer-service (port 9002)
├── gis-service (port 9003)
└── ... (each with separate port/subdomain)

Internal Communication
├── Services use DNS hostnames
├── Example: agrischeme-auth-db
└── Prone to DNS resolution errors
```

**Problems:**
- 15+ different API endpoints to manage
- Complex mobile app configuration
- DNS resolution failures (`gaierror`)
- No unified security/rate limiting
- Port management complexity

### After (New Architecture)

```
Mobile App
└── Single API Client → http://server/api/v1

Traefik API Gateway (port 80/443)
├── /api/v1/auth/*     → auth-service:9000
├── /api/v1/farmers/*  → farmer-service:9001
├── /api/v1/gis/*      → gis-service:8000
└── ... (path-based routing)

Services (on Docker network)
├── auth-service (internal port 9000)
├── farmer-service (internal port 9001)
└── ... (not exposed externally)

Internal Communication
├── Docker container names
├── Example: postgres:5432, auth-service:9000
└── Fast, reliable Docker DNS
```

**Benefits:**
- Single API endpoint
- Simplified configuration
- No DNS dependency issues
- Centralized security
- Easy service addition

## Migration Steps

### Phase 1: Infrastructure Changes

#### 1.1 Update Docker Compose

The `docker-compose.yml` has been updated with:

1. **Traefik service** added
2. **Service labels** for routing
3. **Health checks** for all services
4. **Network configuration** standardized
5. **Database names** updated

**No action needed** - changes already implemented.

#### 1.2 Database Configuration

**Old:**
```yaml
DATABASE_URL: postgresql+asyncpg://postgres:postgres@agrischeme-auth-db:5432/agrischeme_auth
```

**New:**
```yaml
DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/agrischeme_auth
```

**Action:** Environment variables in `docker-compose.yml` already updated.

### Phase 2: Service Configuration

#### 2.1 Service-to-Service Communication

**Old approach:**
```python
# services/farmer/app/core/config.py
auth_service_url: str = "http://agrischeme-auth:9000"  # DNS hostname
```

**New approach:**
```python
# services/farmer/app/core/config.py
auth_service_url: str = "http://auth-service:9000"  # Container name
```

**Action:** Already configured in `docker-compose.yml` environment variables.

#### 2.2 Service URLs

All services now use Docker container names:

- `postgres:5432` (not `agrischeme-postgres` or DNS hostname)
- `redis:6379` (not `agrischeme-redis`)
- `auth-service:9000` (not external URL)
- `farmer-service:9001` (not external URL)

### Phase 3: Mobile App Migration

#### 3.1 API Client Refactoring

**Old code:**
```typescript
// Multiple API clients
const AUTH_API_URL = buildApiUrl(9001);
const FARMER_API_URL = buildApiUrl(9002);
const GIS_API_URL = buildApiUrl(9003);

export const apiClient = axios.create({ baseURL: AUTH_API_URL });
export const farmerClient = axios.create({ baseURL: FARMER_API_URL });
export const gisClient = axios.create({ baseURL: GIS_API_URL });
```

**New code:**
```typescript
// Single unified client
const API_GATEWAY_URL = buildApiGatewayUrl();
export const apiClient = axios.create({ baseURL: API_GATEWAY_URL });
export const farmerClient = apiClient;  // Alias for compatibility
```

**Action:** Already updated in `apps/mobile/src/services/api.ts`.

#### 3.2 Environment Variables

**Old `.env.production`:**
```env
EXPO_PUBLIC_AUTH_API_URL=http://subdomain1.server.sslip.io/api/v1
EXPO_PUBLIC_FARMER_API_URL=http://subdomain2.server.sslip.io/api/v1
EXPO_PUBLIC_GIS_API_URL=http://subdomain3.server.sslip.io/api/v1
# ... (15 different URLs)
```

**New `.env.production`:**
```env
EXPO_PUBLIC_API_URL=http://213.32.19.116/api/v1
```

**Action:** Already updated in `apps/mobile/.env.production`.

#### 3.3 API Method Calls

No changes needed! API methods remain the same:

```typescript
// Auth API - still works
authApi.login(email, password);
authApi.register(data);

// Farmer API - still works
farmerApi.getProfile(farmerId);
farmApi.list(userId);

// GIS API - still works
gisApi.reverseGeocode(lat, lng);
```

The only difference is they all now route through the gateway.

### Phase 4: Deployment Migration

#### 4.1 Local Development

**Old workflow:**
```bash
# Start services
docker-compose up -d

# Each service accessible on different port
curl http://localhost:9001/api/v1/auth/health
curl http://localhost:9002/api/v1/farmers/health
```

**New workflow:**
```bash
# Start services (includes Traefik)
docker-compose up -d

# All services accessible through gateway
curl http://localhost/api/v1/auth/health
curl http://localhost/api/v1/farmers/health

# Traefik dashboard
open http://localhost:8080
```

#### 4.2 Production Deployment

**Old deployment:**
```bash
# Deploy each service separately
./deploy-service.sh auth 9001
./deploy-service.sh farmer 9002
./deploy-service.sh gis 9003
# ... repeat for all services

# Configure DNS for each subdomain
```

**New deployment:**
```bash
# Deploy all services at once
docker-compose up -d

# Or use deployment script
./scripts/deploy/deploy-with-gateway.sh

# Configure DNS for single domain (optional)
```

#### 4.3 Coolify Configuration

**Changes needed:**

1. **Remove individual service subdomains**
   - Old: Each service had separate subdomain
   - New: All services behind Traefik, not exposed directly

2. **Configure Traefik service**
   - Add Traefik as a service in Coolify
   - Expose port 80 (and 443 for SSL)
   - Point domain to Traefik

3. **Update environment variables**
   - Services use container names for internal communication
   - No external URLs needed

### Phase 5: Testing Migration

#### 5.1 Pre-Migration Checklist

Before migrating:

- [ ] Backup current database
- [ ] Document current service URLs
- [ ] Test current mobile app functionality
- [ ] Export environment variables
- [ ] Snapshot current Coolify configuration

#### 5.2 Migration Testing

1. **Test locally first:**
   ```bash
   docker-compose up -d
   # Run comprehensive tests
   ./comprehensive-test.sh
   ```

2. **Test mobile app:**
   ```bash
   cd apps/mobile
   expo start
   # Test registration, login, data fetching
   ```

3. **Test service communication:**
   ```bash
   docker exec -it agrischeme-farmer bash
   curl http://auth-service:9000/health
   ```

#### 5.3 Post-Migration Checklist

After migration:

- [ ] All services healthy: `docker-compose ps`
- [ ] Traefik dashboard accessible: `http://server:8080`
- [ ] Health checks pass: `curl http://server/api/v1/*/health`
- [ ] Registration works through gateway
- [ ] Login works through gateway
- [ ] Mobile app connects successfully
- [ ] No DNS resolution errors in logs
- [ ] Service-to-service communication works

### Phase 6: Rollback Plan

If issues arise, you can rollback:

#### Option 1: Keep Old Ports Exposed

The new configuration still exposes individual service ports:

```yaml
auth-service:
  ports:
    - "9000:9000"  # Still accessible directly
```

This means:
- Gateway route: `http://server/api/v1/auth/health` ✓
- Direct access: `http://server:9000/health` ✓ (fallback)

#### Option 2: Revert Mobile App

Keep the old mobile app version while fixing gateway issues:

```typescript
// Temporarily switch back
const API_URL = process.env.EXPO_PUBLIC_AUTH_API_URL || 'http://old-server:9001/api/v1';
```

#### Option 3: Full Rollback

```bash
# Revert docker-compose.yml
git checkout HEAD~1 docker-compose.yml

# Restart services
docker-compose up -d

# Revert mobile app
cd apps/mobile
git checkout HEAD~1 .env.production src/services/api.ts
```

### Phase 7: Optimization (Post-Migration)

Once migration is successful, optimize:

#### 7.1 Remove Direct Port Exposure

After confirming gateway works, remove individual port mappings:

```yaml
# Before
auth-service:
  ports:
    - "9000:9000"

# After (only gateway exposes services)
auth-service:
  # No ports section - only accessible via gateway
  expose:
    - "9000"
```

#### 7.2 Enable HTTPS

Configure Let's Encrypt:

```yaml
# traefik.yml
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@agrischeme.com
      storage: /acme.json
      httpChallenge:
        entryPoint: web
```

Update service labels:

```yaml
labels:
  - "traefik.http.routers.auth.tls=true"
  - "traefik.http.routers.auth.tls.certresolver=letsencrypt"
```

#### 7.3 Add Rate Limiting

```yaml
labels:
  - "traefik.http.middlewares.rate-limit.ratelimit.average=100"
  - "traefik.http.middlewares.rate-limit.ratelimit.burst=50"
  - "traefik.http.routers.auth.middlewares=rate-limit"
```

#### 7.4 Add Authentication Middleware

```yaml
labels:
  # Require JWT validation at gateway level
  - "traefik.http.middlewares.auth-check.forwardauth.address=http://auth-service:9000/validate"
```

## Timeline

Recommended migration timeline:

### Week 1: Preparation
- Day 1-2: Review implementation
- Day 3-4: Local testing
- Day 5: Mobile app testing

### Week 2: Staging Deployment
- Day 1: Deploy to staging
- Day 2-3: Integration testing
- Day 4: Performance testing
- Day 5: Fix issues

### Week 3: Production Deployment
- Day 1: Deploy to production
- Day 2-3: Monitor closely
- Day 4: Mobile app release
- Day 5: Optimization

## Support and Troubleshooting

### Common Migration Issues

#### Issue 1: DNS Resolution Errors

**Symptom:** `gaierror: Name or service not known`

**Fix:**
```bash
# Check service is on correct network
docker inspect agrischeme-auth | grep NetworkMode

# Should be: agrischeme-network

# Recreate service
docker-compose up -d --force-recreate auth-service
```

#### Issue 2: Gateway 404 Errors

**Symptom:** Traefik returns 404 for valid routes

**Fix:**
```bash
# Check Traefik config
docker logs agrischeme-traefik | grep router

# Restart Traefik
docker-compose restart traefik

# Verify labels
docker inspect agrischeme-auth | grep -A 20 Labels
```

#### Issue 3: Mobile App Connection Failures

**Symptom:** Network request failed

**Fix:**
```typescript
// Verify URL in app
console.log('API_GATEWAY_URL:', API_GATEWAY_URL);

// Check reachability
curl http://server/api/v1/auth/health

// Test from device browser
// http://server/api/v1/auth/health
```

## Conclusion

The migration to API gateway architecture provides:

✅ **Simplified architecture** - One endpoint instead of 15+
✅ **Better reliability** - No DNS resolution issues
✅ **Easier deployment** - Single gateway configuration
✅ **Better security** - Centralized authentication/rate limiting
✅ **Future-ready** - Easy to add SSL, monitoring, caching

All implementation is complete and ready for testing!
