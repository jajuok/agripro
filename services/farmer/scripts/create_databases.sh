#!/bin/bash

# Script to create AgriScheme Pro databases in Coolify PostgreSQL
# Usage: ./create_databases.sh [container_name] [postgres_user] [postgres_password]

set -e

# Configuration
CONTAINER_NAME="${1:-agrischeme-postgres}"
POSTGRES_USER="${2:-agrischeme_admin}"
POSTGRES_PASSWORD="${3:-P4fzWbXHbnODNUUKQkC1LbZy20ZMzNW6BKUSqozGnz8bbXS94peDj2WBoMb5N1oo}"
POSTGRES_DB="${4:-agrischeme_auth}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AgriScheme Pro - Database Creation Script         ║${NC}"
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
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

# Check if container exists
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}Error: Container '${CONTAINER_NAME}' not found or not running${NC}"
    echo "Available PostgreSQL containers:"
    docker ps --filter "ancestor=postgres" --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

echo -e "${BLUE}Using PostgreSQL container:${NC} ${CONTAINER_NAME}"
echo -e "${BLUE}PostgreSQL user:${NC} ${POSTGRES_USER}"
echo -e "${BLUE}Connecting to database:${NC} ${POSTGRES_DB}"
echo ""

# Function to create database
create_database() {
    local db_name=$1

    echo -n "Creating database: ${db_name}... "

    # Set password environment variable and create database
    docker exec -i "$CONTAINER_NAME" env PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE DATABASE ${db_name};" 2>&1

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed (may already exist)${NC}"
    fi
}

# Create all databases
echo "Creating databases..."
echo ""

for db in "${DATABASES[@]}"; do
    create_database "$db"
done

echo ""
echo -e "${GREEN}Database creation process completed!${NC}"
echo ""

# List all databases
echo -e "${BLUE}Listing all databases:${NC}"
docker exec -i "$CONTAINER_NAME" env PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\l" | grep agrischeme

echo ""
echo -e "${GREEN}Done!${NC}"
