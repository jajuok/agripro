#!/bin/bash

# Set Environment Variables for Existing Applications
# Use this to add env vars to applications that were created without them

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

# Strip the numeric prefix if present (e.g., "3|token" -> "token")
if [[ "$COOLIFY_API_TOKEN" == *"|"* ]]; then
    COOLIFY_API_TOKEN="${COOLIFY_API_TOKEN#*|}"
fi

if [ -z "$SERVER_IP" ] || [ -z "$COOLIFY_API_TOKEN" ]; then
    log_error "Missing required parameters"
    echo ""
    echo "Usage: $0 <SERVER_IP> <COOLIFY_API_TOKEN>"
    exit 1
fi

COOLIFY_URL="http://${SERVER_IP}:8000"

# Read app UUIDs from saved file
if [ ! -f "${SCRIPT_DIR}/.secrets/app_uuids.txt" ]; then
    log_error "App UUIDs file not found"
    log_info "Run the deployment script first to create applications"
    exit 1
fi

log_section "Setting Environment Variables"

# =============================================================================
# SET ENV VARS FOR EACH SERVICE
# =============================================================================

success_count=0
failed_count=0

while IFS='=' read -r service_name app_uuid; do
    # Skip comments and empty lines
    [[ "$service_name" =~ ^#.*$ ]] && continue
    [ -z "$service_name" ] && continue

    echo ""
    log_step "Setting env vars for ${service_name}-service"
    log_info "UUID: $app_uuid"

    # Get database name from service name
    case "$service_name" in
        auth) db_name="agrischeme_auth" ;;
        farmer) db_name="agrischeme_farmer" ;;
        farm) db_name="agrischeme_farm" ;;
        financial) db_name="agrischeme_financial" ;;
        gis) db_name="agrischeme_gis" ;;
        market) db_name="agrischeme_market" ;;
        ai) db_name="agrischeme_ai" ;;
        iot) db_name="agrischeme_iot" ;;
        livestock) db_name="agrischeme_livestock" ;;
        task) db_name="agrischeme_task" ;;
        inventory) db_name="agrischeme_inventory" ;;
        notification) db_name="agrischeme_notification" ;;
        traceability) db_name="agrischeme_traceability" ;;
        compliance) db_name="agrischeme_compliance" ;;
        integration) db_name="agrischeme_integration" ;;
        *) log_warning "Unknown service: $service_name"; continue ;;
    esac

    # Build URLs
    db_container="agrischeme-${service_name}-db"
    database_url="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${db_container}:5432/${db_name}"
    redis_url="redis://:${REDIS_PASSWORD}@agrischeme-redis:6379/0"

    # Build env vars using jq for proper escaping
    env_vars=$(jq -n \
        --arg db_url "$database_url" \
        --arg redis_url "$redis_url" \
        '[
            {
                "key": "DATABASE_URL",
                "value": $db_url,
                "is_preview": false,
                "is_build_time": false,
                "is_literal": true,
                "is_multiline": false,
                "is_shown_once": false
            },
            {
                "key": "REDIS_URL",
                "value": $redis_url,
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
        ]')

    # Add JWT vars for auth service
    if [ "$service_name" = "auth" ]; then
        env_vars=$(echo "$env_vars" | jq \
            --arg jwt_key "$JWT_SECRET_KEY" \
            '. += [
                {
                    "key": "JWT_SECRET_KEY",
                    "value": $jwt_key,
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

    # Set environment variables via API
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        --connect-timeout 10 \
        --max-time 30 \
        -X PATCH \
        "${COOLIFY_URL}/api/v1/applications/${app_uuid}/envs/bulk" \
        -H "Authorization: Bearer ${COOLIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"data\": ${env_vars}}")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        log_success "Environment variables set"
        ((success_count++))
    else
        body=$(echo "$response" | sed '/HTTP_CODE:/d')
        log_error "Failed (HTTP $http_code)"
        log_info "Response: ${body:0:200}"
        ((failed_count++))
    fi

    sleep 1  # Rate limiting

done < "${SCRIPT_DIR}/.secrets/app_uuids.txt"

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
log_section "Summary"

echo ""
echo -e "${GREEN}Successful: ${success_count}${NC}"
echo -e "${RED}Failed: ${failed_count}${NC}"
echo ""

if [ $success_count -gt 0 ]; then
    log_success "Environment variables configured!"
    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo "  1. Deploy applications in Coolify UI (or use instant_deploy)"
    echo "  2. Check Coolify UI: ${COOLIFY_URL}"
    echo "  3. Wait for services to build and start"
fi

echo ""
