#!/bin/bash

# Redeploy Services - Clean up and deploy fresh
# This script combines cleanup and deployment in one command

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"

# =============================================================================
# CONFIGURATION
# =============================================================================

SERVER_IP="${1}"
COOLIFY_API_TOKEN="${2}"
SERVER_UUID="${3:-0}"

if [ -z "$SERVER_IP" ] || [ -z "$COOLIFY_API_TOKEN" ]; then
    log_error "Missing required parameters"
    echo ""
    echo "Usage: $0 <SERVER_IP> <COOLIFY_API_TOKEN> [SERVER_UUID]"
    echo ""
    echo "Example:"
    echo "  $0 213.32.19.116 your-api-token-here"
    exit 1
fi

log_section "AgriScheme Services - Clean Redeploy"

echo ""
echo -e "${CYAN}This will:${NC}"
echo "  1. Delete all existing AgriScheme services from Coolify"
echo "  2. Deploy all 15 services fresh"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    log_info "Cancelled"
    exit 0
fi

echo ""

# =============================================================================
# STEP 1: CLEANUP
# =============================================================================

log_section "Step 1: Cleanup Existing Services"

"${SCRIPT_DIR}/cleanup-services.sh" "$SERVER_IP" "$COOLIFY_API_TOKEN" || {
    log_warning "Cleanup had issues, but continuing..."
}

echo ""
echo -e "${YELLOW}Waiting 5 seconds before deployment...${NC}"
sleep 5
echo ""

# =============================================================================
# STEP 2: DEPLOY
# =============================================================================

log_section "Step 2: Deploy All Services"

"${SCRIPT_DIR}/deploy-services-coolify-api.sh" "$SERVER_IP" "$COOLIFY_API_TOKEN" "$SERVER_UUID"

# =============================================================================
# DONE
# =============================================================================

echo ""
log_success "Redeployment completed!"
echo ""
