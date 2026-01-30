#!/bin/bash

# Script to deploy PostgreSQL databases to Coolify project via API
# Usage: ./deploy_databases_to_project.sh <API_TOKEN> <PROJECT_UUID> <ENVIRONMENT_NAME>

set +e

# Configuration
COOLIFY_API_TOKEN="${1}"
PROJECT_UUID="${2}"
ENVIRONMENT_NAME="${3:-production}"
COOLIFY_URL="${4:-http://localhost}"

POSTGRES_USER="agrischeme_admin"
POSTGRES_PASSWORD="P4fzWbXHbnODNUUKQkC1LbZy20ZMzNW6BKUSqozGnz8bbXS94peDj2WBoMb5N1oo"
POSTGRES_VERSION="16"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Deploy Databases to Coolify Project               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Validate inputs
if [ -z "$COOLIFY_API_TOKEN" ] || [ -z "$PROJECT_UUID" ]; then
    echo -e "${RED}Error: Missing required parameters${NC}"
    echo ""
    echo "Usage: $0 <API_TOKEN> <PROJECT_UUID> [ENVIRONMENT_NAME] [COOLIFY_URL]"
    echo ""
    echo -e "${YELLOW}How to get API Token:${NC}"
    echo "  1. Open Coolify UI → Settings → API Tokens"
    echo "  2. Create token with 'Database' permissions"
    echo ""
    echo -e "${YELLOW}How to get Project UUID:${NC}"
    echo "  1. Go to your 'agrischeme-infra' project"
    echo "  2. Look at URL: /project/<UUID>"
    echo "  3. Or run: curl -H 'Authorization: Bearer <TOKEN>' ${COOLIFY_URL}/api/v1/projects"
    exit 1
fi

echo -e "${BLUE}Coolify URL:${NC} ${COOLIFY_URL}"
echo -e "${BLUE}Project UUID:${NC} ${PROJECT_UUID}"
echo -e "${BLUE}Environment:${NC} ${ENVIRONMENT_NAME}"
echo ""

# Database configurations
declare -A DATABASES=(
    ["market"]="agrischeme_market"
    ["ai"]="agrischeme_ai"
    ["iot"]="agrischeme_iot"
    ["livestock"]="agrischeme_livestock"
    ["task"]="agrischeme_task"
    ["inventory"]="agrischeme_inventory"
    ["notification"]="agrischeme_notification"
    ["traceability"]="agrischeme_traceability"
    ["compliance"]="agrischeme_compliance"
    ["integration"]="agrischeme_integration"
)

# Function to deploy a database via Coolify API
deploy_database() {
    local service_name=$1
    local db_name=$2

    echo -n "Deploying ${service_name}-db (${db_name})... "

    # Create JSON payload
    local payload=$(cat <<EOF
{
    "project_uuid": "${PROJECT_UUID}",
    "environment_name": "${ENVIRONMENT_NAME}",
    "type": "postgresql",
    "name": "${service_name}-db",
    "description": "PostgreSQL database for ${service_name} service",
    "postgres_user": "${POSTGRES_USER}",
    "postgres_password": "${POSTGRES_PASSWORD}",
    "postgres_db": "${db_name}",
    "postgres_initdb_args": "",
    "postgres_host_auth_method": "scram-sha-256",
    "postgres_conf": "",
    "image": "postgres:${POSTGRES_VERSION}",
    "is_public": false,
    "instant_deploy": true
}
EOF
)

    # Make API call
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
        -X POST \
        -H "Authorization: Bearer ${COOLIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -d "$payload" \
        "${COOLIFY_URL}/api/v1/databases/postgresql")

    http_code=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS:/d')

    if [ "$http_code" -eq 201 ] || [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ created${NC}"
        # Extract UUID if available
        uuid=$(echo "$body" | grep -o '"uuid":"[^"]*' | cut -d'"' -f4)
        if [ -n "$uuid" ]; then
            echo "  UUID: ${uuid}"
        fi
        return 0
    else
        echo -e "${RED}✗ failed (HTTP ${http_code})${NC}"
        echo "  Response: ${body}" | head -c 200
        return 1
    fi
}

# Deploy all databases
echo -e "${YELLOW}Deploying ${#DATABASES[@]} PostgreSQL databases...${NC}"
echo ""

success_count=0
failed_count=0

for service_name in "${!DATABASES[@]}"; do
    db_name="${DATABASES[$service_name]}"

    if deploy_database "$service_name" "$db_name"; then
        ((success_count++))
    else
        ((failed_count++))
    fi

    echo ""
    sleep 2  # Rate limiting between API calls
done

# Summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Deployment Summary                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}Successful: ${success_count}${NC}"
echo -e "${RED}Failed: ${failed_count}${NC}"
echo ""

echo -e "${GREEN}Done!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Check Coolify UI → Projects → agrischeme-infra → Resources"
echo "2. Verify all databases show as 'healthy'"
echo "3. Get internal connection URLs from each database's details"
echo "4. Update service environment variables with DATABASE_URL"
