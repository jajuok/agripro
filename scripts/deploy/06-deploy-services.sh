#!/bin/bash

# Phase 6: Deploy Microservices
# Note: This requires GitHub integration to be set up in Coolify UI

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"

SERVER_IP=$1
DOMAIN=$2
SSH_KEY=$3

log_section "Phase 6: Microservice Deployment"

log_warning "Microservice deployment requires GitHub integration in Coolify UI"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Manual Steps Required:${NC}"
echo ""
echo "  1. Open Coolify UI: http://${SERVER_IP}:${COOLIFY_PORT}"
echo "  2. Go to Sources → Add GitHub App"
echo "  3. Authorize Coolify to access ${GITHUB_REPO}"
echo "  4. For each service in the list below:"
echo "     a. Click '+ New' → Application → GitHub"
echo "     b. Select repository and branch (${GITHUB_BRANCH})"
echo "     c. Configure as shown below"
echo "     d. Add environment variables"
echo "     e. Click Deploy"
echo ""
echo -e "${GREEN}Services to deploy:${NC}"
echo ""

if [ -n "$DOMAIN" ]; then
    for service in "${SERVICES_TO_DEPLOY[@]}"; do
        echo "  • ${service}-service"
        echo "    Base Directory: services/${service}"
        echo "    Port: 8000"
        echo "    Domain: ${service}.${API_SUBDOMAIN}.${DOMAIN}"
        echo ""
    done
else
    for service in "${SERVICES_TO_DEPLOY[@]}"; do
        echo "  • ${service}-service"
        echo "    Base Directory: services/${service}"
        echo "    Port: 8000"
        echo "    Access: Will be assigned port by Coolify"
        echo ""
    done
fi

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

log_info "Environment variables templates are available in: config/service-env-template.txt"

read -p "Press Enter when all services are deployed..."

log_success "Phase 6 completed: Microservices deployment initiated"
