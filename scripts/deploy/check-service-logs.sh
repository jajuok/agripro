#!/bin/bash

# Check Service Logs via API
# Fetches deployment logs to diagnose issues

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"

# =============================================================================
# CONFIGURATION
# =============================================================================

SERVER_IP="${1}"
COOLIFY_API_TOKEN="${2}"
SERVICE_FILTER="${3:-}"  # Optional: specific service name

# Strip the numeric prefix if present
if [[ "$COOLIFY_API_TOKEN" == *"|"* ]]; then
    COOLIFY_API_TOKEN="${COOLIFY_API_TOKEN#*|}"
fi

if [ -z "$SERVER_IP" ] || [ -z "$COOLIFY_API_TOKEN" ]; then
    log_error "Missing required parameters"
    echo ""
    echo "Usage: $0 <SERVER_IP> <COOLIFY_API_TOKEN> [SERVICE_NAME]"
    echo ""
    echo "Examples:"
    echo "  $0 213.32.19.116 TOKEN              # Check all services"
    echo "  $0 213.32.19.116 TOKEN auth         # Check only auth service"
    exit 1
fi

COOLIFY_URL="http://${SERVER_IP}:8000"

# Read app UUIDs
if [ ! -f "${SCRIPT_DIR}/.secrets/app_uuids.txt" ]; then
    log_error "App UUIDs file not found"
    exit 1
fi

log_section "Checking Service Status and Logs"

# =============================================================================
# CHECK EACH SERVICE
# =============================================================================

while IFS='=' read -r service_name app_uuid; do
    # Skip comments and empty lines
    [[ "$service_name" =~ ^#.*$ ]] && continue
    [ -z "$service_name" ] && continue

    # Filter if specific service requested
    if [ -n "$SERVICE_FILTER" ] && [ "$service_name" != "$SERVICE_FILTER" ]; then
        continue
    fi

    echo ""
    echo "========================================================================"
    log_info "Checking ${service_name}-service (UUID: $app_uuid)"
    echo "========================================================================"
    echo ""

    # Get application details
    response=$(curl -s \
        -X GET \
        "${COOLIFY_URL}/api/v1/applications/${app_uuid}" \
        -H "Authorization: Bearer ${COOLIFY_API_TOKEN}" \
        -H "Accept: application/json")

    # Extract status
    status=$(echo "$response" | jq -r '.status // "unknown"' 2>/dev/null)
    echo "Status: $status"
    echo ""

    # If not running, show the error/logs
    if [ "$status" != "running" ]; then
        echo "Last deployment logs:"
        echo "------------------------------------------------------------------------"

        # Try to get logs (API endpoint may vary)
        log_response=$(curl -s \
            -X GET \
            "${COOLIFY_URL}/api/v1/applications/${app_uuid}/logs" \
            -H "Authorization: Bearer ${COOLIFY_API_TOKEN}" \
            -H "Accept: application/json" 2>/dev/null || echo '{"error":"Could not fetch logs"}')

        # Display logs
        echo "$log_response" | jq -r '.logs // .data // . | if type=="string" then . else tostring end' 2>/dev/null | tail -50
        echo "------------------------------------------------------------------------"
    else
        log_success "${service_name} is running"
    fi

    echo ""

done < "${SCRIPT_DIR}/.secrets/app_uuids.txt"

echo ""
log_info "Check complete. Review the logs above for errors."
echo ""
