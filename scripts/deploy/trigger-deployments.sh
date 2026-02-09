#!/bin/bash

# Trigger Deployments for All Services
# Use this after pushing code changes to redeploy all applications

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"

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

log_section "Triggering Deployments"

# =============================================================================
# TRIGGER DEPLOYMENTS
# =============================================================================

success_count=0
failed_count=0

while IFS='=' read -r service_name app_uuid; do
    # Skip comments and empty lines
    [[ "$service_name" =~ ^#.*$ ]] && continue
    [ -z "$service_name" ] && continue

    echo ""
    log_step "Deploying ${service_name}-service"
    log_info "UUID: $app_uuid"

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        --connect-timeout 10 \
        --max-time 30 \
        -X POST \
        "${COOLIFY_URL}/api/v1/deploy" \
        -H "Authorization: Bearer ${COOLIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"uuid\": \"${app_uuid}\", \"force\": true}")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        log_success "Deployment triggered"
        ((success_count++))
    else
        body=$(echo "$response" | sed '/HTTP_CODE:/d')
        log_error "Failed (HTTP $http_code)"
        log_info "Response: ${body:0:200}"
        ((failed_count++))
    fi

    sleep 2  # Rate limiting

done < "${SCRIPT_DIR}/.secrets/app_uuids.txt"

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
log_section "Summary"

echo ""
echo -e "${GREEN}Triggered: ${success_count}${NC}"
echo -e "${RED}Failed: ${failed_count}${NC}"
echo ""

if [ $success_count -gt 0 ]; then
    log_success "Deployments triggered!"
    echo ""
    echo -e "${CYAN}What's Happening:${NC}"
    echo "  • Coolify is pulling latest code from GitHub"
    echo "  • Building Docker images for each service"
    echo "  • Starting containers with environment variables"
    echo ""
    echo -e "${CYAN}Monitor Progress:${NC}"
    echo "  • Open Coolify UI: ${COOLIFY_URL}"
    echo "  • Check each service's build logs"
    echo "  • Wait for 'Running' and 'Healthy' status (~5-10 min per service)"
    echo ""
    echo -e "${CYAN}After All Services Are Running:${NC}"
    echo "  • Run database migrations for each service"
    echo "  • Test service endpoints: http://${SERVER_IP}:<port>/health"
fi

echo ""
