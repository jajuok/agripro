# Traefik API Gateway - Complete Deployment Guide

This guide walks you through deploying the Traefik API Gateway for AgriScheme Pro.

**Time Required**: 2-3 hours
**Difficulty**: Medium

---

## Prerequisites

- ✅ All 15 services deployed in Coolify
- ✅ Services are healthy and running
- ✅ Access to Coolify UI at `http://213.32.19.116:8000`
- ✅ SSH access to server (optional, for troubleshooting)

---

## Part 1: Deploy Traefik Gateway (30 minutes)

### Step 1: Access Coolify

1. Open browser: `http://213.32.19.116:8000`
2. Log in to Coolify

### Step 2: Create New Docker Compose Resource

1. Click **"Projects"** in sidebar
2. Select your project (or create new: "agrischeme-infra")
3. Click **"+ New Resource"**
4. Select **"Docker Compose"**

### Step 3: Configure Traefik

**Name**: `agrischeme-gateway`

**Docker Compose Content**: Copy the entire content from:
```
/Users/oscarrombo/agripro/infrastructure/gateway/docker-compose.yml
```

**Key Configuration Points**:
- Port 80: API Gateway entry point
- Port 8080: Traefik Dashboard
- Network: `coolify` (external)
- Docker socket access: Required for service discovery

### Step 4: Deploy

1. Click **"Save"** or **"Deploy"**
2. Wait for deployment (~30 seconds)
3. Check status: Should show "Running"

### Step 5: Verify Traefik is Working

**Test from your local machine**:
```bash
# Check Traefik API
curl http://213.32.19.116:8080/api/http/routers

# Expected: JSON array (empty initially, will have routers after Step 2)
```

**Expected Response**:
```json
[]
```

If you get this, Traefik is running correctly!

**Access Dashboard** (optional):
Open in browser: `http://213.32.19.116:8080`

You should see the Traefik dashboard showing:
- 0 routers (we'll add these next)
- 0 services
- 1 entrypoint (web)

---

## Part 2: Configure Service Labels (1-2 hours)

Now we'll add Traefik routing labels to each of your 15 services.

### How Traefik Labels Work

Traefik reads Docker labels to understand how to route requests:
- `TRAEFIK_ENABLE=true` - Tell Traefik to route to this service
- `TRAEFIK_HTTP_ROUTERS_..._RULE` - What URL path to match
- `TRAEFIK_HTTP_SERVICES_..._PORT` - What port the service listens on

### Service Configuration Order

**Start with these critical services**:
1. Auth (for login/registration)
2. Farmer (for user data)
3. GIS (commonly used)

Then add the rest.

### Detailed Steps for Each Service

For **EACH** of the 15 services, follow this process:

---

#### Auth Service (Example - Follow for All Services)

1. **Go to Service**:
   - Coolify UI → Services → "auth"

2. **Open Environment Variables**:
   - Click **"Environment Variables"** tab
   - You'll see existing variables

3. **Add Traefik Labels**:

   Click **"+ Add"** button and add each of these:

   **Variable 1**:
   - Name: `TRAEFIK_ENABLE`
   - Value: `true`

   **Variable 2**:
   - Name: `TRAEFIK_HTTP_ROUTERS_AUTH_RULE`
   - Value: `PathPrefix(\`/api/v1/auth\`)`

   **Variable 3**:
   - Name: `TRAEFIK_HTTP_ROUTERS_AUTH_ENTRYPOINTS`
   - Value: `web`

   **Variable 4**:
   - Name: `TRAEFIK_HTTP_ROUTERS_AUTH_PRIORITY`
   - Value: `100`

   **Variable 5**:
   - Name: `TRAEFIK_HTTP_SERVICES_AUTH_LOADBALANCER_SERVER_PORT`
   - Value: `8000`

4. **Save**:
   - Click **"Save"** button

5. **Restart Service**:
   - Click **"Restart"** button
   - Wait for service to restart (~30 seconds)

6. **Verify**:
   ```bash
   # Check Traefik now sees the auth service
   curl http://213.32.19.116:8080/api/http/routers | grep auth

   # Test routing
   curl http://213.32.19.116/api/v1/auth/health
   ```

   **Expected**: `{"status":"healthy","service":"auth"}`

---

#### Repeat for All 15 Services

Use the exact labels from `/Users/oscarrombo/agripro/infrastructure/gateway/SERVICE_LABELS.md`

**Service Checklist**:
- [ ] 1. Auth Service
- [ ] 2. Farmer Service (note: multiple paths)
- [ ] 3. Farm Service
- [ ] 4. GIS Service
- [ ] 5. Financial Service
- [ ] 6. Market Service
- [ ] 7. AI Service
- [ ] 8. IoT Service
- [ ] 9. Livestock Service
- [ ] 10. Task Service
- [ ] 11. Inventory Service
- [ ] 12. Notification Service
- [ ] 13. Traceability Service
- [ ] 14. Compliance Service
- [ ] 15. Integration Service

**Pro Tip**: After configuring 2-3 services, test them before continuing:
```bash
curl http://213.32.19.116/api/v1/auth/health
curl http://213.32.19.116/api/v1/farmers/health
curl http://213.32.19.116/api/v1/gis/health
```

---

## Part 3: Test Gateway Routing (15 minutes)

After all services are configured:

### Test All Health Endpoints

```bash
# Create a test script
cat > /tmp/test-gateway.sh << 'EOF'
#!/bin/bash

echo "Testing AgriScheme API Gateway Routing"
echo "======================================="
echo ""

GATEWAY="http://213.32.19.116/api/v1"

services=(
  "auth"
  "farmers"
  "gis"
  "financial"
  "market"
  "ai"
  "iot"
  "livestock"
  "tasks"
  "inventory"
  "notifications"
  "traceability"
  "compliance"
  "integration"
)

for service in "${services[@]}"; do
  echo -n "Testing /$service/health... "
  response=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY/$service/health" 2>&1)

  if [ "$response" = "200" ]; then
    echo "✓ OK"
  else
    echo "✗ Failed (HTTP $response)"
  fi
done

echo ""
echo "Testing complete!"
EOF

chmod +x /tmp/test-gateway.sh
bash /tmp/test-gateway.sh
```

**Expected Output**:
```
Testing AgriScheme API Gateway Routing
=======================================

Testing /auth/health... ✓ OK
Testing /farmers/health... ✓ OK
Testing /gis/health... ✓ OK
...
Testing complete!
```

### Test Registration Flow

```bash
# Test complete registration through gateway
curl -X POST http://213.32.19.116/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "gateway-test@example.com",
    "password": "Test123!",
    "first_name": "Gateway",
    "last_name": "Test",
    "phone_number": "+254712345678"
  }'
```

**Expected**: User created successfully with tokens returned

### Check Traefik Dashboard

Open: `http://213.32.19.116:8080`

You should see:
- **15 routers** (one per service, farmer has multiple)
- All routers showing **green** (active)
- **15 services** (one per microservice)

---

## Part 4: Update & Deploy Mobile App (30 minutes)

### Update Configuration

The files have already been updated:
- ✅ `.env.production` - Uses `EXPO_PUBLIC_API_URL`
- ✅ `build-release.sh` - Exports gateway URL
- ✅ `api.ts` - Already supports gateway mode

### Rebuild APK

```bash
cd /Users/oscarrombo/agripro/apps/mobile
bash build-release.sh
```

**Build time**: 2-3 minutes

### Install on Device

```bash
adb install -r android/app/build/outputs/apk/release/app-release.apk
```

### Test on Device

1. **Open app**
2. **Try Registration**:
   - Should work through gateway
   - Creates user via `http://213.32.19.116/api/v1/auth/register`
3. **Try Login**:
   - Should authenticate successfully
   - Gets tokens from gateway
4. **Navigate to My Farms**:
   - Should load farms via `http://213.32.19.116/api/v1/farms/...`

---

## Troubleshooting

### Problem: Traefik returns 404 for all requests

**Cause**: Service labels not configured or service not on same network

**Solution**:
1. Check service has labels set
2. Verify service is running: `docker ps | grep <service-name>`
3. Check Traefik logs: `docker logs agrischeme-api-gateway`
4. Restart both service and Traefik

### Problem: Some services work, others don't

**Cause**: Missing or incorrect labels on non-working services

**Solution**:
1. Compare working vs non-working service labels
2. Check for typos in environment variables
3. Verify `TRAEFIK_ENABLE=true` is set
4. Restart non-working services

### Problem: Traefik dashboard empty (no routers)

**Cause**: Traefik can't access Docker socket or wrong network

**Solution**:
1. Check Traefik has Docker socket mounted:
   ```bash
   docker inspect agrischeme-api-gateway | grep docker.sock
   ```
2. Verify network is `coolify`:
   ```bash
   docker inspect agrischeme-api-gateway | grep coolify
   ```
3. Redeploy Traefik with correct configuration

### Problem: Mobile app still getting errors

**Cause**: Old APK cached or wrong environment variable

**Solution**:
1. Uninstall app completely from device
2. Rebuild APK fresh: `bash build-release.sh`
3. Install new APK
4. Check app logs: `adb logcat | grep API`

### Problem: Gateway works locally but not from mobile

**Cause**: Network/firewall issue or wrong IP

**Solution**:
1. Verify server IP is correct: `213.32.19.116`
2. Test from mobile browser: `http://213.32.19.116/api/v1/auth/health`
3. Check server firewall allows port 80
4. Try with mobile data (not WiFi) to rule out network issues

---

## Verification Checklist

After deployment, verify:

- [ ] Traefik container is running
- [ ] Traefik dashboard accessible at `:8080`
- [ ] All 15 services configured with labels
- [ ] All services restarted after adding labels
- [ ] Health endpoints return 200 OK through gateway
- [ ] Registration works through gateway (test with curl)
- [ ] Login works through gateway (test with curl)
- [ ] Mobile APK rebuilt with gateway URL
- [ ] Mobile app can register new users
- [ ] Mobile app can login
- [ ] Mobile app can load farms data

---

## Success Criteria

✅ **Gateway Working** when:
1. Traefik dashboard shows all 15 services
2. All health endpoints return 200 OK
3. Registration/login work via curl
4. Mobile app can authenticate
5. Mobile app can access all features

---

## Next Steps After Success

1. **Add SSL/TLS**:
   - Configure domain: `api.agrischeme.com`
   - Add Let's Encrypt
   - Update mobile app to HTTPS

2. **Add Monitoring**:
   - Set up Prometheus metrics
   - Create Grafana dashboards
   - Configure alerts

3. **Add Security**:
   - Rate limiting middleware
   - IP whitelisting (optional)
   - Request logging
   - CORS headers

4. **Performance**:
   - Enable compression
   - Add caching headers
   - Load balancing (if needed)

---

## Support

If you encounter issues:

1. **Check logs**:
   ```bash
   docker logs agrischeme-api-gateway
   docker logs <service-container-name>
   ```

2. **Traefik API**:
   ```bash
   curl http://213.32.19.116:8080/api/http/routers
   curl http://213.32.19.116:8080/api/http/services
   ```

3. **Test direct service access** (bypass gateway):
   ```bash
   # Get service container name
   docker ps | grep auth

   # Access directly
   curl http://eswo8kkw0owo8ckk00cgsc0g:8000/api/v1/health
   ```

4. **Restart everything**:
   ```bash
   # Restart Traefik
   docker restart agrischeme-api-gateway

   # Restart a service (via Coolify UI)
   ```

---

**Good luck with the deployment!** 🚀

Once the gateway is working, you'll have a clean, maintainable architecture with a single entry point for all your microservices.
