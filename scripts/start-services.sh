#!/usr/bin/env bash

# =============================================================================
# AgriScheme Pro - Backend Services Startup Script
# =============================================================================
# This script starts all backend microservices for local development.
#
# Services:
#   - PostgreSQL (port 5433)
#   - Redis (port 6379)
#   - Auth Service (port 9001)
#   - Farmer Service (port 9002)
#   - GIS Service (port 9003)
#
# Usage:
#   ./scripts/start-services.sh [options]
#
# Options:
#   --infra-only    Start only infrastructure (PostgreSQL, Redis)
#   --no-migrate    Skip database migrations
#   --service=NAME  Start only specific service (auth, farmer, gis)
#   --stop          Stop all services
#   --status        Show service status
#   --help          Show this help message
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Service configuration (compatible with bash 3.x)
SERVICE_NAMES="auth farmer gis"
AUTH_PORT=9001
FARMER_PORT=9002
GIS_PORT=9003

get_port() {
    local service=$1
    case $service in
        auth) echo $AUTH_PORT ;;
        farmer) echo $FARMER_PORT ;;
        gis) echo $GIS_PORT ;;
        *) echo "" ;;
    esac
}

# PID file directory
PID_DIR="$PROJECT_ROOT/.pids"
LOG_DIR="$PROJECT_ROOT/.logs"

# =============================================================================
# Helper Functions
# =============================================================================

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

ensure_dirs() {
    mkdir -p "$PID_DIR" "$LOG_DIR"
}

# =============================================================================
# Infrastructure Functions
# =============================================================================

start_infrastructure() {
    log_info "Starting infrastructure services..."

    cd "$PROJECT_ROOT"

    # Start only postgres and redis from docker-compose
    docker compose up -d postgres redis

    # Wait for services to be healthy
    log_info "Waiting for PostgreSQL to be ready..."
    local max_attempts=30
    local attempt=0
    while ! docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            log_error "PostgreSQL failed to start"
            exit 1
        fi
        sleep 1
    done
    log_success "PostgreSQL is ready"

    log_info "Waiting for Redis to be ready..."
    attempt=0
    while ! docker compose exec -T redis redis-cli ping > /dev/null 2>&1; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            log_error "Redis failed to start"
            exit 1
        fi
        sleep 1
    done
    log_success "Redis is ready"

    log_success "Infrastructure services started"
}

stop_infrastructure() {
    log_info "Stopping infrastructure services..."
    cd "$PROJECT_ROOT"
    docker compose down
    log_success "Infrastructure services stopped"
}

# =============================================================================
# Database Functions
# =============================================================================

run_migrations() {
    log_info "Running database migrations..."

    # Auth service migrations
    if [ -d "$PROJECT_ROOT/services/auth/.venv" ]; then
        log_info "Running auth service migrations..."
        cd "$PROJECT_ROOT/services/auth"
        .venv/bin/alembic upgrade head 2>/dev/null || log_warning "Auth migrations may have already been applied"
    fi

    # Farmer service migrations
    if [ -d "$PROJECT_ROOT/services/farmer/.venv" ]; then
        log_info "Running farmer service migrations..."
        cd "$PROJECT_ROOT/services/farmer"
        .venv/bin/alembic upgrade head 2>/dev/null || log_warning "Farmer migrations may have already been applied"
    fi

    log_success "Migrations completed"
}

# =============================================================================
# Service Functions
# =============================================================================

start_service() {
    local service=$1
    local port=$(get_port "$service")
    local service_dir="$PROJECT_ROOT/services/$service"
    local pid_file="$PID_DIR/${service}.pid"
    local log_file="$LOG_DIR/${service}.log"

    if [ -z "$port" ]; then
        log_error "Unknown service: $service"
        return 1
    fi

    if [ ! -d "$service_dir" ]; then
        log_warning "Service directory not found: $service_dir"
        return 1
    fi

    # Check if already running
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log_warning "$service service is already running (PID: $pid)"
            return 0
        fi
        rm -f "$pid_file"
    fi

    # Check if venv exists
    if [ ! -d "$service_dir/.venv" ]; then
        log_error "Virtual environment not found for $service. Run: cd services/$service && uv venv && uv pip install -e ."
        return 1
    fi

    log_info "Starting $service service on port $port..."

    cd "$service_dir"

    # Start the service in background
    nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$port" --reload > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    # Wait a moment and check if it started
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        log_success "$service service started (PID: $pid, Port: $port)"
    else
        log_error "$service service failed to start. Check logs: $log_file"
        rm -f "$pid_file"
        return 1
    fi
}

stop_service() {
    local service=$1
    local pid_file="$PID_DIR/${service}.pid"

    if [ ! -f "$pid_file" ]; then
        log_warning "$service service is not running (no PID file)"
        return 0
    fi

    local pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
        log_info "Stopping $service service (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 1
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        log_success "$service service stopped"
    else
        log_warning "$service service was not running"
    fi
    rm -f "$pid_file"
}

start_all_services() {
    for service in $SERVICE_NAMES; do
        start_service "$service"
    done
}

stop_all_services() {
    for service in $SERVICE_NAMES; do
        stop_service "$service"
    done
}

# =============================================================================
# Status Function
# =============================================================================

show_status() {
    echo ""
    echo "=========================================="
    echo "  AgriScheme Pro - Service Status"
    echo "=========================================="
    echo ""

    # Infrastructure status
    echo "Infrastructure:"
    cd "$PROJECT_ROOT"
    if docker compose ps postgres 2>/dev/null | grep -q "running"; then
        echo -e "  PostgreSQL: ${GREEN}Running${NC} (port 5433)"
    else
        echo -e "  PostgreSQL: ${RED}Stopped${NC}"
    fi

    if docker compose ps redis 2>/dev/null | grep -q "running"; then
        echo -e "  Redis:      ${GREEN}Running${NC} (port 6379)"
    else
        echo -e "  Redis:      ${RED}Stopped${NC}"
    fi

    echo ""
    echo "Microservices:"
    for service in $SERVICE_NAMES; do
        local port=$(get_port "$service")
        local pid_file="$PID_DIR/${service}.pid"
        local display_name=$(printf "%-8s" "$service")

        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "  $display_name ${GREEN}Running${NC} (PID: $pid, Port: $port)"
            else
                echo -e "  $display_name ${RED}Stopped${NC} (stale PID file)"
            fi
        else
            echo -e "  $display_name ${RED}Stopped${NC}"
        fi
    done

    echo ""
    echo "API Endpoints:"
    echo "  Auth:   http://localhost:9001/api/v1"
    echo "  Farmer: http://localhost:9002/api/v1"
    echo "  GIS:    http://localhost:9003/api/v1"
    echo ""
    echo "API Docs (Swagger UI):"
    echo "  Auth:   http://localhost:9001/docs"
    echo "  Farmer: http://localhost:9002/docs"
    echo "  GIS:    http://localhost:9003/docs"
    echo ""
}

# =============================================================================
# Help Function
# =============================================================================

show_help() {
    echo "AgriScheme Pro - Backend Services Startup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --infra-only     Start only infrastructure (PostgreSQL, Redis)"
    echo "  --no-migrate     Skip database migrations"
    echo "  --service=NAME   Start only specific service (auth, farmer, gis)"
    echo "  --stop           Stop all services"
    echo "  --status         Show service status"
    echo "  --logs=NAME      Tail logs for a service"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start all services"
    echo "  $0 --infra-only       # Start only PostgreSQL and Redis"
    echo "  $0 --service=auth     # Start only auth service"
    echo "  $0 --stop             # Stop all services"
    echo "  $0 --status           # Show service status"
    echo "  $0 --logs=farmer      # Tail farmer service logs"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
    ensure_dirs
    cd "$PROJECT_ROOT"

    local infra_only=false
    local no_migrate=false
    local specific_service=""
    local stop_services=false
    local show_status_only=false
    local tail_logs=""

    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --infra-only)
                infra_only=true
                ;;
            --no-migrate)
                no_migrate=true
                ;;
            --service=*)
                specific_service="${arg#*=}"
                ;;
            --stop)
                stop_services=true
                ;;
            --status)
                show_status_only=true
                ;;
            --logs=*)
                tail_logs="${arg#*=}"
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $arg"
                show_help
                exit 1
                ;;
        esac
    done

    # Handle --status
    if [ "$show_status_only" = true ]; then
        show_status
        exit 0
    fi

    # Handle --logs
    if [ -n "$tail_logs" ]; then
        local log_file="$LOG_DIR/${tail_logs}.log"
        if [ -f "$log_file" ]; then
            tail -f "$log_file"
        else
            log_error "Log file not found: $log_file"
            exit 1
        fi
        exit 0
    fi

    # Handle --stop
    if [ "$stop_services" = true ]; then
        stop_all_services
        stop_infrastructure
        exit 0
    fi

    echo ""
    echo "=========================================="
    echo "  AgriScheme Pro - Starting Services"
    echo "=========================================="
    echo ""

    # Start infrastructure
    start_infrastructure

    # Exit if infra-only
    if [ "$infra_only" = true ]; then
        show_status
        exit 0
    fi

    # Run migrations unless --no-migrate
    if [ "$no_migrate" = false ]; then
        run_migrations
    fi

    # Start services
    if [ -n "$specific_service" ]; then
        local port=$(get_port "$specific_service")
        if [ -z "$port" ]; then
            log_error "Unknown service: $specific_service"
            exit 1
        fi
        start_service "$specific_service"
    else
        start_all_services
    fi

    # Show final status
    show_status
}

main "$@"
