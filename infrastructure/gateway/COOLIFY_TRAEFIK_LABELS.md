# Service Labels for Coolify's Built-in Traefik

These labels configure Coolify's existing Traefik proxy to route requests to your services.

**Entry Point**: `http://213.32.19.116/api/v1/*`

---

## How to Add Labels

For each service:
1. Go to Coolify UI → Service → **Environment Variables**
2. Click **"+ Add"** for each variable below
3. Click **"Save"**
4. **Restart** the service

---

## 1. Auth Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_AUTH_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/auth`)
TRAEFIK_HTTP_ROUTERS_AUTH_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_AUTH_PRIORITY=100
TRAEFIK_HTTP_SERVICES_AUTH_LOADBALANCER_SERVER_PORT=8000
```

**Test:**
```bash
curl http://213.32.19.116/api/v1/auth/health
```

---

## 2. Farmer Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_FARMER_RULE=Host(`213.32.19.116`) && (PathPrefix(`/api/v1/farmers`) || PathPrefix(`/api/v1/farms`) || PathPrefix(`/api/v1/kyc`) || PathPrefix(`/api/v1/documents`) || PathPrefix(`/api/v1/farm-registration`))
TRAEFIK_HTTP_ROUTERS_FARMER_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_FARMER_PRIORITY=100
TRAEFIK_HTTP_SERVICES_FARMER_LOADBALANCER_SERVER_PORT=8000
```

**Test:**
```bash
curl http://213.32.19.116/api/v1/farmers/health
curl http://213.32.19.116/api/v1/farms/health
```

---

## 3. GIS Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_GIS_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/gis`)
TRAEFIK_HTTP_ROUTERS_GIS_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_GIS_PRIORITY=100
TRAEFIK_HTTP_SERVICES_GIS_LOADBALANCER_SERVER_PORT=8000
```

**Test:**
```bash
curl http://213.32.19.116/api/v1/gis/health
```

---

## 4. Financial Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_FINANCIAL_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/financial`)
TRAEFIK_HTTP_ROUTERS_FINANCIAL_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_FINANCIAL_PRIORITY=100
TRAEFIK_HTTP_SERVICES_FINANCIAL_LOADBALANCER_SERVER_PORT=8000
```

---

## 5. Market Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_MARKET_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/market`)
TRAEFIK_HTTP_ROUTERS_MARKET_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_MARKET_PRIORITY=100
TRAEFIK_HTTP_SERVICES_MARKET_LOADBALANCER_SERVER_PORT=8000
```

---

## 6. AI Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_AI_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/ai`)
TRAEFIK_HTTP_ROUTERS_AI_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_AI_PRIORITY=100
TRAEFIK_HTTP_SERVICES_AI_LOADBALANCER_SERVER_PORT=8000
```

---

## 7. IoT Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_IOT_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/iot`)
TRAEFIK_HTTP_ROUTERS_IOT_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_IOT_PRIORITY=100
TRAEFIK_HTTP_SERVICES_IOT_LOADBALANCER_SERVER_PORT=8000
```

---

## 8. Livestock Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_LIVESTOCK_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/livestock`)
TRAEFIK_HTTP_ROUTERS_LIVESTOCK_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_LIVESTOCK_PRIORITY=100
TRAEFIK_HTTP_SERVICES_LIVESTOCK_LOADBALANCER_SERVER_PORT=8000
```

---

## 9. Task Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_TASK_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/tasks`)
TRAEFIK_HTTP_ROUTERS_TASK_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_TASK_PRIORITY=100
TRAEFIK_HTTP_SERVICES_TASK_LOADBALANCER_SERVER_PORT=8000
```

---

## 10. Inventory Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_INVENTORY_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/inventory`)
TRAEFIK_HTTP_ROUTERS_INVENTORY_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_INVENTORY_PRIORITY=100
TRAEFIK_HTTP_SERVICES_INVENTORY_LOADBALANCER_SERVER_PORT=8000
```

---

## 11. Notification Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_NOTIFICATION_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/notifications`)
TRAEFIK_HTTP_ROUTERS_NOTIFICATION_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_NOTIFICATION_PRIORITY=100
TRAEFIK_HTTP_SERVICES_NOTIFICATION_LOADBALANCER_SERVER_PORT=8000
```

---

## 12. Traceability Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_TRACEABILITY_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/traceability`)
TRAEFIK_HTTP_ROUTERS_TRACEABILITY_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_TRACEABILITY_PRIORITY=100
TRAEFIK_HTTP_SERVICES_TRACEABILITY_LOADBALANCER_SERVER_PORT=8000
```

---

## 13. Compliance Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_COMPLIANCE_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/compliance`)
TRAEFIK_HTTP_ROUTERS_COMPLIANCE_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_COMPLIANCE_PRIORITY=100
TRAEFIK_HTTP_SERVICES_COMPLIANCE_LOADBALANCER_SERVER_PORT=8000
```

---

## 14. Integration Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_INTEGRATION_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/integration`)
TRAEFIK_HTTP_ROUTERS_INTEGRATION_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_INTEGRATION_PRIORITY=100
TRAEFIK_HTTP_SERVICES_INTEGRATION_LOADBALANCER_SERVER_PORT=8000
```

---

## 15. Farm Service

```bash
TRAEFIK_ENABLE=true
TRAEFIK_HTTP_ROUTERS_FARM_RULE=Host(`213.32.19.116`) && PathPrefix(`/api/v1/farm`)
TRAEFIK_HTTP_ROUTERS_FARM_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_FARM_PRIORITY=90
TRAEFIK_HTTP_SERVICES_FARM_LOADBALANCER_SERVER_PORT=8000
```

**Note**: Lower priority to avoid conflict with `/api/v1/farms`

---

## Quick Start: Configure Auth Service First

1. **Delete the failed gateway deployment** in Coolify
2. **Configure auth service** with labels above
3. **Restart auth service**
4. **Test**:
   ```bash
   curl http://213.32.19.116/api/v1/auth/health
   ```

If that works, proceed with the other services!

---

## Testing After Each Service

```bash
# Auth
curl http://213.32.19.116/api/v1/auth/health

# Farmer
curl http://213.32.19.116/api/v1/farmers/health

# Test registration through gateway
curl -X POST http://213.32.19.116/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","first_name":"Test","last_name":"User","phone_number":"+254712345678"}'
```

---

## Troubleshooting

### Labels not working

**Check:**
1. Service is on the same Docker network as Coolify's Traefik
2. Labels are set exactly as shown (no typos)
3. Service is restarted after adding labels

**Debug:**
```bash
# Check if Traefik sees the service
docker logs $(docker ps -q -f name=proxy) 2>&1 | grep auth
```

### 404 errors

**Most common cause**: Service not restarted after adding labels

**Solution**: Restart the service in Coolify UI

---

## Benefits of Using Coolify's Traefik

✅ No port conflicts
✅ Already running and tested
✅ Integrated with Coolify
✅ No additional containers
✅ Works immediately after adding labels

---

## Next: Mobile App

Once services are configured and tested, rebuild the mobile app:

```bash
cd /Users/oscarrombo/agripro/apps/mobile
bash build-release.sh
adb install -r android/app/build/outputs/apk/release/app-release.apk
```

The mobile app is already configured to use `http://213.32.19.116/api/v1`!
