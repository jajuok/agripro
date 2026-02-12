#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Install bubblewrap if not present
if ! command -v bubblewrap &> /dev/null; then
  echo "Installing @bubblewrap/cli..."
  npm install -g @bubblewrap/cli
fi

# Generate keystore if it doesn't exist
if [ ! -f agripro-twa.keystore ]; then
  echo "Generating signing keystore..."
  keytool -genkeypair -v \
    -keystore agripro-twa.keystore \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -alias agripro \
    -dname "CN=AgriScheme Pro,O=AgriScheme,C=KE"
  echo ""
  echo "IMPORTANT: Run ./generate-assetlinks.sh to update the asset links file"
  echo ""
fi

# Initialize and build
echo "=== Building TWA APK ==="
bubblewrap init --manifest="twa-manifest.json"
bubblewrap build

echo ""
echo "=== Build complete ==="
echo "APK: app-release-signed.apk"
ls -lh app-release-signed.apk 2>/dev/null || echo "(check output directory for APK)"
