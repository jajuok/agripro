#!/bin/bash

# Phase 5: Deploy Infrastructure Services
# Deploys Redis and Kafka

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/config/deployment.env"
load_secrets "${SCRIPT_DIR}/.secrets/deployment.secrets"

SERVER_IP=$1
DOMAIN=$2
SSH_KEY=$3

log_section "Phase 5: Infrastructure Services Deployment"

# =============================================================================
# DEPLOY REDIS
# =============================================================================

log_step "Deploying Redis"

remote_exec "$SERVER_IP" "$SSH_KEY" "
    docker run -d \
        --name agrischeme-redis \
        --network agrischeme-network \
        -e REDIS_PASSWORD=${REDIS_PASSWORD} \
        -v agrischeme-redis-data:/data \
        --restart unless-stopped \
        --health-cmd='redis-cli --pass ${REDIS_PASSWORD} ping | grep PONG' \
        --health-interval=10s \
        --health-timeout=5s \
        --health-retries=5 \
        redis:${REDIS_VERSION} \
        redis-server --requirepass ${REDIS_PASSWORD}
"

log_success "Redis deployed"

# =============================================================================
# DEPLOY KAFKA
# =============================================================================

log_step "Deploying Kafka cluster"

remote_exec "$SERVER_IP" "$SSH_KEY" "cat > /opt/agrischeme/docker-compose-kafka.yml << 'KAFKA_EOF'
version: '3.8'

networks:
  agrischeme-network:
    external: true

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:${KAFKA_VERSION}
    container_name: agrischeme-zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
    networks:
      - agrischeme-network
    restart: unless-stopped

  kafka:
    image: confluentinc/cp-kafka:${KAFKA_VERSION}
    container_name: agrischeme-kafka
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: agrischeme-zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://agrischeme-kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    volumes:
      - kafka-data:/var/lib/kafka/data
    networks:
      - agrischeme-network
    restart: unless-stopped

volumes:
  zookeeper-data:
  kafka-data:
KAFKA_EOF

    cd /opt/agrischeme
    docker compose -f docker-compose-kafka.yml up -d
"

log_success "Kafka cluster deployed"

# Wait for services
log_step "Waiting for services to be healthy"
sleep 20

log_success "Phase 5 completed: Infrastructure services deployed"
