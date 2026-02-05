# Service Labels Configuration for Traefik Routing

Add these labels to each service via Coolify UI → Service → Environment Variables

**Important**: Coolify converts environment variables to Docker labels automatically.

---

## 1. Auth Service

**Coolify UUID**: `eswo8kkw0owo8ckk00cgsc0g`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_AUTH_RULE=PathPrefix(`/api/v1/auth`)
TRAEFIK_HTTP_ROUTERS_AUTH_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_AUTH_PRIORITY=100
TRAEFIK_HTTP_SERVICES_AUTH_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/auth/*` → auth-service:8000

---

## 2. Farmer Service

**Coolify UUID**: `fswk00skcko8wgkcs840o4ok`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_FARMER_RULE=PathPrefix(`/api/v1/farmers`) || PathPrefix(`/api/v1/farms`) || PathPrefix(`/api/v1/kyc`) || PathPrefix(`/api/v1/documents`) || PathPrefix(`/api/v1/farm-registration`)
TRAEFIK_HTTP_ROUTERS_FARMER_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_FARMER_PRIORITY=100
TRAEFIK_HTTP_SERVICES_FARMER_LOADBALANCER_SERVER_PORT=8000
```

**Routes**:
- `/api/v1/farmers/*` → farmer-service:8000
- `/api/v1/farms/*` → farmer-service:8000
- `/api/v1/kyc/*` → farmer-service:8000
- `/api/v1/documents/*` → farmer-service:8000
- `/api/v1/farm-registration/*` → farmer-service:8000

---

## 3. Farm Service

**Coolify UUID**: `e800ock8kkck4g80kkw4k4os`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_FARM_RULE=PathPrefix(`/api/v1/farm`)
TRAEFIK_HTTP_ROUTERS_FARM_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_FARM_PRIORITY=90
TRAEFIK_HTTP_SERVICES_FARM_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/farm/*` → farm-service:8000

**Note**: Lower priority than farmer service to avoid conflicts with `/api/v1/farms`

---

## 4. GIS Service

**Coolify UUID**: `ckscgcwgcckgk40g4sgkocsw`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_GIS_RULE=PathPrefix(`/api/v1/gis`)
TRAEFIK_HTTP_ROUTERS_GIS_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_GIS_PRIORITY=100
TRAEFIK_HTTP_SERVICES_GIS_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/gis/*` → gis-service:8000

---

## 5. Financial Service

**Coolify UUID**: `ksk48c04o0c4o00gs8ggo4go`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_FINANCIAL_RULE=PathPrefix(`/api/v1/financial`)
TRAEFIK_HTTP_ROUTERS_FINANCIAL_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_FINANCIAL_PRIORITY=100
TRAEFIK_HTTP_SERVICES_FINANCIAL_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/financial/*` → financial-service:8000

---

## 6. Market Service

**Coolify UUID**: `dgk8w048wcc0ckg00k0k0oc4`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_MARKET_RULE=PathPrefix(`/api/v1/market`)
TRAEFIK_HTTP_ROUTERS_MARKET_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_MARKET_PRIORITY=100
TRAEFIK_HTTP_SERVICES_MARKET_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/market/*` → market-service:8000

---

## 7. AI Service

**Coolify UUID**: `dgos8sgc0ckgc0kco04gg4kw`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_AI_RULE=PathPrefix(`/api/v1/ai`)
TRAEFIK_HTTP_ROUTERS_AI_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_AI_PRIORITY=100
TRAEFIK_HTTP_SERVICES_AI_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/ai/*` → ai-service:8000

---

## 8. IoT Service

**Coolify UUID**: `rgc0c8so8c8kgckc4gskscc4`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_IOT_RULE=PathPrefix(`/api/v1/iot`)
TRAEFIK_HTTP_ROUTERS_IOT_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_IOT_PRIORITY=100
TRAEFIK_HTTP_SERVICES_IOT_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/iot/*` → iot-service:8000

---

## 9. Livestock Service

**Coolify UUID**: `rggcw4ocg4cswk8cokoswo00`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_LIVESTOCK_RULE=PathPrefix(`/api/v1/livestock`)
TRAEFIK_HTTP_ROUTERS_LIVESTOCK_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_LIVESTOCK_PRIORITY=100
TRAEFIK_HTTP_SERVICES_LIVESTOCK_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/livestock/*` → livestock-service:8000

---

## 10. Task Service

**Coolify UUID**: `rckowgo8ogwogw8gc04o48ko`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_TASK_RULE=PathPrefix(`/api/v1/tasks`)
TRAEFIK_HTTP_ROUTERS_TASK_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_TASK_PRIORITY=100
TRAEFIK_HTTP_SERVICES_TASK_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/tasks/*` → task-service:8000

---

## 11. Inventory Service

**Coolify UUID**: `i0gkkgkgs88ks44oo0csc84w`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_INVENTORY_RULE=PathPrefix(`/api/v1/inventory`)
TRAEFIK_HTTP_ROUTERS_INVENTORY_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_INVENTORY_PRIORITY=100
TRAEFIK_HTTP_SERVICES_INVENTORY_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/inventory/*` → inventory-service:8000

---

## 12. Notification Service

**Coolify UUID**: `fsg84owk8cggwc844kkcgcoc`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_NOTIFICATION_RULE=PathPrefix(`/api/v1/notifications`)
TRAEFIK_HTTP_ROUTERS_NOTIFICATION_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_NOTIFICATION_PRIORITY=100
TRAEFIK_HTTP_SERVICES_NOTIFICATION_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/notifications/*` → notification-service:8000

---

## 13. Traceability Service

**Coolify UUID**: `eww0o8woscc4ckkg4kokwcoo`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_TRACEABILITY_RULE=PathPrefix(`/api/v1/traceability`)
TRAEFIK_HTTP_ROUTERS_TRACEABILITY_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_TRACEABILITY_PRIORITY=100
TRAEFIK_HTTP_SERVICES_TRACEABILITY_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/traceability/*` → traceability-service:8000

---

## 14. Compliance Service

**Coolify UUID**: `v4c4c4k4g0wcwcc484cggk0k`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_COMPLIANCE_RULE=PathPrefix(`/api/v1/compliance`)
TRAEFIK_HTTP_ROUTERS_COMPLIANCE_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_COMPLIANCE_PRIORITY=100
TRAEFIK_HTTP_SERVICES_COMPLIANCE_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/compliance/*` → compliance-service:8000

---

## 15. Integration Service

**Coolify UUID**: `gw8s0swo000g0wcsk4s444k0`

**Add these environment variables**:
```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_INTEGRATION_RULE=PathPrefix(`/api/v1/integration`)
TRAEFIK_HTTP_ROUTERS_INTEGRATION_ENTRYPOINTS=web
TRAEFIK_HTTP_ROUTERS_INTEGRATION_PRIORITY=100
TRAEFIK_HTTP_SERVICES_INTEGRATION_LOADBALANCER_SERVER_PORT=8000
```

**Routes**: `/api/v1/integration/*` → integration-service:8000

---

## How to Add Labels in Coolify

1. Go to Coolify UI: `http://213.32.19.116:8000`
2. Navigate to the service (e.g., "auth")
3. Click **"Environment Variables"** tab
4. Click **"+ Add"** for each variable above
5. Enter variable name and value exactly as shown
6. Click **"Save"**
7. **Restart the service** for labels to take effect

## Verification

After adding labels and restarting services, check Traefik dashboard:

```bash
# Open dashboard
open http://213.32.19.116:8080

# Or via API
curl http://213.32.19.116:8080/api/http/routers | jq
```

You should see routers for all configured services.

## Testing Individual Services

```bash
# Test each service through gateway
curl http://213.32.19.116/api/v1/auth/health
curl http://213.32.19.116/api/v1/farmers/health
curl http://213.32.19.116/api/v1/gis/health
# ... etc for all services
```

## Priority Explanation

- **Priority 100**: Most specific paths (e.g., `/api/v1/farmers`)
- **Priority 90**: Less specific paths that might conflict (e.g., `/api/v1/farm` vs `/api/v1/farms`)

Higher priority routes are matched first.

## Troubleshooting

### Service not appearing in Traefik

**Check**:
1. Labels are set correctly (no typos)
2. Service is running
3. Service is on `coolify` network
4. Traefik can access Docker socket

**Solution**: Restart both service and Traefik gateway

### 404 errors

**Check**:
1. PathPrefix matches your request path
2. Service port is correct (8000)
3. Service is actually listening on that port

**Debug**: Check Traefik logs
```bash
docker logs agrischeme-api-gateway
```

### Conflicts between routes

**Check**: Priority values - higher priority routes match first

**Example**: `/api/v1/farms` should have higher priority than `/api/v1/farm`
