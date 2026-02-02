#!/bin/bash

# Automated Service Deployment via Coolify API (v4)
# Based on official Coolify API documentation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"
load_secrets "${SCRIPT_DIR}/.secrets/deployment.secrets"

# =============================================================================
# CONFIGURATION
# =============================================================================

SERVER_IP="${1}"
COOLIFY_API_TOKEN="${2}"
SERVER_UUID="${3:-0}"  # Default server ID

COOLIFY_URL="http://${SERVER_IP}:8000"
GITHUB_REPO="jajuok/agripro"
GITHUB_BRANCH="main"

# Services configuration
SERVICES=(
    "auth:services/auth:agrischeme_auth"
    "farmer:services/farmer:agrischeme_farmer"
    "farm:services/farm:agrischeme_farm"
    "financial:services/financial:agrischeme_financial"
    "gis:services/gis:agrischeme_gis"
    "market:services/market:agrischeme_market"
    "ai:services/ai:agrischeme_ai"
    "iot:services/iot:agrischeme_iot"
    "livestock:services/livestock:agrischeme_livestock"
    "task:services/task:agrischeme_task"
    "inventory:services/inventory:agrischeme_inventory"
    "notification:services/notification:agrischeme_notification"
    "traceability:services/traceability:agrischeme_traceability"
    "compliance:services/compliance:agrischeme_compliance"
    "integration:services/integration:agrischeme_integration"
)

# =============================================================================
# VALIDATION
# =============================================================================

log_section "Coolify API Service Deployment"

if [ -z "$SERVER_IP" ] || [ -z "$COOLIFY_API_TOKEN" ]; then
    log_error "Missing required parameters"
    echo ""
    echo "Usage: $0 <SERVER_IP> <COOLIFY_API_TOKEN> [SERVER_UUID]"
    echo ""
    echo "Get API Token from Coolify UI:"
    echo "  Settings → API Tokens → Create New Token"
    echo "  Note: If token shows as '3|token123', use only 'token123'"
    echo ""
    exit 1
fi

log_info "Server IP: $SERVER_IP"
log_info "Coolify URL: $COOLIFY_URL"
log_info "API Token: ${COOLIFY_API_TOKEN:0:20}..."
echo ""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

create_application() {
    local service_name=$1
    local base_dir=$2
    local db_name=$3

    log_step "Creating ${service_name}-service"
    log_info "API endpoint: ${COOLIFY_URL}/api/v1/applications/public"

    # Get database URL
    local db_container="agrischeme-${service_name}-db"
    local database_url="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${db_container}:5432/${db_name}"

    # Create application via API
    local payload=$(cat <<EOF
{
    "server_uuid": "${SERVER_UUID}",
    "project_uuid": "0",
    "environment_name": "production",
    "repository_url": "https://github.com/${GITHUB_REPO}",
    "branch": "${GITHUB_BRANCH}",
    "build_pack": "dockerfile",
    "base_directory": "${base_dir}",
    "dockerfile_location": "Dockerfile",
    "name": "${service_name}-service",
    "description": "AgriScheme ${service_name} service",
    "domains": "",
    "ports_exposes": "8000",
    "instant_deploy": false
}
EOF
)

    log_info "Sending API request to ${COOLIFY_URL}/api/v1/applications/public..."
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        --connect-timeout 10 \
        --max-time 30 \
        -X POST \
        "${COOLIFY_URL}/api/v1/applications/public" \
        -H "Authorization: ${COOLIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -d "$payload")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        # Extract UUID from response
        app_uuid=$(echo "$body" | jq -r '.uuid // .data.uuid // .id // .data.id' 2>/dev/null)

        if [ -n "$app_uuid" ] && [ "$app_uuid" != "null" ]; then
            log_success "Application created: $app_uuid"
            echo "$app_uuid"
            return 0
        else
            log_warning "Created but couldn't extract UUID"
            log_info "Response: $body"
            return 1
        fi
    else
        log_error "Failed (HTTP $http_code)"
        log_info "Response: ${body:0:300}"
        return 1
    fi
}

set_environment_variables() {
    local app_uuid=$1
    local service_name=$2
    local db_name=$3

    log_step "Setting environment variables for ${service_name}"

    local db_container="agrischeme-${service_name}-db"
    local database_url="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${db_container}:5432/${db_name}"

    # Build environment variables array
    local env_vars='[
        {
            "key": "DATABASE_URL",
            "value": "'"${database_url}"'",
            "is_preview": false,
            "is_build_time": false,
            "is_literal": true,
            "is_multiline": false,
            "is_shown_once": false
        },
        {
            "key": "REDIS_URL",
            "value": "redis://:'"${REDIS_PASSWORD}"'@agrischeme-redis:6379/0",
            "is_preview": false,
            "is_build_time": false,
            "is_literal": true,
            "is_multiline": false,
            "is_shown_once": false
        },
        {
            "key": "KAFKA_BOOTSTRAP_SERVERS",
            "value": "agrischeme-kafka:9092",
            "is_preview": false,
            "is_build_time": false,
            "is_literal": true,
            "is_multiline": false,
            "is_shown_once": false
        },
        {
            "key": "ENVIRONMENT",
            "value": "production",
            "is_preview": false,
            "is_build_time": false,
            "is_literal": true,
            "is_multiline": false,
            "is_shown_once": false
        },
        {
            "key": "LOG_LEVEL",
            "value": "INFO",
            "is_preview": false,
            "is_build_time": false,
            "is_literal": true,
            "is_multiline": false,
            "is_shown_once": false
        },
        {
            "key": "DEBUG",
            "value": "false",
            "is_preview": false,
            "is_build_time": false,
            "is_literal": true,
            "is_multiline": false,
            "is_shown_once": false
        },
        {
            "key": "CORS_ORIGINS",
            "value": "[\"*\"]",
            "is_preview": false,
            "is_build_time": false,
            "is_literal": true,
            "is_multiline": false,
            "is_shown_once": false
        }
    ]'

    # Add JWT variables for auth service
    if [ "$service_name" = "auth" ]; then
        env_vars=$(echo "$env_vars" | jq '. += [
            {
                "key": "JWT_SECRET_KEY",
                "value": "'"${JWT_SECRET_KEY}"'",
                "is_preview": false,
                "is_build_time": false,
                "is_literal": true,
                "is_multiline": false,
                "is_shown_once": false
            },
            {
                "key": "JWT_ALGORITHM",
                "value": "HS256",
                "is_preview": false,
                "is_build_time": false,
                "is_literal": true,
                "is_multiline": false,
                "is_shown_once": false
            },
            {
                "key": "ACCESS_TOKEN_EXPIRE_MINUTES",
                "value": "30",
                "is_preview": false,
                "is_build_time": false,
                "is_literal": true,
                "is_multiline": false,
                "is_shown_once": false
            },
            {
                "key": "REFRESH_TOKEN_EXPIRE_DAYS",
                "value": "7",
                "is_preview": false,
                "is_build_time": false,
                "is_literal": true,
                "is_multiline": false,
                "is_shown_once": false
            }
        ]')
    fi

    # Set environment variables via bulk API
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X PATCH \
        "${COOLIFY_URL}/api/v1/applications/${app_uuid}/envs/bulk" \
        -H "Authorization: ${COOLIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"data\": ${env_vars}}")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        log_success "Environment variables set"
        return 0
    else
        log_warning "Failed to set env vars (HTTP $http_code)"
        return 1
    fi
}

deploy_application() {
    local app_uuid=$1
    local service_name=$2

    log_step "Deploying ${service_name}-service"

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X POST \
        "${COOLIFY_URL}/api/v1/deploy" \
        -H "Authorization: ${COOLIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"uuid\": \"${app_uuid}\"}")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        log_success "Deployment triggered"
        return 0
    else
        log_warning "Failed to trigger deployment (HTTP $http_code)"
        return 1
    fi
}

# =============================================================================
# DEPLOY SERVICES
# =============================================================================

log_section "Deploying Services"

# Use regular arrays (compatible with bash 3.x)
app_uuids_names=()
app_uuids_values=()
success_count=0
failed_count=0
failed_services=()

for service_config in "${SERVICES[@]}"; do
    IFS=':' read -r service_name base_dir db_name <<< "$service_config"

    echo ""
    log_info "Processing ${service_name}-service..."

    # Create application
    app_uuid=$(create_application "$service_name" "$base_dir" "$db_name")

    if [ -n "$app_uuid" ] && [ "$app_uuid" != "null" ]; then
        app_uuids_names+=("$service_name")
        app_uuids_values+=("$app_uuid")

        # Set environment variables
        if set_environment_variables "$app_uuid" "$service_name" "$db_name"; then
            # Trigger deployment
            if deploy_application "$app_uuid" "$service_name"; then
                ((success_count++))
                log_success "${service_name}-service completed"
            else
                ((failed_count++))
                failed_services+=("$service_name")
            fi
        else
            ((failed_count++))
            failed_services+=("$service_name")
        fi
    else
        ((failed_count++))
        failed_services+=("$service_name")
    fi

    echo ""
    sleep 3  # Rate limiting
done

# =============================================================================
# SUMMARY
# =============================================================================

log_section "Deployment Summary"

echo ""
echo -e "${GREEN}Successful: ${success_count}/${#SERVICES[@]}${NC}"
echo -e "${RED}Failed: ${failed_count}/${#SERVICES[@]}${NC}"
echo ""

if [ ${#failed_services[@]} -gt 0 ]; then
    echo -e "${YELLOW}Failed services:${NC}"
    for svc in "${failed_services[@]}"; do
        echo "  ✗ $svc"
    done
    echo ""
fi

echo -e "${CYAN}Deployed services:${NC}"
for i in "${!app_uuids_names[@]}"; do
    echo "  ✓ ${app_uuids_names[$i]}-service (UUID: ${app_uuids_values[$i]})"
done

echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Check deployment status in Coolify UI: ${COOLIFY_URL}:8000"
echo "  2. Monitor build logs for each service"
echo "  3. Wait for all services to show 'Running' status (~10-15 min)"
echo "  4. Run migrations: ./scripts/deploy/run-migrations.sh"
echo ""

if [ $success_count -eq ${#SERVICES[@]} ]; then
    log_success "All services deployed successfully!"
else
    log_warning "Some services failed - check Coolify UI for details"
fi

# Save app UUIDs for future reference
echo "# Application UUIDs" > "${SCRIPT_DIR}/.secrets/app_uuids.txt"
for i in "${!app_uuids_names[@]}"; do
    echo "${app_uuids_names[$i]}=${app_uuids_values[$i]}" >> "${SCRIPT_DIR}/.secrets/app_uuids.txt"
done

log_info "App UUIDs saved to .secrets/app_uuids.txt"
