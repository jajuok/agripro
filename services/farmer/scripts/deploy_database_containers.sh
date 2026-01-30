#!/bin/bash

# Script to deploy individual PostgreSQL containers for each AgriScheme database
# Usage: ./deploy_database_containers.sh

set +e  # Don't exit on errors, continue with all databases

# Configuration
POSTGRES_USER="agrischeme_admin"
POSTGRES_PASSWORD="P4fzWbXHbnODNUUKQkC1LbZy20ZMzNW6BKUSqozGnz8bbXS94peDj2WBoMb5N1oo"
POSTGRES_VERSION="16-alpine"
NETWORK_NAME="agrischeme-network"
BASE_PORT=5432

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AgriScheme Pro - Database Container Deployment    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Database configurations: service_name:database_name:port
DATABASES=(
    "market:agrischeme_market:5440"
    "ai:agrischeme_ai:5441"
    "iot:agrischeme_iot:5442"
    "livestock:agrischeme_livestock:5443"
    "task:agrischeme_task:5444"
    "inventory:agrischeme_inventory:5445"
    "notification:agrischeme_notification:5446"
    "traceability:agrischeme_traceability:5447"
    "compliance:agrischeme_compliance:5448"
    "integration:agrischeme_integration:5449"
)

# Create Docker network if it doesn't exist
echo -n "Checking Docker network... "
if docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    echo -e "${YELLOW}already exists${NC}"
else
    docker network create "$NETWORK_NAME"
    echo -e "${GREEN}✓ created${NC}"
fi
echo ""

# Function to deploy a PostgreSQL container
deploy_container() {
    local service_name=$1
    local db_name=$2
    local port=$3
    local container_name="agrischeme-${service_name}-db"

    echo -n "Deploying ${container_name} (${db_name}:${port})... "

    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${YELLOW}already exists${NC}"

        # Check if it's running
        if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
            echo -n "  Starting existing container... "
            docker start "$container_name" >/dev/null 2>&1
            echo -e "${GREEN}✓ started${NC}"
        fi
        return 0
    fi

    # Create new container
    create_output=$(docker run -d \
        --name "$container_name" \
        --network "$NETWORK_NAME" \
        -e POSTGRES_DB="$db_name" \
        -e POSTGRES_USER="$POSTGRES_USER" \
        -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        -p "${port}:5432" \
        -v "${container_name}-data:/var/lib/postgresql/data" \
        --restart unless-stopped \
        --health-cmd="pg_isready -U ${POSTGRES_USER} -d ${db_name}" \
        --health-interval=10s \
        --health-timeout=5s \
        --health-retries=5 \
        postgres:${POSTGRES_VERSION} 2>&1)

    create_status=$?

    if [ $create_status -eq 0 ]; then
        echo -e "${GREEN}✓ created${NC}"
        echo "  Database: ${db_name}"
        echo "  Port: ${port}"
        echo "  Network: ${NETWORK_NAME}"
        return 0
    else
        echo -e "${RED}✗ failed${NC}"
        echo "  Error: ${create_output}"
        return 1
    fi
}

# Deploy all database containers
echo -e "${YELLOW}Deploying database containers...${NC}"
echo ""

success_count=0
failed_count=0

for db_config in "${DATABASES[@]}"; do
    IFS=':' read -r service_name db_name port <<< "$db_config"

    if deploy_container "$service_name" "$db_name" "$port"; then
        ((success_count++))
    else
        ((failed_count++))
    fi

    echo ""
    sleep 1
done

# Wait for containers to be healthy
echo -e "${YELLOW}Waiting for containers to be healthy...${NC}"
sleep 5

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Deployment Summary                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}Successful: ${success_count}${NC}"
echo -e "${RED}Failed: ${failed_count}${NC}"
echo ""

# List all AgriScheme PostgreSQL containers
echo -e "${BLUE}AgriScheme PostgreSQL containers:${NC}"
docker ps --filter "name=agrischeme-*-db" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${GREEN}Done!${NC}"
echo ""

# Display connection strings
echo -e "${BLUE}Connection Strings (for services):${NC}"
echo ""
for db_config in "${DATABASES[@]}"; do
    IFS=':' read -r service_name db_name port <<< "$db_config"
    container_name="agrischeme-${service_name}-db"
    echo -e "${YELLOW}${service_name}-service:${NC}"
    echo "  DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${container_name}:5432/${db_name}"
    echo "  External (host): postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${port}/${db_name}"
    echo ""
done

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Verify all containers are healthy: docker ps --filter 'name=agrischeme-*-db'"
echo "2. Test connection to a database: docker exec -it agrischeme-market-db psql -U ${POSTGRES_USER} -d agrischeme_market"
echo "3. Update service environment variables with the DATABASE_URL values above"
