#!/bin/bash

# Phase 4: Deploy Databases
# Creates PostgreSQL containers for each service via Coolify UI automation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"
load_secrets "${SCRIPT_DIR}/.secrets/deployment.secrets"

SERVER_IP=$1
DOMAIN=$2
SSH_KEY=$3

log_section "Phase 4: Database Deployment"

log_info "Deploying ${#DATABASES[@]} PostgreSQL databases"

# =============================================================================
# CREATE DOCKER COMPOSE FOR ALL DATABASES
# =============================================================================

log_step "Cleaning up existing database containers (if any)"

# Stop and remove existing containers using simpler commands
remote_exec "$SERVER_IP" "$SSH_KEY" "
    docker ps -a --filter 'name=agrischeme-' --format '{{.Names}}' | grep '\-db$' | xargs -r docker rm -f 2>/dev/null || true
" || true

# Remove old compose file
remote_exec "$SERVER_IP" "$SSH_KEY" "rm -f /opt/agrischeme/docker-compose-databases.yml" || true

log_success "Cleanup completed"

log_step "Creating database containers"

# Generate docker-compose content
compose_content="networks:
  agrischeme-network:
    external: false

services:
"

for db_config in "${DATABASES[@]}"; do
    IFS=':' read -r service_name db_name <<< "$db_config"
    compose_content+="
  agrischeme-${service_name}-db:
    image: postgres:${POSTGRES_VERSION}
    container_name: agrischeme-${service_name}-db
    environment:
      POSTGRES_DB: ${db_name}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ${service_name}-db-data:/var/lib/postgresql/data
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
volumes:
"

for db_config in "${DATABASES[@]}"; do
    IFS=':' read -r service_name db_name <<< "$db_config"
    compose_content+="  ${service_name}-db-data:
"
done

# Write docker-compose file to server
remote_exec "$SERVER_IP" "$SSH_KEY" "cat > /opt/agrischeme/docker-compose-databases.yml" <<< "$compose_content"

# Deploy databases
log_step "Starting database containers"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    cd /opt/agrischeme
    docker compose -f docker-compose-databases.yml up -d
"

log_success "Database containers started"

# =============================================================================
# WAIT FOR DATABASES TO BE HEALTHY
# =============================================================================

log_step "Waiting for databases to be healthy"

for db_config in "${DATABASES[@]}"; do
    IFS=':' read -r service_name db_name <<< "$db_config"
    container_name="agrischeme-${service_name}-db"

    echo -n "Waiting for ${container_name}... "

    max_attempts=60
    for ((i=1; i<=max_attempts; i++)); do
        health_status=$(remote_exec "$SERVER_IP" "$SSH_KEY" "docker inspect --format='{{.State.Health.Status}}' $container_name 2>/dev/null || echo 'starting'")

        if [ "$health_status" = "healthy" ]; then
            echo -e "${GREEN}✓ healthy${NC}"
            break
        fi

        if [ $i -eq $max_attempts ]; then
            echo -e "${RED}✗ failed${NC}"
            log_error "${container_name} failed to become healthy"
            exit 1
        fi

        sleep 2
    done
done

log_success "All databases are healthy"

# =============================================================================
# VERIFY DATABASE CONNECTIONS
# =============================================================================

log_step "Verifying database connections"

for db_config in "${DATABASES[@]}"; do
    IFS=':' read -r service_name db_name <<< "$db_config"
    container_name="agrischeme-${service_name}-db"

    echo -n "Testing ${db_name}... "

    if remote_exec "$SERVER_IP" "$SSH_KEY" "docker exec ${container_name} psql -U ${POSTGRES_USER} -d ${db_name} -c 'SELECT 1;' > /dev/null 2>&1"; then
        echo -e "${GREEN}✓ connected${NC}"
    else
        echo -e "${RED}✗ failed${NC}"
        log_error "Failed to connect to ${db_name}"
        exit 1
    fi
done

log_success "All database connections verified"

# =============================================================================
# SAVE DATABASE CONNECTION STRINGS
# =============================================================================

log_step "Generating database connection strings"

SECRETS_FILE="${SCRIPT_DIR}/.secrets/deployment.secrets"

for db_config in "${DATABASES[@]}"; do
    IFS=':' read -r service_name db_name <<< "$db_config"
    container_name="agrischeme-${service_name}-db"

    # Internal connection string (for Docker network)
    internal_url="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${container_name}:5432/${db_name}"

    # Save to secrets file
    save_secret "${service_name}_DATABASE_URL" "$internal_url" "$SECRETS_FILE"
done

log_success "Database connection strings saved"

# =============================================================================
# DISPLAY SUMMARY
# =============================================================================

log_success "Phase 4 completed: All databases deployed"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              Database Deployment Summary                     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

remote_exec "$SERVER_IP" "$SSH_KEY" "
    docker ps --filter 'name=agrischeme-*-db' --format 'table {{.Names}}\t{{.Status}}'
"

echo ""
log_info "Connection strings saved to: .secrets/deployment.secrets"
