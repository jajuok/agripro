#!/bin/bash

# Cleanup Script - Delete All AgriScheme Services from Coolify
# Use this before running a fresh deployment

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
    echo ""
    echo "Example:"
    echo "  $0 213.32.19.116 your-api-token-here"
    exit 1
fi

COOLIFY_URL="http://${SERVER_IP}:8000"

log_section "Coolify Service Cleanup"

log_info "Server IP: $SERVER_IP"
log_info "Coolify URL: $COOLIFY_URL"
log_info "API Token: ${COOLIFY_API_TOKEN:0:20}..."
echo ""

# =============================================================================
# LIST ALL APPLICATIONS
# =============================================================================

log_step "Fetching all applications"

response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    --connect-timeout 10 \
    --max-time 30 \
    -X GET \
    "${COOLIFY_URL}/api/v1/applications" \
    -H "Authorization: Bearer ${COOLIFY_API_TOKEN}" \
    -H "Accept: application/json")

http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_CODE:/d')

if [ "$http_code" != "200" ]; then
    log_error "Failed to fetch applications (HTTP $http_code)"
    log_info "Response: $body"
    exit 1
fi

log_success "Applications fetched"

# Parse application list
app_count=$(echo "$body" | jq '. | length' 2>/dev/null || echo "0")

if [ "$app_count" = "0" ]; then
    log_info "No applications found"
    exit 0
fi

log_info "Found $app_count application(s)"
echo ""

# Extract AgriScheme service UUIDs and names
agrischeme_uuids=()
agrischeme_names=()

# Parse each application
for i in $(seq 0 $((app_count - 1))); do
    name=$(echo "$body" | jq -r ".[$i].name // empty" 2>/dev/null || echo "")
    uuid=$(echo "$body" | jq -r ".[$i].uuid // .[$i].id // empty" 2>/dev/null || echo "")

    # Check if it's an AgriScheme service (contains "service" or "agrischeme")
    if [[ "$name" == *"-service"* ]] || [[ "$name" == *"agrischeme"* ]]; then
        if [ -n "$uuid" ] && [ "$uuid" != "null" ]; then
            agrischeme_uuids+=("$uuid")
            agrischeme_names+=("$name")
            log_info "Found: $name (UUID: $uuid)"
        fi
    fi
done

echo ""

if [ ${#agrischeme_uuids[@]} -eq 0 ]; then
    log_info "No AgriScheme services found to delete"
    exit 0
fi

log_warning "Found ${#agrischeme_uuids[@]} AgriScheme service(s) to delete"
echo ""

# =============================================================================
# CONFIRM DELETION
# =============================================================================

echo -e "${YELLOW}Services to be deleted:${NC}"
for i in "${!agrischeme_names[@]}"; do
    echo "  - ${agrischeme_names[$i]}"
done
echo ""

read -p "Are you sure you want to delete these services? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    log_info "Deletion cancelled"
    exit 0
fi

echo ""

# =============================================================================
# DELETE SERVICES
# =============================================================================

log_section "Deleting Services"

success_count=0
failed_count=0

for i in "${!agrischeme_uuids[@]}"; do
    uuid="${agrischeme_uuids[$i]}"
    name="${agrischeme_names[$i]}"

    log_step "Deleting $name"

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        --connect-timeout 10 \
        --max-time 30 \
        -X DELETE \
        "${COOLIFY_URL}/api/v1/applications/${uuid}" \
        -H "Authorization: Bearer ${COOLIFY_API_TOKEN}" \
        -H "Accept: application/json")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)

    if [ "$http_code" = "200" ] || [ "$http_code" = "204" ]; then
        log_success "$name deleted"
        ((success_count++))
    else
        log_error "$name failed (HTTP $http_code)"
        ((failed_count++))
    fi

    sleep 1  # Rate limiting
done

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
log_section "Cleanup Summary"

echo ""
echo -e "${GREEN}Deleted: ${success_count}/${#agrischeme_uuids[@]}${NC}"
echo -e "${RED}Failed: ${failed_count}/${#agrischeme_uuids[@]}${NC}"
echo ""

if [ $success_count -eq ${#agrischeme_uuids[@]} ]; then
    log_success "All services deleted successfully!"
    echo ""
    echo -e "${CYAN}Ready to deploy fresh!${NC}"
    echo ""
    echo "Run deployment:"
    echo "  ./scripts/deploy/deploy-services-coolify-api.sh ${SERVER_IP} ${COOLIFY_API_TOKEN}"
else
    log_warning "Some services failed to delete"
    echo ""
    echo "Check Coolify UI for remaining services: ${COOLIFY_URL}"
fi

echo ""
