#!/bin/bash

# AgriScheme Pro - Automated Coolify Deployment
# Main orchestration script

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common utilities
source "${SCRIPT_DIR}/utils/common.sh"

# =============================================================================
# CONFIGURATION
# =============================================================================

# Load configuration
if [ -f "${SCRIPT_DIR}/config/deployment.env" ]; then
    source "${SCRIPT_DIR}/config/deployment.env"
else
    log_error "Configuration file not found: ${SCRIPT_DIR}/config/deployment.env"
    exit 1
fi

# Command line arguments
SERVER_IP="${1:-}"
DOMAIN="${2:-}"
SSH_KEY="${3:-$HOME/.ssh/id_rsa}"

# =============================================================================
# VALIDATION
# =============================================================================

validate_inputs() {
    log_section "Validating Inputs"

    if [ -z "$SERVER_IP" ]; then
        log_error "Server IP is required"
        echo "Usage: $0 <SERVER_IP> [DOMAIN] [SSH_KEY_PATH]"
        exit 1
    fi

    if ! validate_ip "$SERVER_IP"; then
        log_error "Invalid IP address: $SERVER_IP"
        exit 1
    fi

    if [ -n "$DOMAIN" ] && ! validate_domain "$DOMAIN"; then
        log_error "Invalid domain: $DOMAIN"
        exit 1
    fi

    if [ ! -f "$SSH_KEY" ]; then
        log_error "SSH key not found: $SSH_KEY"
        exit 1
    fi

    # Set deployment mode
    if [ -z "$DOMAIN" ]; then
        export DEPLOYMENT_MODE="ip-only"
        log_info "Deployment mode: IP-only (no domain)"
    else
        export DEPLOYMENT_MODE="domain"
        log_info "Deployment mode: Domain-based"
    fi

    log_success "All inputs validated"
}

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

preflight_checks() {
    log_section "Pre-flight Checks"

    # Check required commands
    log_step "Checking required commands"
    local required_commands=("ssh" "scp" "openssl" "jq")

    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            log_error "Required command not found: $cmd"
            exit 1
        fi
        log_info "✓ $cmd"
    done

    # Test SSH connection
    if ! check_ssh_connection "$SERVER_IP" "$SSH_KEY"; then
        log_error "Cannot connect to server via SSH"
        exit 1
    fi

    log_success "Pre-flight checks passed"
}

# =============================================================================
# GENERATE SECRETS
# =============================================================================

generate_secrets() {
    log_section "Generating Secrets"

    mkdir -p "${SCRIPT_DIR}/.secrets"
    SECRETS_FILE="${SCRIPT_DIR}/.secrets/deployment.secrets"

    # Clear existing secrets
    > "$SECRETS_FILE"

    # Generate passwords if not set
    if [ -z "$POSTGRES_PASSWORD" ]; then
        POSTGRES_PASSWORD=$(generate_password)
        log_info "Generated PostgreSQL password"
    fi

    if [ -z "$REDIS_PASSWORD" ]; then
        REDIS_PASSWORD=$(generate_password)
        log_info "Generated Redis password"
    fi

    if [ -z "$JWT_SECRET_KEY" ]; then
        JWT_SECRET_KEY=$(generate_password)
        log_info "Generated JWT secret key"
    fi

    if [ -z "$GRAFANA_PASSWORD" ]; then
        GRAFANA_PASSWORD=$(generate_password)
        log_info "Generated Grafana password"
    fi

    # Save secrets
    save_secret "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD" "$SECRETS_FILE"
    save_secret "REDIS_PASSWORD" "$REDIS_PASSWORD" "$SECRETS_FILE"
    save_secret "JWT_SECRET_KEY" "$JWT_SECRET_KEY" "$SECRETS_FILE"
    save_secret "GRAFANA_PASSWORD" "$GRAFANA_PASSWORD" "$SECRETS_FILE"

    # Export for use in subscripts
    export POSTGRES_PASSWORD REDIS_PASSWORD JWT_SECRET_KEY GRAFANA_PASSWORD

    log_success "Secrets generated and saved to $SECRETS_FILE"
}

# =============================================================================
# DEPLOYMENT PHASES
# =============================================================================

run_phase() {
    local phase_number=$1
    local phase_script=$2
    local phase_name=$3

    log_section "Phase ${phase_number}: ${phase_name}"

    local script_path="${SCRIPT_DIR}/${phase_script}"

    if [ ! -f "$script_path" ]; then
        log_error "Phase script not found: $script_path"
        return 1
    fi

    chmod +x "$script_path"

    if bash "$script_path" "$SERVER_IP" "$DOMAIN" "$SSH_KEY"; then
        log_success "Phase ${phase_number} completed: ${phase_name}"
        return 0
    else
        log_error "Phase ${phase_number} failed: ${phase_name}"
        return 1
    fi
}

# =============================================================================
# MAIN DEPLOYMENT
# =============================================================================

main() {
    clear

    echo -e "${CYAN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║           AgriScheme Pro - Automated Coolify Deployment              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    log_info "Server IP: $SERVER_IP"
    if [ -n "$DOMAIN" ]; then
        log_info "Domain: $DOMAIN"
    else
        log_info "Domain: Not configured (IP-only deployment)"
    fi
    log_info "SSH Key: $SSH_KEY"
    echo ""

    if ! confirm_action "This will deploy AgriScheme Pro to the specified server. Continue?"; then
        exit 0
    fi

    # Start deployment
    local start_time=$(date +%s)

    # Validation
    validate_inputs

    # Pre-flight checks
    preflight_checks

    # Generate secrets
    generate_secrets

    # Phase 1: Server Setup
    run_phase 1 "01-server-setup.sh" "Server Setup" || exit 1

    # Phase 2: Install Coolify
    run_phase 2 "02-install-coolify.sh" "Coolify Installation" || exit 1

    # Phase 3: DNS Configuration (skip if IP-only mode)
    if [ "$DEPLOYMENT_MODE" = "domain" ]; then
        run_phase 3 "03-configure-dns.sh" "DNS Configuration Helper" || exit 1
    else
        log_info "Skipping Phase 3: DNS Configuration (IP-only deployment)"
    fi

    # Phase 4: Deploy Databases
    run_phase 4 "04-deploy-databases.sh" "Database Deployment" || exit 1

    # Phase 5: Deploy Infrastructure
    run_phase 5 "05-deploy-infrastructure.sh" "Infrastructure Services" || exit 1

    # Phase 6: Deploy Microservices
    run_phase 6 "06-deploy-services.sh" "Microservice Deployment" || exit 1

    # Phase 7: Configure Monitoring
    if [ "$ENABLE_MONITORING" = "true" ]; then
        run_phase 7 "07-configure-monitoring.sh" "Monitoring Setup" || exit 1
    fi

    # Phase 8: Run Migrations
    run_phase 8 "08-run-migrations.sh" "Database Migrations" || exit 1

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    # Deployment summary
    echo ""
    print_summary "$SERVER_IP" "$DOMAIN"

    echo ""
    log_success "Total deployment time: ${minutes}m ${seconds}s"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Next Steps:${NC}"
    if [ "$DEPLOYMENT_MODE" = "domain" ]; then
        echo "  1. Configure DNS A records (see instructions above)"
        echo "  2. Access Coolify UI: http://${SERVER_IP}:8000"
        echo "  3. Complete Coolify initial setup wizard"
        echo "  4. Connect GitHub repository in Coolify"
        echo "  5. Update mobile app API endpoints"
    else
        echo "  1. Access Coolify UI: http://${SERVER_IP}:8000"
        echo "  2. Complete Coolify initial setup wizard"
        echo "  3. Connect GitHub repository in Coolify"
        echo "  4. Services will be accessible via IP:PORT"
        echo "  5. Consider configuring a domain later for SSL/HTTPS"
    fi
    echo ""
    echo -e "${CYAN}Credentials:${NC}"
    echo "  PostgreSQL: agrischeme_admin / (see .secrets/deployment.secrets)"
    echo "  Grafana: admin / (see .secrets/deployment.secrets)"
    echo ""
    echo -e "${CYAN}Documentation:${NC}"
    echo "  Deployment Plan: docs/deployment/coolify-deployment-plan.md"
    echo "  Secrets: .secrets/deployment.secrets"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Run main function
main "$@"
