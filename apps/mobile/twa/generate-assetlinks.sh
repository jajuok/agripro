#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

KEYSTORE="agripro-twa.keystore"
ALIAS="agripro"
OUTPUT="../../../infrastructure/pwa/assetlinks.json"

if [ ! -f "$KEYSTORE" ]; then
  echo "Error: Keystore not found. Run build-twa.sh first to generate it."
  exit 1
fi

# Extract SHA-256 fingerprint
FINGERPRINT=$(keytool -list -v -keystore "$KEYSTORE" -alias "$ALIAS" 2>/dev/null \
  | grep "SHA256:" \
  | sed 's/.*SHA256: //')

if [ -z "$FINGERPRINT" ]; then
  echo "Error: Could not extract SHA-256 fingerprint."
  exit 1
fi

echo "SHA-256 fingerprint: $FINGERPRINT"

cat > "$OUTPUT" << EOF
[
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "com.agrischeme.pro",
      "sha256_cert_fingerprints": [
        "$FINGERPRINT"
      ]
    }
  }
]
EOF

echo "Asset links written to: $OUTPUT"
echo "Deploy this file to /.well-known/assetlinks.json on the PWA host."
