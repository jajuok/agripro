#!/bin/bash

# Phase 2: Install Coolify
# Installs and configures Coolify on the server

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"

SERVER_IP=$1
DOMAIN=$2
SSH_KEY=$3

log_section "Phase 2: Coolify Installation"

# =============================================================================
# INSTALL COOLIFY
# =============================================================================

log_step "Installing Coolify"

remote_exec_sudo "$SERVER_IP" "$SSH_KEY" "
    set -e

    # Download and run Coolify installer
    curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash

    # Wait for Coolify to start
    echo 'Waiting for Coolify to initialize...'
    sleep 30

    # Check if Coolify is running
    docker ps | grep coolify
"

log_success "Coolify installed"

# =============================================================================
# WAIT FOR COOLIFY TO BE READY
# =============================================================================

log_step "Waiting for Coolify to be ready"

max_attempts=20
attempt=0

while [ $attempt -lt $max_attempts ]; do
    # Add retry logic for SSH connection issues
    if remote_exec "$SERVER_IP" "$SSH_KEY" "curl -s http://localhost:${COOLIFY_PORT}/api/health 2>/dev/null | grep -q 'ok' || curl -s http://localhost:${COOLIFY_PORT} 2>/dev/null | grep -q 'Coolify'" 2>/dev/null; then
        log_success "Coolify is ready"
        break
    fi

    attempt=$((attempt + 1))
    echo -n "."

    # Longer sleep to avoid overwhelming SSH
    sleep 15

    if [ $attempt -eq $max_attempts ]; then
        log_error "Coolify failed to start within expected time"
        log_info "You can check Coolify status manually at: http://${SERVER_IP}:8000"
        exit 1
    fi
done

# =============================================================================
# VERIFY COOLIFY CONTAINERS
# =============================================================================

log_step "Verifying Coolify containers"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    echo 'Coolify containers:'
    docker ps --filter 'name=coolify' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
"

log_success "Coolify containers verified"

# =============================================================================
# DISPLAY ACCESS INFORMATION
# =============================================================================

log_success "Phase 2 completed: Coolify is installed and running"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Coolify Access Information:${NC}"
echo ""
echo "  URL: http://${SERVER_IP}:${COOLIFY_PORT}"
echo ""
echo -e "${YELLOW}Manual Steps Required:${NC}"
echo "  1. Open the URL above in your browser"
echo "  2. Complete the initial setup wizard"
echo "  3. Create an admin account"
echo "  4. Generate an API token (Settings → API Tokens)"
echo "  5. Save the API token for later use"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

read -p "Press Enter when you have completed the Coolify setup wizard..."

# =============================================================================
# REQUEST API TOKEN
# =============================================================================

echo ""
log_info "Please enter the API token you generated in Coolify:"
read -sp "API Token: " COOLIFY_API_TOKEN
echo ""

if [ -z "$COOLIFY_API_TOKEN" ]; then
    log_error "API token is required to continue"
    exit 1
fi

# Save API token
SECRETS_FILE="${SCRIPT_DIR}/.secrets/deployment.secrets"
save_secret "COOLIFY_API_TOKEN" "$COOLIFY_API_TOKEN" "$SECRETS_FILE"

log_success "API token saved"

# =============================================================================
# CREATE COOLIFY PROJECT
# =============================================================================

log_step "Creating Coolify project"

# Create project via API
project_response=$(remote_exec "$SERVER_IP" "$SSH_KEY" "
    curl -s -X POST \
        -H 'Authorization: Bearer ${COOLIFY_API_TOKEN}' \
        -H 'Content-Type: application/json' \
        http://localhost/api/v1/projects \
        -d '{
            \"name\": \"agrischeme-infra\",
            \"description\": \"AgriScheme Pro Infrastructure\"
        }'
")

log_info "Project response: $project_response"

log_success "Coolify project created"

log_success "Phase 2 completed successfully"
