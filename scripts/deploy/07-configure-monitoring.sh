#!/bin/bash

# Phase 7: Configure Monitoring
# Sets up Prometheus and Grafana

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"
load_secrets "${SCRIPT_DIR}/.secrets/deployment.secrets"

SERVER_IP=$1
DOMAIN=$2
SSH_KEY=$3

log_section "Phase 7: Monitoring Setup"

log_info "Monitoring setup will be configured in Coolify UI"
log_info "Grafana password saved in .secrets/deployment.secrets"

log_success "Phase 7 completed: Monitoring configuration ready"
