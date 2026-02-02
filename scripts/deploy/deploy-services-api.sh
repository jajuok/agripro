#!/bin/bash

# Automated Service Deployment via Coolify API
# Deploys all 15 AgriScheme Pro microservices

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
PROJECT_UUID="${3:-}"

COOLIFY_URL="http://${SERVER_IP}"
GITHUB_REPO="jajuok/agripro"
GITHUB_BRANCH="main"

# Services configuration: name:base_directory:database_name
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

log_section "Automated Service Deployment"

if [ -z "$SERVER_IP" ] || [ -z "$COOLIFY_API_TOKEN" ]; then
    log_error "Missing required parameters"
    echo ""
    echo "Usage: $0 <SERVER_IP> <COOLIFY_API_TOKEN> [PROJECT_UUID]"
    echo ""
    echo "Get your API token from Coolify UI:"
    echo "  Settings → API Tokens → Create New Token"
    echo ""
    echo "Get your Project UUID from Coolify UI:"
    echo "  Projects → agrischeme-infra → Check URL for UUID"
    echo "  Or leave empty to create a new project"
    exit 1
fi

log_info "Server: $SERVER_IP"
log_info "API Token: ${COOLIFY_API_TOKEN:0:20}..."
echo ""

# =============================================================================
# CREATE PROJECT (if needed)
# =============================================================================

if [ -z "$PROJECT_UUID" ]; then
    log_step "Creating Coolify project"

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X POST \
        "${COOLIFY_URL}/api/v1/projects" \
        -H "Authorization: Bearer ${COOLIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "agrischeme-infra",
            "description": "AgriScheme Pro Infrastructure"
        }')

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        PROJECT_UUID=$(echo "$body" | jq -r '.uuid // .id // .data.uuid // .data.id' 2>/dev/null || echo "")

        if [ -n "$PROJECT_UUID" ] && [ "$PROJECT_UUID" != "null" ]; then
            log_success "Project created: $PROJECT_UUID"
            save_secret "PROJECT_UUID" "$PROJECT_UUID" "${SCRIPT_DIR}/.secrets/deployment.secrets"
        else
            log_warning "Project created but couldn't extract UUID"
            log_info "Please get the project UUID from Coolify UI and run again"
            log_info "Or check existing projects: curl -H 'Authorization: Bearer TOKEN' ${COOLIFY_URL}/api/v1/projects"
            exit 1
        fi
    else
        log_warning "API returned HTTP $http_code"
        log_info "Response: $body"
        log_info ""
        log_info "The Coolify API might not be available or the endpoint might be different."
        log_info "Please use the manual deployment guide instead:"
        log_info "  docs/deployment/coolify-ui-service-deployment-guide.md"
        exit 1
    fi
else
    log_info "Using existing project: $PROJECT_UUID"
fi

# =============================================================================
# DEPLOY SERVICES
# =============================================================================

log_section "Deploying Services"

deploy_service() {
    local service_name=$1
    local base_dir=$2
    local db_name=$3

    log_step "Deploying ${service_name}-service"

    # Get database URL
    local db_container="agrischeme-${service_name}-db"
    local database_url="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${db_container}:5432/${db_name}"

    # Build environment variables JSON
    local env_vars=$(cat <<EOF
{
    "DATABASE_URL": "${database_url}",
    "REDIS_URL": "redis://:${REDIS_PASSWORD}@agrischeme-redis:6379/0",
    "KAFKA_BOOTSTRAP_SERVERS": "agrischeme-kafka:9092",
    "ENVIRONMENT": "production",
    "LOG_LEVEL": "INFO",
    "DEBUG": "false",
    "CORS_ORIGINS": "[\"*\"]"
}
EOF
)

    # Add JWT secret for auth service
    if [ "$service_name" = "auth" ]; then
        env_vars=$(echo "$env_vars" | jq ". + {
            \"JWT_SECRET_KEY\": \"${JWT_SECRET_KEY}\",
            \"JWT_ALGORITHM\": \"HS256\",
            \"ACCESS_TOKEN_EXPIRE_MINUTES\": \"30\",
            \"REFRESH_TOKEN_EXPIRE_DAYS\": \"7\"
        }")
    fi

    # Create application payload
    local payload=$(cat <<EOF
{
    "project_uuid": "${PROJECT_UUID}",
    "server_uuid": "0",
    "environment_name": "production",
    "git_repository": "https://github.com/${GITHUB_REPO}",
    "git_branch": "${GITHUB_BRANCH}",
    "git_commit_sha": "HEAD",
    "git_full_url": "https://github.com/${GITHUB_REPO}",
    "build_pack": "dockerfile",
    "base_directory": "${base_dir}",
    "dockerfile_location": "Dockerfile",
    "name": "${service_name}-service",
    "description": "AgriScheme ${service_name} service",
    "domains": "",
    "ports_exposes": "8000",
    "ports_mappings": "",
    "environment_variables": ${env_vars},
    "is_static": false,
    "install_command": "",
    "build_command": "",
    "start_command": "",
    "instant_deploy": true
}
EOF
)

    # Deploy via API
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X POST \
        "${COOLIFY_URL}/api/v1/applications" \
        -H "Authorization: Bearer ${COOLIFY_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$payload")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        log_success "${service_name}-service deployed"
        return 0
    else
        log_error "${service_name}-service failed (HTTP $http_code)"
        log_info "Response: ${body:0:200}"
        return 1
    fi
}

# Deploy all services
success_count=0
failed_count=0
failed_services=()

for service_config in "${SERVICES[@]}"; do
    IFS=':' read -r service_name base_dir db_name <<< "$service_config"

    if deploy_service "$service_name" "$base_dir" "$db_name"; then
        ((success_count++))
    else
        ((failed_count++))
        failed_services+=("$service_name")
    fi

    echo ""
    sleep 2  # Rate limiting
done

# =============================================================================
# SUMMARY
# =============================================================================

log_section "Deployment Summary"

echo -e "${GREEN}Successful: ${success_count}/${#SERVICES[@]}${NC}"
echo -e "${RED}Failed: ${failed_count}/${#SERVICES[@]}${NC}"

if [ ${#failed_services[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Failed services:${NC}"
    for svc in "${failed_services[@]}"; do
        echo "  - $svc"
    done
    echo ""
    echo -e "${YELLOW}You can deploy these manually using the guide:${NC}"
    echo "  docs/deployment/coolify-ui-service-deployment-guide.md"
fi

echo ""
if [ $failed_count -eq 0 ]; then
    log_success "All services deployed successfully!"
else
    log_warning "Some services failed. Check Coolify UI for details."
fi

echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Check service status in Coolify UI: ${COOLIFY_URL}:8000"
echo "  2. Run database migrations for each service"
echo "  3. Test service endpoints: http://${SERVER_IP}:<port>/health"
echo "  4. Configure mobile app with service URLs"
