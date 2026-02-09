#!/bin/bash
# Update nginx gateway configuration on server

SERVER="root@213.32.19.116"
NGINX_DIR="/tmp/nginx-gateway"

echo "Updating nginx gateway configuration..."
echo "========================================"

# Copy updated nginx.conf to server
echo "1. Copying nginx.conf to server..."
scp nginx.conf ${SERVER}:${NGINX_DIR}/nginx.conf

if [ $? -ne 0 ]; then
    echo "✗ Failed to copy nginx.conf"
    exit 1
fi

echo "✓ Configuration copied"

# Test nginx configuration
echo ""
echo "2. Testing nginx configuration..."
ssh ${SERVER} "docker exec agrischeme-nginx-gateway nginx -t"

if [ $? -ne 0 ]; then
    echo "✗ Nginx configuration test failed"
    exit 1
fi

echo "✓ Configuration valid"

# Reload nginx
echo ""
echo "3. Reloading nginx..."
ssh ${SERVER} "docker exec agrischeme-nginx-gateway nginx -s reload"

if [ $? -ne 0 ]; then
    echo "✗ Failed to reload nginx"
    exit 1
fi

echo "✓ Nginx reloaded successfully"
echo ""
echo "Gateway updated! Test with:"
echo "  curl http://213.32.19.116:8888/api/v1/auth/health"
