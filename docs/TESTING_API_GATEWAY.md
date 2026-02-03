# Testing API Gateway Implementation

This guide provides step-by-step instructions to test the API gateway implementation locally before deploying to production.

## Prerequisites

- Docker and Docker Compose installed
- Node.js and npm/yarn installed
- Expo CLI installed for mobile testing
- curl or Postman for API testing

## Step 1: Start Services Locally

```bash
# Navigate to project root
cd /Users/oscarrombo/agripro

# Start all services with Traefik gateway
docker-compose up -d

# Wait for services to be healthy (about 30-60 seconds)
docker-compose ps
```

Expected output should show all services as "healthy":
```
NAME                    STATUS
agrischeme-traefik      Up
agrischeme-postgres     Up (healthy)
agrischeme-redis        Up (healthy)
agrischeme-auth         Up (healthy)
agrischeme-farmer       Up (healthy)
agrischeme-gis          Up (healthy)
...
```

## Step 2: Verify Traefik Dashboard

```bash
# Open Traefik dashboard in browser
open http://localhost:8080

# Or check via curl
curl http://localhost:8080/api/http/routers
```

You should see routers for all services:
- `auth@docker`
- `farmer@docker`
- `gis@docker`
- `financial@docker`
- etc.

## Step 3: Test Gateway Routing

### Test Auth Service

```bash
# Health check
curl http://localhost/api/v1/auth/health

# Expected response:
# {"status":"healthy","service":"auth"}

# Register a user
curl -X POST http://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+254712345678"
  }'

# Login
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Save the access_token from the response for next tests
```

### Test Farmer Service

```bash
# Health check
curl http://localhost/api/v1/farmers/health

# Get farmer profile (replace {token} and {farmer_id})
curl http://localhost/api/v1/farmers/{farmer_id} \
  -H "Authorization: Bearer {token}"
```

### Test GIS Service

```bash
# Health check
curl http://localhost/api/v1/gis/health

# Reverse geocode
curl -X POST http://localhost/api/v1/gis/reverse-geocode \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "latitude": -1.2921,
    "longitude": 36.8219
  }'
```

### Test All Service Health Endpoints

```bash
# Create a test script
cat > test-health.sh << 'EOF'
#!/bin/bash
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

echo "Testing all service health endpoints..."
for service in "${services[@]}"; do
  echo -n "Testing $service... "
  response=$(curl -s http://localhost/api/v1/$service/health)
  if [[ $response == *"healthy"* ]]; then
    echo "✓ OK"
  else
    echo "✗ FAILED"
    echo "Response: $response"
  fi
done
EOF

chmod +x test-health.sh
./test-health.sh
```

## Step 4: Test Internal Service Communication

Verify that services can communicate with each other using container names:

```bash
# Exec into farmer service
docker exec -it agrischeme-farmer bash

# Inside container, test DNS resolution
ping -c 2 postgres
ping -c 2 auth-service
ping -c 2 redis

# Test connectivity
curl http://auth-service:9000/health
curl http://postgres:5432  # Should fail but resolve

# Exit container
exit
```

## Step 5: Test Database Connectivity

```bash
# Connect to PostgreSQL
docker exec -it agrischeme-postgres psql -U postgres

# List databases
\l

# You should see all databases:
# agrischeme_auth
# agrischeme_farmer
# agrischeme_gis
# agrischeme_financial
# ... etc

# Connect to a database
\c agrischeme_auth

# List tables
\dt

# Exit
\q
```

## Step 6: Test Mobile App Locally

### Start Expo Development Server

```bash
cd apps/mobile

# Install dependencies if needed
yarn install

# Start Expo
expo start
```

### Configure for Local Testing

The mobile app should automatically detect your development server IP. Verify in the console output:

```
API Configuration: {
  API_GATEWAY_URL: 'http://192.168.x.x/api/v1',
  ...
}
```

### Test Registration Flow

1. Open Expo app on your device/emulator
2. Navigate to Register screen
3. Fill in registration details
4. Submit form
5. Verify in logs that request goes to gateway:
   ```
   POST http://{your-ip}/api/v1/auth/register
   ```

### Test Login Flow

1. Navigate to Login screen
2. Enter credentials
3. Submit
4. Verify successful login and token storage

### Test Farmer Profile

1. After login, navigate to profile
2. Verify farmer data loads from gateway:
   ```
   GET http://{your-ip}/api/v1/farmers/{id}
   ```

## Step 7: Check Logs

```bash
# View Traefik logs
docker logs agrischeme-traefik

# View auth service logs
docker logs agrischeme-auth

# View farmer service logs
docker logs agrischeme-farmer

# Follow logs in real-time
docker logs -f agrischeme-traefik
```

## Step 8: Performance Testing

### Test Response Times

```bash
# Test auth service
time curl http://localhost/api/v1/auth/health

# Test multiple services
for i in {1..10}; do
  time curl -s http://localhost/api/v1/auth/health > /dev/null
done
```

### Expected Latency

- Health checks: < 50ms
- Auth endpoints: < 200ms
- Data fetching: < 300ms

Additional latency from Traefik should be < 10ms.

## Step 9: Load Testing (Optional)

```bash
# Install Apache Bench
# On macOS: brew install httpd (includes ab)

# Test 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost/api/v1/auth/health

# Test with POST (login)
ab -n 100 -c 5 -p login.json -T application/json \
  http://localhost/api/v1/auth/login

# Where login.json contains:
# {"email":"test@example.com","password":"SecurePass123!"}
```

## Step 10: Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (optional - deletes all data)
docker-compose down -v

# Remove test script
rm -f test-health.sh
```

## Common Issues and Solutions

### Port 80 Already in Use

**Error**: `Bind for 0.0.0.0:80 failed: port is already allocated`

**Solution**:
```bash
# Find what's using port 80
sudo lsof -i :80

# Stop the service or change Traefik port in docker-compose.yml
# Change "80:80" to "8000:80" and use http://localhost:8000
```

### Services Not Healthy

**Error**: Services stuck in "starting" state

**Solution**:
```bash
# Check service logs
docker logs agrischeme-auth

# Common issues:
# 1. Database not ready - wait longer
# 2. Port conflict - check ports
# 3. Build error - rebuild image
docker-compose build auth-service
docker-compose up -d auth-service
```

### Gateway Returns 404

**Error**: `404 page not found` from Traefik

**Solution**:
```bash
# Check Traefik discovered the service
docker logs agrischeme-traefik | grep -i "router"

# Verify service labels
docker inspect agrischeme-auth | grep -A 10 Labels

# Restart Traefik
docker-compose restart traefik
```

### Mobile App Can't Connect

**Error**: `Network request failed`

**Solution**:
1. Verify device is on same network as development machine
2. Check firewall allows connections on port 80
3. For Android emulator, use `http://10.0.2.2/api/v1`
4. For iOS simulator, use `http://localhost/api/v1`
5. Check network security config allows cleartext traffic

## Success Criteria

- ✅ All services show "healthy" status
- ✅ Traefik dashboard shows all routers
- ✅ All health endpoints return 200 OK
- ✅ Auth registration and login work through gateway
- ✅ Farmer service can call auth service internally
- ✅ Mobile app connects and functions properly
- ✅ Response times are acceptable (< 200ms)
- ✅ No DNS resolution errors in logs

## Next Steps After Testing

Once local testing is successful:

1. **Commit changes**: All configuration files are ready
2. **Deploy to staging**: Test in staging environment
3. **Configure DNS**: Point domain to server
4. **Setup SSL**: Configure Let's Encrypt certificates
5. **Deploy mobile app**: Build and release updated app
6. **Monitor**: Watch logs and metrics after deployment

## Automated Testing Script

```bash
#!/bin/bash
# comprehensive-test.sh

set -e

echo "Starting comprehensive API gateway tests..."

# Start services
echo "1. Starting services..."
docker-compose up -d
sleep 30

# Check service health
echo "2. Checking service health..."
services=("auth" "farmers" "gis" "financial")
for service in "${services[@]}"; do
    response=$(curl -s http://localhost/api/v1/$service/health)
    if [[ $response == *"healthy"* ]]; then
        echo "✓ $service is healthy"
    else
        echo "✗ $service failed"
        exit 1
    fi
done

# Test registration
echo "3. Testing user registration..."
register_response=$(curl -s -X POST http://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","first_name":"Test","last_name":"User","phone_number":"+254712345678"}')

if [[ $register_response == *"user_id"* ]]; then
    echo "✓ Registration successful"
else
    echo "✗ Registration failed"
    exit 1
fi

# Test login
echo "4. Testing login..."
login_response=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}')

if [[ $login_response == *"access_token"* ]]; then
    echo "✓ Login successful"
else
    echo "✗ Login failed"
    exit 1
fi

echo "All tests passed! ✓"
```

Save this as `comprehensive-test.sh`, make it executable, and run it:

```bash
chmod +x comprehensive-test.sh
./comprehensive-test.sh
```
