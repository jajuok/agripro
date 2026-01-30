#!/bin/bash

# Phase 8: Run Database Migrations
# Executes Alembic migrations for each service

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"

SERVER_IP=$1
DOMAIN=$2
SSH_KEY=$3

log_section "Phase 8: Database Migrations"

log_info "Database migrations will be run automatically on first deployment"
log_info "Or manually via: docker exec <service-container> alembic upgrade head"

log_success "Phase 8 completed: Migration instructions provided"
