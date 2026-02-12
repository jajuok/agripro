#!/usr/bin/env bash
set -euo pipefail

# Configuration — override via environment or edit defaults
VPS_HOST="${VPS_HOST:-213.32.19.116}"
VPS_USER="${VPS_USER:-ubuntu}"
VPS_PORT="${VPS_PORT:-4491}"
REMOTE_DIR="${REMOTE_DIR:-/opt/agripro-pwa}"
SSH_OPTS="-p ${VPS_PORT}"
SCP_OPTS="-P ${VPS_PORT}"

echo "=== Building PWA ==="
cd "$(dirname "$0")/../../apps/mobile"
npm run build:pwa

echo "=== Copying assetlinks.json into dist ==="
INFRA_DIR="$(dirname "$0")"
mkdir -p dist/.well-known
cp "${INFRA_DIR}/assetlinks.json" dist/.well-known/assetlinks.json

echo "=== Creating remote directory ==="
ssh ${SSH_OPTS} "${VPS_USER}@${VPS_HOST}" "sudo mkdir -p ${REMOTE_DIR} && sudo chown -R ${VPS_USER}:${VPS_USER} ${REMOTE_DIR}"

echo "=== Uploading dist/ to VPS ==="
ssh ${SSH_OPTS} "${VPS_USER}@${VPS_HOST}" "rm -rf ${REMOTE_DIR}/dist"
scp ${SCP_OPTS} -r dist "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/"

echo "=== Uploading Caddyfile & docker-compose ==="
scp ${SCP_OPTS} "${INFRA_DIR}/Caddyfile" "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/Caddyfile"
scp ${SCP_OPTS} "${INFRA_DIR}/docker-compose.yml" "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/docker-compose.yml"

echo "=== Restarting Caddy ==="
ssh ${SSH_OPTS} "${VPS_USER}@${VPS_HOST}" "cd ${REMOTE_DIR} && docker compose up -d --force-recreate"

echo "=== Done! PWA deployed to https://app.${VPS_HOST}.sslip.io ==="
