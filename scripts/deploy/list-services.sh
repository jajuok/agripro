#!/bin/bash

# List All Services in Coolify
# Simple script to see what's currently deployed

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
    echo ""
    echo "Example:"
    echo "  $0 213.32.19.116 your-api-token-here"
    exit 1
fi

COOLIFY_URL="http://${SERVER_IP}:8000"

log_section "Coolify Services List"

log_info "Fetching from: ${COOLIFY_URL}/api/v1/applications"
echo ""

# =============================================================================
# FETCH APPLICATIONS
# =============================================================================

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
    echo ""
    echo "Response:"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    exit 1
fi

# =============================================================================
# DISPLAY APPLICATIONS
# =============================================================================

app_count=$(echo "$body" | jq '. | length' 2>/dev/null || echo "0")

if [ "$app_count" = "0" ]; then
    log_info "No applications found"
    exit 0
fi

log_success "Found $app_count application(s)"
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
printf "%-5s %-30s %-40s %s\n" "No." "Name" "UUID" "Status"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

for i in $(seq 0 $((app_count - 1))); do
    name=$(echo "$body" | jq -r ".[$i].name // \"N/A\"" 2>/dev/null)
    uuid=$(echo "$body" | jq -r ".[$i].uuid // .[$i].id // \"N/A\"" 2>/dev/null)
    status=$(echo "$body" | jq -r ".[$i].status // \"unknown\"" 2>/dev/null)

    # Truncate UUID for display
    uuid_short="${uuid:0:36}"

    printf "%-5s %-30s %-40s %s\n" "$((i + 1))." "$name" "$uuid_short" "$status"
done

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Show AgriScheme services specifically
agrischeme_count=0
for i in $(seq 0 $((app_count - 1))); do
    name=$(echo "$body" | jq -r ".[$i].name // \"\"" 2>/dev/null)
    if [[ "$name" == *"-service"* ]] || [[ "$name" == *"agrischeme"* ]]; then
        ((agrischeme_count++))
    fi
done

if [ $agrischeme_count -gt 0 ]; then
    echo -e "${YELLOW}AgriScheme Services: ${agrischeme_count}${NC}"
else
    echo -e "${GREEN}No AgriScheme services found${NC}"
fi

echo ""
echo "To delete all services, run:"
echo "  ./scripts/deploy/cleanup-services.sh ${SERVER_IP} <API_TOKEN>"
echo ""
echo "To redeploy fresh, run:"
echo "  ./scripts/deploy/redeploy-services.sh ${SERVER_IP} <API_TOKEN>"
echo ""
