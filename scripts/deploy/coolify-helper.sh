#!/bin/bash

# Coolify UI Deployment Helper
# Generates all configuration and guides you through UI deployment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"
load_secrets "${SCRIPT_DIR}/.secrets/deployment.secrets"

# =============================================================================
# CONFIGURATION
# =============================================================================

SERVER_IP="${1}"

if [ -z "$SERVER_IP" ]; then
    log_error "Server IP required"
    echo "Usage: $0 <SERVER_IP>"
    exit 1
fi

COOLIFY_URL="http://${SERVER_IP}:8000"

# Services to deploy
SERVICES=(
    "auth:agrischeme_auth:Authentication and authorization service"
    "farmer:agrischeme_farmer:Farmer profile management service"
    "farm:agrischeme_farm:Farm operations management service"
    "financial:agrischeme_financial:Financial transactions service"
    "gis:agrischeme_gis:Geographic information system service"
    "market:agrischeme_market:Market and pricing service"
    "ai:agrischeme_ai:AI and recommendations service"
    "iot:agrischeme_iot:IoT device management service"
    "livestock:agrischeme_livestock:Livestock management service"
    "task:agrischeme_task:Task and workflow service"
    "inventory:agrischeme_inventory:Inventory management service"
    "notification:agrischeme_notification:Notifications service"
    "traceability:agrischeme_traceability:Product traceability service"
    "compliance:agrischeme_compliance:Compliance and regulations service"
    "integration:agrischeme_integration:Third-party integrations service"
)

# =============================================================================
# WELCOME
# =============================================================================

clear

cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║           AgriScheme Pro - Coolify Deployment Helper                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

This helper will guide you through deploying all 15 services in Coolify UI.

For each service, I'll:
  • Show you exactly what to enter
  • Generate environment variables
  • Provide copy-paste values
  • Track your progress

Ready to start? Press Enter...
EOF

read -r

# =============================================================================
# INITIAL SETUP
# =============================================================================

log_section "Initial Setup"

echo ""
echo -e "${CYAN}1. Open Coolify in your browser:${NC}"
echo "   ${COOLIFY_URL}"
echo ""
echo -e "${CYAN}2. Make sure you've connected GitHub:${NC}"
echo "   Sources → + Add → GitHub App → Authorize"
echo "   Repository: jajuok/agripro"
echo ""
echo -e "${CYAN}3. Create project (if not exists):${NC}"
echo "   Projects → + New Project"
echo "   Name: agrischeme-infra"
echo "   Environment: production"
echo ""

read -p "Press Enter when ready to start deploying services..."

# =============================================================================
# DEPLOY EACH SERVICE
# =============================================================================

deployed_count=0

for service_config in "${SERVICES[@]}"; do
    IFS=':' read -r service_name db_name description <<< "$service_config"

    clear

    # Progress indicator
    deployed_count=$((deployed_count))
    total=${#SERVICES[@]}

    log_section "Service $((deployed_count + 1))/${total}: ${service_name}-service"

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}Description:${NC} ${description}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Generate database URL
    db_container="agrischeme-${service_name}-db"
    database_url="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${db_container}:5432/${db_name}"

    # Instructions
    echo -e "${YELLOW}▶ STEP 1: Create Application${NC}"
    echo "  1. In Coolify, go to: Projects → agrischeme-infra → production"
    echo "  2. Click: + New Resource → Application"
    echo "  3. Select your GitHub source"
    echo ""
    read -p "Press Enter when done..."

    echo ""
    echo -e "${YELLOW}▶ STEP 2: Repository Configuration${NC}"
    echo ""
    echo -e "${GREEN}Copy these values:${NC}"
    echo ""
    echo "  Repository:        jajuok/agripro"
    echo "  Branch:            main"
    echo "  Build Pack:        Dockerfile"
    echo "  Base Directory:    services/${service_name}"
    echo "  Dockerfile:        Dockerfile"
    echo ""
    read -p "Press Enter when done..."

    echo ""
    echo -e "${YELLOW}▶ STEP 3: Application Settings${NC}"
    echo ""
    echo -e "${GREEN}Copy these values:${NC}"
    echo ""
    echo "  Name:              ${service_name}-service"
    echo "  Description:       ${description}"
    echo "  Port:              8000"
    echo "  Domain:            (leave empty for IP-only)"
    echo ""
    read -p "Press Enter when done..."

    echo ""
    echo -e "${YELLOW}▶ STEP 4: Environment Variables${NC}"
    echo ""
    echo -e "${GREEN}Click 'Environment Variables' tab and add these:${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Common environment variables
    cat << ENV_COMMON

  DATABASE_URL
  ${database_url}

  REDIS_URL
  redis://:${REDIS_PASSWORD}@agrischeme-redis:6379/0

  KAFKA_BOOTSTRAP_SERVERS
  agrischeme-kafka:9092

  ENVIRONMENT
  production

  LOG_LEVEL
  INFO

  DEBUG
  false

  CORS_ORIGINS
  ["*"]
ENV_COMMON

    # Add JWT variables for auth service
    if [ "$service_name" = "auth" ]; then
        cat << ENV_AUTH

  JWT_SECRET_KEY
  ${JWT_SECRET_KEY}

  JWT_ALGORITHM
  HS256

  ACCESS_TOKEN_EXPIRE_MINUTES
  30

  REFRESH_TOKEN_EXPIRE_DAYS
  7
ENV_AUTH
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${YELLOW}💡 Tip: Copy entire blocks with triple-click${NC}"
    echo ""
    read -p "Press Enter when all variables are added..."

    echo ""
    echo -e "${YELLOW}▶ STEP 5: Deploy${NC}"
    echo "  1. Click 'Save'"
    echo "  2. Click 'Deploy'"
    echo "  3. Wait for build to complete (2-5 minutes)"
    echo "  4. Check status shows 'Running' and 'Healthy'"
    echo ""
    read -p "Press Enter when deployed and healthy..."

    deployed_count=$((deployed_count + 1))

    # Save progress
    echo "${service_name}" >> "${SCRIPT_DIR}/.secrets/deployed_services.txt"

    # Quick verification
    echo ""
    echo -e "${GREEN}✓ ${service_name}-service deployed (${deployed_count}/${total})${NC}"
    echo ""

    if [ $deployed_count -lt $total ]; then
        echo -e "${CYAN}Ready for next service?${NC}"
        read -p "Press Enter to continue..."
    fi
done

# =============================================================================
# COMPLETION
# =============================================================================

clear

log_section "🎉 All Services Deployed!"

echo ""
echo -e "${GREEN}Congratulations! All 15 services are deployed.${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Deployment Summary${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

for service_config in "${SERVICES[@]}"; do
    IFS=':' read -r service_name db_name description <<< "$service_config"
    echo "  ✓ ${service_name}-service"
done

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Service URLs
echo -e "${YELLOW}Access Your Services:${NC}"
echo ""
echo "  Coolify UI:  ${COOLIFY_URL}"
echo ""
echo "  Check service ports in Coolify UI under each service"
echo "  Health check: http://${SERVER_IP}:<port>/health"
echo ""

# Next steps
echo -e "${CYAN}Next Steps:${NC}"
echo ""
echo "  1. Run database migrations:"
echo "     ./scripts/deploy/run-migrations.sh ${SERVER_IP}"
echo ""
echo "  2. Test all service endpoints"
echo ""
echo "  3. Update mobile app configuration:"
echo "     apps/mobile/src/services/api.ts"
echo ""
echo "  4. Test end-to-end workflows"
echo ""

# Cleanup progress file
rm -f "${SCRIPT_DIR}/.secrets/deployed_services.txt"

log_success "Deployment completed!"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
