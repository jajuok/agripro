#!/bin/bash

# Deploy All Services via Docker Compose
# Alternative to Coolify API - deploys services directly with Docker Compose

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"
load_secrets "${SCRIPT_DIR}/.secrets/deployment.secrets"

# =============================================================================
# CONFIGURATION
# =============================================================================

SERVER_IP="${1}"
SSH_KEY="${2}"

# Services to deploy
SERVICES=(
    "auth:agrischeme_auth"
    "farmer:agrischeme_farmer"
    "farm:agrischeme_farm"
    "financial:agrischeme_financial"
    "gis:agrischeme_gis"
    "market:agrischeme_market"
    "ai:agrischeme_ai"
    "iot:agrischeme_iot"
    "livestock:agrischeme_livestock"
    "task:agrischeme_task"
    "inventory:agrischeme_inventory"
    "notification:agrischeme_notification"
    "traceability:agrischeme_traceability"
    "compliance:agrischeme_compliance"
    "integration:agrischeme_integration"
)

log_section "Service Deployment via Docker Compose"

# =============================================================================
# CLONE REPOSITORY ON SERVER
# =============================================================================

log_step "Setting up repository on server"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    cd /opt/agrischeme

    # Clone or update repository
    if [ -d agripro ]; then
        cd agripro
        git pull origin main
    else
        git clone https://github.com/jajuok/agripro.git
        cd agripro
    fi

    # Show current commit
    git log -1 --oneline
"

log_success "Repository ready"

# =============================================================================
# GENERATE DOCKER COMPOSE FILE
# =============================================================================

log_step "Generating docker-compose file for services"

compose_content="networks:
  agrischeme-network:
    external: true

services:
"

port=8100  # Starting port for services

for service_config in "${SERVICES[@]}"; do
    IFS=':' read -r service_name db_name <<< "$service_config"

    database_url="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@agrischeme-${service_name}-db:5432/${db_name}"

    compose_content+="
  agrischeme-${service_name}-service:
    build:
      context: .
      dockerfile: services/${service_name}/Dockerfile
    container_name: agrischeme-${service_name}-service
    environment:
      DATABASE_URL: '${database_url}'
      REDIS_URL: 'redis://:${REDIS_PASSWORD}@agrischeme-redis:6379/0'
      KAFKA_BOOTSTRAP_SERVERS: 'agrischeme-kafka:9092'
      ENVIRONMENT: 'production'
      LOG_LEVEL: 'INFO'
      DEBUG: 'false'
      CORS_ORIGINS: '[\"*\"]'"

    # Add JWT config for auth service
    if [ "$service_name" = "auth" ]; then
        compose_content+="
      JWT_SECRET_KEY: '${JWT_SECRET_KEY}'
      JWT_ALGORITHM: 'HS256'
      ACCESS_TOKEN_EXPIRE_MINUTES: '30'
      REFRESH_TOKEN_EXPIRE_DAYS: '7'"
    fi

    compose_content+="
    ports:
      - '${port}:8000'
    networks:
      - agrischeme-network
    restart: unless-stopped
    depends_on:
      - agrischeme-${service_name}-db
      - agrischeme-redis
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8000/health']
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
"

    ((port++))
done

# Write compose file to server
log_step "Uploading docker-compose file"

remote_exec "$SERVER_IP" "$SSH_KEY" "cat > /opt/agrischeme/agripro/docker-compose-services.yml" <<< "$compose_content"

log_success "Docker compose file created"

# =============================================================================
# BUILD AND DEPLOY SERVICES
# =============================================================================

log_step "Building and deploying services (this may take 10-15 minutes)"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    cd /opt/agrischeme/agripro

    # Build and start services
    docker compose -f docker-compose-services.yml up -d --build

    echo ''
    echo 'Services started!'
"

log_success "Services deployed"

# =============================================================================
# WAIT FOR SERVICES TO BE HEALTHY
# =============================================================================

log_step "Waiting for services to be healthy"

sleep 30  # Give services time to start

# Check each service
for service_config in "${SERVICES[@]}"; do
    IFS=':' read -r service_name db_name <<< "$service_config"
    container_name="agrischeme-${service_name}-service"

    echo -n "Checking ${service_name}-service... "

    # Check if container is running
    status=$(remote_exec "$SERVER_IP" "$SSH_KEY" "docker ps --filter 'name=${container_name}' --format '{{.Status}}'" || echo "not running")

    if echo "$status" | grep -q "Up"; then
        echo -e "${GREEN}✓ running${NC}"
    else
        echo -e "${RED}✗ not running${NC}"
    fi
done

log_success "Health check completed"

# =============================================================================
# DISPLAY SERVICE ACCESS INFO
# =============================================================================

log_section "Service Access Information"

echo ""
echo -e "${CYAN}Services are accessible at:${NC}"
echo ""

port=8100
for service_config in "${SERVICES[@]}"; do
    IFS=':' read -r service_name db_name <<< "$service_config"
    echo "  ${service_name}-service: http://${SERVER_IP}:${port}/health"
    ((port++))
done

echo ""
log_success "All services deployed!"

echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Test service endpoints (curl http://${SERVER_IP}:8100/health)"
echo "  2. Run database migrations: ./scripts/deploy/run-migrations.sh"
echo "  3. Update mobile app with service URLs"
echo "  4. Check logs: docker logs agrischeme-auth-service"
