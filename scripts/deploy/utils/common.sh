#!/bin/bash

# Common utility functions for deployment scripts

# Colors
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export PURPLE='\033[0;35m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${PURPLE}▶ $1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

log_section() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  $1${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Progress indicator
show_progress() {
    local duration=$1
    local message=$2

    echo -n "$message"
    for ((i=0; i<duration; i++)); do
        echo -n "."
        sleep 1
    done
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Generate secure random password
generate_password() {
    openssl rand -base64 48 | tr -d "=+/" | cut -c1-64
}

# Check SSH connection
check_ssh_connection() {
    local server_ip=$1
    local ssh_key=$2
    local user=${3:-ubuntu}

    log_step "Testing SSH connection to ${server_ip} as ${user}"

    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -i "$ssh_key" "${user}@${server_ip}" "echo 'Connection successful'" >/dev/null 2>&1; then
        log_success "SSH connection successful"
        return 0
    else
        log_error "SSH connection failed"
        return 1
    fi
}

# Remote command execution
remote_exec() {
    local server_ip=$1
    local ssh_key=$2
    local command=$3
    local user=${4:-ubuntu}

    ssh -o StrictHostKeyChecking=no -i "$ssh_key" "${user}@${server_ip}" "$command"
}

# Remote command execution with sudo
remote_exec_sudo() {
    local server_ip=$1
    local ssh_key=$2
    local command=$3
    local user=${4:-ubuntu}

    # Execute command with sudo, passing the full command as a single string
    ssh -o StrictHostKeyChecking=no -i "$ssh_key" "${user}@${server_ip}" "sudo bash -c \"$command\""
}

# Copy file to remote server
remote_copy() {
    local server_ip=$1
    local ssh_key=$2
    local local_file=$3
    local remote_path=$4
    local user=${5:-ubuntu}

    scp -o StrictHostKeyChecking=no -i "$ssh_key" "$local_file" "${user}@${server_ip}:${remote_path}"
}

# Wait for service to be healthy
wait_for_service() {
    local server_ip=$1
    local ssh_key=$2
    local container_name=$3
    local max_attempts=${4:-30}
    local interval=${5:-10}

    log_info "Waiting for ${container_name} to be healthy..."

    for ((i=1; i<=max_attempts; i++)); do
        status=$(remote_exec "$server_ip" "$ssh_key" "docker inspect --format='{{.State.Health.Status}}' $container_name 2>/dev/null || echo 'not_found'")

        if [ "$status" = "healthy" ]; then
            log_success "${container_name} is healthy"
            return 0
        fi

        echo -n "."
        sleep "$interval"
    done

    log_error "${container_name} failed to become healthy"
    return 1
}

# Create directory on remote server
remote_mkdir() {
    local server_ip=$1
    local ssh_key=$2
    local dir_path=$3

    remote_exec "$server_ip" "$ssh_key" "mkdir -p $dir_path"
}

# Check if container exists
container_exists() {
    local server_ip=$1
    local ssh_key=$2
    local container_name=$3

    result=$(remote_exec "$server_ip" "$ssh_key" "docker ps -a --format '{{.Names}}' | grep -q '^${container_name}$' && echo 'yes' || echo 'no'")

    [ "$result" = "yes" ]
}

# Save secret to file
save_secret() {
    local name=$1
    local value=$2
    local secrets_file=${3:-.secrets/deployment.secrets}

    mkdir -p "$(dirname "$secrets_file")"
    echo "${name}=${value}" >> "$secrets_file"
    chmod 600 "$secrets_file"
}

# Load secrets from file
load_secrets() {
    local secrets_file=${1:-.secrets/deployment.secrets}

    if [ -f "$secrets_file" ]; then
        set -a
        source "$secrets_file"
        set +a
    fi
}

# Validate IP address
validate_ip() {
    local ip=$1

    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Validate domain
validate_domain() {
    local domain=$1

    if [[ $domain =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Print deployment summary
print_summary() {
    local server_ip=$1
    local domain=$2

    log_section "Deployment Summary"

    echo "Server IP: ${server_ip}"
    echo "Domain: ${domain}"
    echo "Coolify URL: https://coolify.${domain}"
    echo "API URL: https://api.${domain}"
    echo ""
    echo "Secrets stored in: .secrets/deployment.secrets"
    echo ""
    log_success "Deployment completed successfully!"
}

# Handle errors
handle_error() {
    local exit_code=$1
    local error_message=$2

    log_error "$error_message"
    log_error "Exit code: $exit_code"
    log_info "Check logs for more details"

    exit "$exit_code"
}

# Confirm action
confirm_action() {
    local message=$1

    echo -e "${YELLOW}${message}${NC}"
    read -p "Continue? (yes/no): " -r
    echo

    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        return 0
    else
        log_warning "Action cancelled by user"
        return 1
    fi
}

# Export all functions
export -f log_info log_success log_warning log_error log_step log_section
export -f show_progress command_exists generate_password
export -f check_ssh_connection remote_exec remote_exec_sudo remote_copy remote_mkdir
export -f wait_for_service container_exists
export -f save_secret load_secrets
export -f validate_ip validate_domain
export -f print_summary handle_error confirm_action
