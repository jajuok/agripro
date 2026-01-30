#!/bin/bash

# Phase 1: Server Setup
# Configures Ubuntu server with security hardening and required packages

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"

SERVER_IP=$1
DOMAIN=$2
SSH_KEY=$3

log_section "Phase 1: Server Setup"

# =============================================================================
# SYSTEM UPDATES
# =============================================================================

log_step "Updating system packages"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    set -e
    export DEBIAN_FRONTEND=noninteractive

    apt-get update -qq
    apt-get upgrade -y -qq
    apt-get install -y -qq \
        curl \
        wget \
        git \
        jq \
        ca-certificates \
        gnupg \
        lsb-release \
        software-properties-common \
        apt-transport-https \
        fail2ban \
        ufw \
        unattended-upgrades
"

log_success "System packages updated"

# =============================================================================
# FIREWALL CONFIGURATION
# =============================================================================

if [ "$UFW_ENABLED" = "true" ]; then
    log_step "Configuring firewall (UFW)"

    remote_exec "$SERVER_IP" "$SSH_KEY" "
        set -e

        # Reset UFW to default
        ufw --force reset

        # Default policies
        ufw default deny incoming
        ufw default allow outgoing

        # Allow SSH
        ufw allow ${SSH_PORT}/tcp

        # Allow HTTP and HTTPS
        ufw allow 80/tcp
        ufw allow 443/tcp

        # Allow Coolify
        ufw allow ${COOLIFY_PORT}/tcp

        # Enable UFW
        ufw --force enable

        # Show status
        ufw status verbose
    "

    log_success "Firewall configured"
fi

# =============================================================================
# FAIL2BAN CONFIGURATION
# =============================================================================

if [ "$FAIL2BAN_ENABLED" = "true" ]; then
    log_step "Configuring Fail2ban"

    remote_exec "$SERVER_IP" "$SSH_KEY" "
        set -e

        # Configure Fail2ban for SSH
        cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ${SSH_PORT}
logpath = %(sshd_log)s
backend = %(sshd_backend)s
EOF

        # Start Fail2ban
        systemctl enable fail2ban
        systemctl restart fail2ban
    "

    log_success "Fail2ban configured"
fi

# =============================================================================
# DOCKER INSTALLATION
# =============================================================================

log_step "Installing Docker"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    set -e

    # Remove old Docker versions
    apt-get remove -y docker docker-engine docker.io containerd runc || true

    # Add Docker GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Add Docker repository
    echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Start Docker
    systemctl enable docker
    systemctl start docker

    # Verify installation
    docker --version
    docker compose version
"

log_success "Docker installed"

# =============================================================================
# SYSTEM OPTIMIZATION
# =============================================================================

log_step "Optimizing system settings"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    set -e

    # Increase file descriptors
    cat >> /etc/security/limits.conf << 'EOF'
* soft nofile 65536
* hard nofile 65536
EOF

    # Optimize sysctl settings
    cat >> /etc/sysctl.conf << 'EOF'
# Network optimization
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.ip_local_port_range = 1024 65535

# Memory optimization
vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 2
EOF

    # Apply sysctl changes
    sysctl -p
"

log_success "System optimized"

# =============================================================================
# TIMEZONE CONFIGURATION
# =============================================================================

log_step "Setting timezone to ${SERVER_TIMEZONE}"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    timedatectl set-timezone ${SERVER_TIMEZONE}
"

log_success "Timezone configured"

# =============================================================================
# UNATTENDED UPGRADES
# =============================================================================

if [ "$UNATTENDED_UPGRADES" = "true" ]; then
    log_step "Configuring automatic security updates"

    remote_exec "$SERVER_IP" "$SSH_KEY" "
        set -e

        # Configure unattended upgrades
        cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    \"\${distro_id}:\${distro_codename}-security\";
    \"\${distro_id}ESMApps:\${distro_codename}-apps-security\";
    \"\${distro_id}ESM:\${distro_codename}-infra-security\";
};

Unattended-Upgrade::AutoFixInterruptedDpkg \"true\";
Unattended-Upgrade::MinimalSteps \"true\";
Unattended-Upgrade::Remove-Unused-Kernel-Packages \"true\";
Unattended-Upgrade::Remove-Unused-Dependencies \"true\";
Unattended-Upgrade::Automatic-Reboot \"false\";
EOF

        # Enable automatic updates
        cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists \"1\";
APT::Periodic::Download-Upgradeable-Packages \"1\";
APT::Periodic::AutocleanInterval \"7\";
APT::Periodic::Unattended-Upgrade \"1\";
EOF
    "

    log_success "Automatic security updates configured"
fi

# =============================================================================
# CREATE DIRECTORIES
# =============================================================================

log_step "Creating deployment directories"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    mkdir -p /opt/agrischeme
    mkdir -p /opt/agrischeme/config
    mkdir -p /opt/agrischeme/backups
    mkdir -p /opt/agrischeme/logs
"

log_success "Directories created"

# =============================================================================
# FINAL CHECKS
# =============================================================================

log_step "Verifying server setup"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    set -e

    # Check Docker
    docker ps > /dev/null

    # Check UFW
    if [ '$UFW_ENABLED' = 'true' ]; then
        ufw status | grep -q 'Status: active'
    fi

    echo 'All checks passed'
"

log_success "Server setup verified"

log_success "Phase 1 completed: Server is ready for Coolify installation"
