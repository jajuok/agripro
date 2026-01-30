#!/bin/bash

# Script to create AgriScheme Pro databases in a PostgreSQL container
# Usage: ./create_databases_simple.sh <container_name>

set -e

# Configuration
CONTAINER_NAME="${1}"
POSTGRES_USER="agrischeme_admin"
POSTGRES_PASSWORD="P4fzWbXHbnODNUUKQkC1LbZy20ZMzNW6BKUSqozGnz8bbXS94peDj2WBoMb5N1oo"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AgriScheme Pro - Database Creation Script         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Validate input
if [ -z "$CONTAINER_NAME" ]; then
    echo -e "${RED}Error: Container name required${NC}"
    echo ""
    echo "Usage: $0 <container_name>"
    echo ""
    echo -e "${YELLOW}Available PostgreSQL containers:${NC}"
    docker ps --filter "ancestor=postgres:16-alpine" --format "{{.Names}}"
    echo ""
    exit 1
fi

# Check if container exists and is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Error: Container '${CONTAINER_NAME}' not found or not running${NC}"
    echo ""
    echo -e "${YELLOW}Available PostgreSQL containers:${NC}"
    docker ps --filter "ancestor=postgres:16-alpine" --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

echo -e "${BLUE}Container:${NC} ${CONTAINER_NAME}"
echo -e "${BLUE}User:${NC} ${POSTGRES_USER}"
echo ""

# Databases to create
DATABASES=(
    "agrischeme_market"
    "agrischeme_ai"
    "agrischeme_iot"
    "agrischeme_livestock"
    "agrischeme_task"
    "agrischeme_inventory"
    "agrischeme_notification"
    "agrischeme_traceability"
    "agrischeme_compliance"
    "agrischeme_integration"
)

echo -e "${YELLOW}Creating ${#DATABASES[@]} databases...${NC}"
echo ""

# Create each database
for db_name in "${DATABASES[@]}"; do
    echo -n "  ${db_name}... "

    result=$(docker exec -i "$CONTAINER_NAME" \
        env PGPASSWORD="$POSTGRES_PASSWORD" \
        psql -U "$POSTGRES_USER" -d postgres \
        -c "CREATE DATABASE ${db_name};" 2>&1)

    if echo "$result" | grep -q "already exists"; then
        echo -e "${YELLOW}already exists${NC}"
    elif echo "$result" | grep -q "CREATE DATABASE"; then
        echo -e "${GREEN}✓ created${NC}"
    else
        echo -e "${RED}✗ failed${NC}"
        echo "  Error: $result"
    fi
done

echo ""
echo -e "${GREEN}Database creation completed!${NC}"
echo ""

# List all databases
echo -e "${BLUE}All databases in container:${NC}"
docker exec -i "$CONTAINER_NAME" \
    env PGPASSWORD="$POSTGRES_PASSWORD" \
    psql -U "$POSTGRES_USER" -d postgres \
    -c "\l" | grep -E "Name|agrischeme" | head -15

echo ""
echo -e "${GREEN}Done!${NC}"
