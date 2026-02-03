# API Gateway & DNS-Independent Service Communication

## Overview

This implementation provides a unified API gateway using Traefik for all external service access, and DNS-independent internal communication using Docker container names.

## Architecture

### External Access
- **Single entry point**: `http://{server}/api/v1/*`
- **Path-based routing**: Traefik routes requests to appropriate services based on URL path
- **Automatic service discovery**: Services are discovered via Docker labels

### Internal Communication
- **Docker bridge network**: All services communicate via `agrischeme-network`
- **Container name resolution**: Services use container names (e.g., `auth-service:9000`)
- **No external DNS dependency**: All resolution happens within Docker's embedded DNS

## Service Routing Table

| Path Prefix | Service | Internal Port |
|------------|---------|---------------|
| `/api/v1/auth/*` | auth-service | 9000 |
| `/api/v1/farmers/*` | farmer-service | 9001 |
| `/api/v1/farms/*` | farmer-service | 9001 |
| `/api/v1/kyc/*` | farmer-service | 9001 |
| `/api/v1/crop-planning/*` | farmer-service | 9001 |
| `/api/v1/gis/*` | gis-service | 8000 |
| `/api/v1/financial/*` | financial-service | 8000 |
| `/api/v1/market/*` | market-service | 8000 |
| `/api/v1/ai/*` | ai-service | 8000 |
| `/api/v1/iot/*` | iot-service | 8000 |
| `/api/v1/livestock/*` | livestock-service | 8000 |
| `/api/v1/tasks/*` | task-service | 8000 |
| `/api/v1/inventory/*` | inventory-service | 8000 |
| `/api/v1/notifications/*` | notification-service | 8000 |
| `/api/v1/traceability/*` | traceability-service | 8000 |
| `/api/v1/compliance/*` | compliance-service | 8000 |
| `/api/v1/integration/*` | integration-service | 8000 |

## Local Development

### Starting Services

```bash
# Start all services with Traefik gateway
docker-compose up -d

# Check Traefik dashboard
open http://localhost:8080

# Test gateway routing
curl http://localhost/api/v1/auth/health
curl http://localhost/api/v1/farmers/health
```

### Mobile App Configuration

The mobile app now uses a single API client that connects through the gateway:

**Development** (auto-detects host):
```bash
# No configuration needed - automatically detects development server
expo start
```

**Production**:
```bash
# Set in apps/mobile/.env.production
EXPO_PUBLIC_API_URL=http://213.32.19.116/api/v1
```

### Verifying Service Communication

```bash
# Exec into a service container
docker exec -it agrischeme-farmer bash

# Test DNS resolution
ping postgres  # Should resolve
ping auth-service  # Should resolve

# Test connectivity
curl http://auth-service:9000/health
```

## Production Deployment

### Prerequisites

1. Server with Docker and Docker Compose
2. Coolify installed (optional, for easier management)
3. Environment variables configured

### Deployment Steps

1. **Deploy infrastructure**:
```bash
# Deploy using docker-compose
docker-compose -f docker-compose.yml up -d
```

2. **Verify Traefik is running**:
```bash
# Check Traefik dashboard
curl http://{server-ip}:8080/api/http/routers

# Should show all configured routes
```

3. **Test gateway routing**:
```bash
# Test each service through gateway
curl http://{server-ip}/api/v1/auth/health
curl http://{server-ip}/api/v1/farmers/health
curl http://{server-ip}/api/v1/gis/health
```

4. **Update mobile app**:
```bash
# Update .env.production
EXPO_PUBLIC_API_URL=http://{server-ip}/api/v1

# Build and deploy mobile app
cd apps/mobile
eas build --platform android --profile production
```

### Using the Deployment Script

```bash
# Set environment variables
export COOLIFY_TOKEN="your-coolify-api-token"
export SERVER_IP="213.32.19.116"

# Run deployment script
./scripts/deploy/deploy-with-gateway.sh
```

## Configuration Files

### Traefik Configuration
- **Location**: `infrastructure/docker/traefik/traefik.yml`
- **Purpose**: Traefik static configuration
- **Key settings**:
  - Entry points (HTTP/HTTPS)
  - Docker provider configuration
  - Certificate resolver

### Docker Compose
- **Location**: `docker-compose.yml`
- **Key additions**:
  - Traefik service definition
  - Service labels for routing
  - Health checks for all services
  - Network configuration

### Service Labels

Each service has Traefik labels for routing:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.{service}.rule=PathPrefix(`/api/v1/{service}`)"
  - "traefik.http.routers.{service}.entrypoints=web"
  - "traefik.http.services.{service}.loadbalancer.server.port={port}"
  - "traefik.http.routers.{service}.middlewares=strip-prefix-{service}"
  - "traefik.http.middlewares.strip-prefix-{service}.stripprefix.prefixes=/api/v1"
```

## Database Configuration

### Single PostgreSQL Instance

All services use a single PostgreSQL container with multiple databases:

- `agrischeme_auth`
- `agrischeme_farmer`
- `agrischeme_farm`
- `agrischeme_financial`
- `agrischeme_gis`
- `agrischeme_market`
- `agrischeme_ai`
- `agrischeme_iot`
- `agrischeme_livestock`
- `agrischeme_task`
- `agrischeme_inventory`
- `agrischeme_notification`
- `agrischeme_traceability`
- `agrischeme_compliance`
- `agrischeme_integration`

### Connection Strings

All services connect using the container name:

```
postgresql+asyncpg://postgres:postgres@postgres:5432/agrischeme_{service}
```

## Troubleshooting

### Service can't connect to database

**Problem**: `gaierror: Name or service not known`

**Solution**: Check that:
1. Service is on `agrischeme-network`
2. DATABASE_URL uses `postgres` container name, not DNS hostname
3. PostgreSQL service is healthy before dependent services start

### Gateway not routing to service

**Problem**: 404 or 502 from gateway

**Solution**:
1. Check Traefik dashboard at `http://{server}:8080`
2. Verify service labels are correct
3. Ensure service is healthy: `docker ps` shows "healthy" status
4. Check service logs: `docker logs agrischeme-{service}`

### Mobile app can't connect

**Problem**: Network request failed

**Solution**:
1. Verify `EXPO_PUBLIC_API_URL` is set correctly
2. Check network security config allows the server IP/domain
3. Test gateway endpoint with curl
4. Check mobile device is on same network (development) or has internet access (production)

## Benefits

### External Access
✅ Single entry point for all services
✅ Simplified mobile app configuration
✅ Centralized authentication/authorization
✅ SSL/TLS termination at gateway
✅ Rate limiting capability

### Internal Communication
✅ No DNS dependency
✅ Fast Docker-native resolution
✅ Automatic service discovery
✅ Network isolation
✅ Simple debugging

### Operational
✅ Leverages existing infrastructure (Traefik)
✅ Automatic load balancing
✅ Health-based routing
✅ Easy service addition
✅ Observable via Traefik dashboard

## Next Steps

1. **DNS Configuration**: Point `api.agrischeme.com` to server IP
2. **SSL Certificates**: Configure Let's Encrypt for HTTPS
3. **Rate Limiting**: Add Traefik middleware for rate limiting
4. **Authentication**: Add JWT validation middleware at gateway
5. **Monitoring**: Integrate Traefik metrics with Prometheus/Grafana

## References

- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Docker Networking](https://docs.docker.com/network/)
- [Coolify Documentation](https://coolify.io/docs)
