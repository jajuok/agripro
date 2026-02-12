#!/bin/bash

# Build script for AgriScheme Pro Release APK
# This builds an APK configured to connect to deployed backend services

set -e

echo "=================================="
echo "AgriScheme Pro - Release APK Build"
echo "=================================="
echo ""

# Load production environment from .env file
# Individual service URLs routed via Coolify's Traefik (port 80)
# EXPO_PUBLIC_API_URL is intentionally NOT set so the app uses
# per-service FQDNs (e.g. farmer.213.32.19.116.sslip.io)
if [ -f ".env" ]; then
  set -a
  source .env
  set +a
fi

echo "✓ Environment variables set for production"
echo "  - Mode: Individual service URLs via Traefik"
echo "  - Auth: ${EXPO_PUBLIC_AUTH_URL:-not set}"
echo "  - Farmer: ${EXPO_PUBLIC_FARMER_URL:-not set}"
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
cd android
./gradlew clean
cd ..
echo "✓ Clean complete"
echo ""

# Skip pre-bundling - Gradle will handle it
echo "Skipping pre-bundle (Gradle will bundle during build)..."
echo ""

# Build the release APK
echo "Building release APK..."
cd android
./gradlew assembleRelease
cd ..
echo "✓ APK build complete"
echo ""

# Find and display the APK location
APK_PATH="android/app/build/outputs/apk/release/app-release.apk"
if [ -f "$APK_PATH" ]; then
    APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
    echo "=================================="
    echo "✓ Build successful!"
    echo "=================================="
    echo ""
    echo "APK Location: $APK_PATH"
    echo "APK Size: $APK_SIZE"
    echo ""
    echo "To install on connected device:"
    echo "  adb install $APK_PATH"
    echo ""
else
    echo "ERROR: APK not found at expected location"
    exit 1
fi
