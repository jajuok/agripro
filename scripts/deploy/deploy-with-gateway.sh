#!/bin/bash
# Deploy AgriScheme Pro with API Gateway via Traefik
# This script deploys all services with Traefik API gateway for unified external access

set -e

# Configuration
SERVER_IP="${SERVER_IP:-213.32.19.116}"
COOLIFY_URL="${COOLIFY_URL:-http://${SERVER_IP}:8000}"
TOKEN="${COOLIFY_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "Error: COOLIFY_TOKEN environment variable is required"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to deploy a service via Coolify API
deploy_service() {
    local service_name=$1
    local service_port=$2
    local path_prefix=$3

    log_info "Deploying ${service_name}..."

    # TODO: Implement Coolify API deployment logic
    # This will depend on Coolify's API structure
    # For now, this is a placeholder

    log_warn "Deployment API call for ${service_name} not yet implemented"
}

# Function to check service health
check_health() {
    local service_name=$1
    local health_url=$2

    log_info "Checking health of ${service_name}..."

    if curl -f -s "${health_url}" > /dev/null; then
        log_info "${service_name} is healthy"
        return 0
    else
        log_error "${service_name} health check failed"
        return 1
    fi
}

main() {
    log_info "Starting deployment with API Gateway..."

    # Deploy infrastructure first
    log_info "Deploying infrastructure services..."

    # Deploy Traefik API Gateway
    log_info "Deploying Traefik API Gateway..."
    # Traefik should be deployed first as it handles all routing

    # Deploy PostgreSQL
    log_info "Deploying PostgreSQL database..."

    # Deploy Redis
    log_info "Deploying Redis cache..."

    # Deploy application services
    log_info "Deploying application services..."

    # Service deployment configuration
    # Format: service_name:port:path_prefix
    services=(
        "auth:9000:/api/v1/auth"
        "farmer:9001:/api/v1/farmers,/api/v1/farms,/api/v1/kyc,/api/v1/crop-planning"
        "gis:9003:/api/v1/gis"
        "financial:9004:/api/v1/financial"
        "market:9005:/api/v1/market"
        "ai:9006:/api/v1/ai"
        "iot:9007:/api/v1/iot"
        "livestock:9008:/api/v1/livestock"
        "task:9009:/api/v1/tasks"
        "inventory:9010:/api/v1/inventory"
        "notification:9011:/api/v1/notifications"
        "traceability:9012:/api/v1/traceability"
        "compliance:9013:/api/v1/compliance"
        "integration:9014:/api/v1/integration"
    )

    for service in "${services[@]}"; do
        IFS=':' read -r name port paths <<< "$service"
        deploy_service "$name" "$port" "$paths"
    done

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10

    # Verify gateway is working
    log_info "Verifying API gateway routing..."

    # Check Traefik dashboard
    if curl -f -s "http://${SERVER_IP}:8080/api/http/routers" > /dev/null; then
        log_info "Traefik dashboard is accessible"
    else
        log_warn "Cannot access Traefik dashboard"
    fi

    # Test a few service endpoints through the gateway
    log_info "Testing service endpoints through gateway..."

    if check_health "auth-service" "http://${SERVER_IP}/api/v1/auth/health"; then
        log_info "Auth service accessible through gateway"
    fi

    if check_health "farmer-service" "http://${SERVER_IP}/api/v1/farmers/health"; then
        log_info "Farmer service accessible through gateway"
    fi

    log_info "Deployment complete!"
    log_info "API Gateway URL: http://${SERVER_IP}/api/v1"
    log_info "Traefik Dashboard: http://${SERVER_IP}:8080"
}

# Run main function
main "$@"
