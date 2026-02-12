#!/usr/bin/env bash
set -euo pipefail

# Configuration — override via environment or edit defaults
VPS_HOST="${VPS_HOST:-213.32.19.116}"
VPS_USER="${VPS_USER:-root}"
REMOTE_DIR="${REMOTE_DIR:-/opt/agripro-pwa}"

echo "=== Building PWA ==="
cd "$(dirname "$0")/../../apps/mobile"
npm run build:pwa

echo "=== Uploading dist/ to VPS ==="
scp -r dist/ "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/dist/"

echo "=== Uploading Caddyfile & docker-compose ==="
INFRA_DIR="$(dirname "$0")"
scp "${INFRA_DIR}/Caddyfile" "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/Caddyfile"
scp "${INFRA_DIR}/docker-compose.yml" "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/docker-compose.yml"
scp "${INFRA_DIR}/assetlinks.json" "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/assetlinks.json"

echo "=== Restarting Caddy ==="
ssh "${VPS_USER}@${VPS_HOST}" "cd ${REMOTE_DIR} && docker compose up -d --force-recreate"

echo "=== Done! PWA deployed to https://app.${VPS_HOST}.sslip.io ==="
