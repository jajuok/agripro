#!/bin/bash

# Deploy Missing Database Containers
# Creates the 5 databases that were missing from initial deployment

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

if [ -z "$SERVER_IP" ] || [ -z "$SSH_KEY" ]; then
    log_error "Missing required parameters"
    echo "Usage: $0 <SERVER_IP> <SSH_KEY>"
    exit 1
fi

log_section "Deploying Missing Databases"

# Missing databases
MISSING_DBS=(
    "auth:agrischeme_auth"
    "farmer:agrischeme_farmer"
    "farm:agrischeme_farm"
    "financial:agrischeme_financial"
    "gis:agrischeme_gis"
)

# =============================================================================
# GENERATE DOCKER COMPOSE
# =============================================================================

log_step "Generating docker-compose for missing databases"

compose_content="version: '3.8'

networks:
  agrischeme-network:
    external: true

services:"

for db_config in "${MISSING_DBS[@]}"; do
    IFS=':' read -r service_name db_name <<< "$db_config"

    compose_content+="
  agrischeme-${service_name}-db:
    image: postgres:${POSTGRES_VERSION}
    container_name: agrischeme-${service_name}-db
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${db_name}
    volumes:
      - agrischeme-${service_name}-db-data:/var/lib/postgresql/data
    networks:
      - agrischeme-network
    restart: unless-stopped
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U ${POSTGRES_USER} -d ${db_name}']
      interval: 10s
      timeout: 5s
      retries: 5
"
done

compose_content+="
volumes:"

for db_config in "${MISSING_DBS[@]}"; do
    IFS=':' read -r service_name db_name <<< "$db_config"
    compose_content+="
  agrischeme-${service_name}-db-data:"
done

log_success "Docker compose generated"

# =============================================================================
# DEPLOY TO SERVER
# =============================================================================

log_step "Uploading docker-compose file to server"

remote_exec "$SERVER_IP" "$SSH_KEY" "cat > /opt/agrischeme/docker-compose-missing-dbs.yml" <<< "$compose_content"

log_success "File uploaded"

log_step "Starting database containers"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    cd /opt/agrischeme
    docker compose -f docker-compose-missing-dbs.yml up -d
"

log_success "Databases started"

# =============================================================================
# VERIFY
# =============================================================================

log_step "Verifying database health"

sleep 15  # Give databases time to initialize

for db_config in "${MISSING_DBS[@]}"; do
    IFS=':' read -r service_name db_name <<< "$db_config"
    container_name="agrischeme-${service_name}-db"

    echo -n "Checking ${container_name}... "

    status=$(remote_exec "$SERVER_IP" "$SSH_KEY" "docker ps --filter 'name=${container_name}' --format '{{.Status}}'" || echo "not running")

    if echo "$status" | grep -q "healthy"; then
        echo -e "${GREEN}✓ healthy${NC}"
    elif echo "$status" | grep -q "Up"; then
        echo -e "${YELLOW}⊙ running (waiting for healthy)${NC}"
    else
        echo -e "${RED}✗ not running${NC}"
    fi
done

echo ""
log_success "Missing databases deployed!"

echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Restart the failed services in Coolify UI"
echo "  2. Or use: ./scripts/deploy/trigger-deployments.sh"
echo "  3. All services should now start successfully"
echo ""
