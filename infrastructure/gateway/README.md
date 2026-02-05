# AgriScheme API Gateway - Traefik Deployment

This directory contains the Traefik API Gateway configuration for AgriScheme Pro.

## Overview

Single entry point for all microservices:
- **External URL**: `http://213.32.19.116/api/v1/*`
- **Dashboard**: `http://213.32.19.116:8080` (monitoring)

## Deployment Steps

### Step 1: Deploy Traefik in Coolify

1. Go to Coolify UI: `http://213.32.19.116:8000`
2. Navigate to: **Projects** → **New Resource**
3. Select: **Docker Compose**
4. Configuration:
   - **Name**: `agrischeme-gateway`
   - **Compose File**: Copy contents from `docker-compose.yml`
   - **Network**: Ensure it uses the `coolify` network
5. Click **Deploy**
6. Wait for container to start (~30 seconds)

### Step 2: Verify Traefik is Running

```bash
# Check Traefik health
curl http://213.32.19.116:8080/api/http/routers

# Should return JSON with routers (empty initially)
```

### Step 3: Configure Service Labels

For each service in Coolify, add the following labels as environment variables.

**Note**: Coolify converts environment variables starting with `TRAEFIK_` to Docker labels.

See `SERVICE_LABELS.md` for complete label configuration for all 15 services.

### Step 4: Test Gateway

```bash
# Test auth service through gateway
curl http://213.32.19.116/api/v1/auth/health

# Should return: {"status":"healthy","service":"auth"}
```

### Step 5: Update Mobile App

Update `.env.production`:
```bash
# Remove individual service URLs
# Use single gateway URL
EXPO_PUBLIC_API_URL=http://213.32.19.116/api/v1
```

Rebuild and deploy mobile APK.

## Architecture

```
Mobile App → http://213.32.19.116/api/v1/auth/register
                ↓
         Traefik Gateway (:80)
                ↓ (path-based routing)
         auth-service:8000 (internal)
```

## Monitoring

**Traefik Dashboard**: `http://213.32.19.116:8080`

Shows:
- Active routes
- Service health
- Request metrics
- Error rates

## Troubleshooting

### Services returning 404

**Problem**: Traefik can't find the service
**Solution**:
1. Check service labels are set correctly
2. Verify service is on `coolify` network
3. Check Traefik logs: `docker logs agrischeme-api-gateway`

### Gateway not accessible

**Problem**: Port 80 not responding
**Solution**:
1. Check Traefik container is running: `docker ps | grep traefik`
2. Check port binding: `netstat -tlnp | grep :80`
3. Restart Traefik in Coolify UI

### Path not routing correctly

**Problem**: Request goes to wrong service
**Solution**:
1. Check PathPrefix in service labels
2. Verify stripPrefix middleware is configured
3. Test with curl to see actual routing

## Next Steps

After gateway is working:

1. **Add SSL/TLS**:
   - Configure domain: `api.agrischeme.com`
   - Add Let's Encrypt certificate resolver
   - Update mobile app to HTTPS

2. **Add Middleware**:
   - Rate limiting
   - CORS headers
   - Authentication
   - Request logging

3. **Monitoring**:
   - Prometheus metrics
   - Grafana dashboards
   - Alerts for downtime
