#!/bin/bash

# Build script for AgriScheme Pro Release APK
# This builds an APK configured to connect to deployed backend services

set -e

echo "=================================="
echo "AgriScheme Pro - Release APK Build"
echo "=================================="
echo ""

# Set production environment variables - Unified API Gateway
export EXPO_PUBLIC_API_URL="http://213.32.19.116:8888/api/v1"

echo "✓ Environment variables set for production"
echo "  - API Gateway: $EXPO_PUBLIC_API_URL"
echo "  - All services accessible through single entry point"
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
