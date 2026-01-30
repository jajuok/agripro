#!/bin/bash

# Phase 3: DNS Configuration Helper
# Provides instructions for DNS setup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"

SERVER_IP=$1
DOMAIN=$2
SSH_KEY=$3

log_section "Phase 3: DNS Configuration"

log_info "DNS records need to be configured manually in your domain registrar"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                DNS Configuration Instructions                ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Add the following DNS A records in your domain registrar:${NC}"
echo ""
echo "┌────────────────────────────────────────────────────────────┐"
echo "│ Type │ Name              │ Value          │ TTL            │"
echo "├────────────────────────────────────────────────────────────┤"
echo "│ A    │ @                 │ ${SERVER_IP}   │ 300 (5 min)    │"
echo "│ A    │ ${COOLIFY_SUBDOMAIN}          │ ${SERVER_IP}   │ 300 (5 min)    │"
echo "│ A    │ ${API_SUBDOMAIN}              │ ${SERVER_IP}   │ 300 (5 min)    │"
echo "│ A    │ *.${API_SUBDOMAIN}            │ ${SERVER_IP}   │ 300 (5 min)    │"
echo "│ CNAME│ www               │ @              │ 300 (5 min)    │"
echo "└────────────────────────────────────────────────────────────┘"
echo ""
echo -e "${GREEN}This will create the following URLs:${NC}"
echo "  • https://${DOMAIN}"
echo "  • https://${COOLIFY_SUBDOMAIN}.${DOMAIN} (Coolify UI)"
echo "  • https://${API_SUBDOMAIN}.${DOMAIN} (API Gateway)"
echo "  • https://auth.${API_SUBDOMAIN}.${DOMAIN} (Auth Service)"
echo "  • https://farmer.${API_SUBDOMAIN}.${DOMAIN} (Farmer Service)"
echo "  • https://farm.${API_SUBDOMAIN}.${DOMAIN} (Farm Service)"
echo "  • ... (and all other services)"
echo ""
echo -e "${YELLOW}Note:${NC} DNS propagation may take up to 48 hours, but usually completes within 15-30 minutes."
echo ""

# =============================================================================
# DNS CHECK
# =============================================================================

log_step "Checking DNS configuration"

echo ""
echo -e "${YELLOW}Checking DNS records...${NC}"
echo ""

check_dns_record() {
    local record=$1
    local expected_ip=$2

    echo -n "Checking ${record}... "

    # Try to resolve the DNS record
    resolved_ip=$(dig +short "$record" @8.8.8.8 2>/dev/null | tail -n1)

    if [ "$resolved_ip" = "$expected_ip" ]; then
        echo -e "${GREEN}✓ Configured${NC} (${resolved_ip})"
        return 0
    else
        if [ -z "$resolved_ip" ]; then
            echo -e "${RED}✗ Not configured${NC}"
        else
            echo -e "${YELLOW}⚠ Resolves to ${resolved_ip} (expected ${expected_ip})${NC}"
        fi
        return 1
    fi
}

# Check if dig is available
if ! command_exists dig; then
    log_warning "dig command not found, skipping DNS verification"
    log_info "You can manually verify DNS records using: dig ${DOMAIN}"
else
    check_dns_record "${DOMAIN}" "${SERVER_IP}" || true
    check_dns_record "${COOLIFY_SUBDOMAIN}.${DOMAIN}" "${SERVER_IP}" || true
    check_dns_record "${API_SUBDOMAIN}.${DOMAIN}" "${SERVER_IP}" || true
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Action Required:${NC}"
echo ""
echo "  1. Add the DNS records shown above to your domain registrar"
echo "  2. Wait 5-10 minutes for DNS propagation"
echo "  3. Verify the records are configured correctly"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

read -p "Press Enter once you have configured the DNS records..."

# =============================================================================
# VERIFY DNS
# =============================================================================

log_step "Verifying DNS configuration"

if command_exists dig; then
    all_configured=true

    check_dns_record "${DOMAIN}" "${SERVER_IP}" || all_configured=false
    check_dns_record "${COOLIFY_SUBDOMAIN}.${DOMAIN}" "${SERVER_IP}" || all_configured=false
    check_dns_record "${API_SUBDOMAIN}.${DOMAIN}" "${SERVER_IP}" || all_configured=false

    if [ "$all_configured" = true ]; then
        log_success "All DNS records are configured correctly"
    else
        log_warning "Some DNS records are not configured yet"
        log_info "Deployment will continue, but SSL certificates may fail until DNS is fully propagated"

        if ! confirm_action "Continue anyway?"; then
            exit 1
        fi
    fi
else
    log_warning "Unable to verify DNS records (dig not available)"
    log_info "Please ensure DNS records are configured before proceeding"
fi

log_success "Phase 3 completed: DNS configuration ready"
