# AgriScheme Pro Mobile App - Release Build

## Build Information

**Version:** 0.1.0
**Build Date:** February 3, 2026
**APK Size:** 65 MB
**Package Name:** com.agrischeme.pro

## APK Location

```
android/app/build/outputs/apk/release/app-release.apk
```

## Backend Services Configuration

The app is configured to connect to the following deployed backend services:

### Primary Services
- **Auth Service:** http://eswo8kkw0owo8ckk00cgsc0g.213.32.19.116.sslip.io/api/v1
- **Farmer Service:** http://fswk00skcko8wgkcs840o4ok.213.32.19.116.sslip.io/api/v1
- **GIS Service:** http://ckscgcwgcckgk40g4sgkocsw.213.32.19.116.sslip.io/api/v1

### Additional Services (Available)
- **Farm Service:** http://e800ock8kkck4g80kkw4k4os.213.32.19.116.sslip.io/api/v1
- **Financial Service:** http://ksk48c04o0c4o00gs8ggo4go.213.32.19.116.sslip.io/api/v1
- **Market Service:** http://dgk8w048wcc0ckg00k0k0oc4.213.32.19.116.sslip.io/api/v1
- **AI Service:** http://dgos8sgc0ckgc0kco04gg4kw.213.32.19.116.sslip.io/api/v1
- **IoT Service:** http://rgc0c8so8c8kgckc4gskscc4.213.32.19.116.sslip.io/api/v1
- **Livestock Service:** http://rggcw4ocg4cswk8cokoswo00.213.32.19.116.sslip.io/api/v1
- **Task Service:** http://rckowgo8ogwogw8gc04o48ko.213.32.19.116.sslip.io/api/v1
- **Inventory Service:** http://i0gkkgkgs88ks44oo0csc84w.213.32.19.116.sslip.io/api/v1
- **Notification Service:** http://fsg84owk8cggwc844kkcgcoc.213.32.19.116.sslip.io/api/v1
- **Traceability Service:** http://eww0o8woscc4ckkg4kokwcoo.213.32.19.116.sslip.io/api/v1
- **Compliance Service:** http://v4c4c4k4g0wcwcc484cggk0k.213.32.19.116.sslip.io/api/v1
- **Integration Service:** http://gw8s0swo000g0wcsk4s444k0.213.32.19.116.sslip.io/api/v1

All services are deployed on OVHcloud VPS and are operational.

## Installation

### Prerequisites
- Android device or emulator running Android 5.0 (API 21) or higher
- USB debugging enabled (for physical device installation)
- ADB (Android Debug Bridge) installed on your computer

### Install on Connected Device

1. Connect your Android device via USB
2. Enable USB debugging on your device
3. Run the installation command:

```bash
adb install android/app/build/outputs/apk/release/app-release.apk
```

### Install via File Transfer

1. Copy the APK to your Android device
2. Open the APK file on your device
3. Allow installation from unknown sources if prompted
4. Complete the installation

## Rebuilding the APK

To rebuild the APK with updated configurations:

```bash
cd apps/mobile
./build-release.sh
```

The build script will:
1. Set production environment variables
2. Clean previous builds
3. Build the release APK with Gradle
4. Output the APK location and size

## Features

The mobile app includes:

- **User Authentication** (Login, Register, 2FA)
- **Farmer Profile Management**
- **Farm Registration** (Multi-step wizard)
- **Farm Location & Boundary** (GPS + Map)
- **Document Upload** (KYC documents)
- **Asset Management**
- **Crop Records**
- **Soil Test Records**
- **Offline Support** (with local storage)
- **Biometric Authentication** (Face ID / Fingerprint)

## Testing

### Test User Accounts

Create test accounts using the registration flow in the app, or use the API to create test users.

### Verify Backend Connectivity

The app will automatically connect to the deployed backend services. Check the app logs to verify successful API calls:

```bash
# View Android logs
adb logcat | grep -i "api\|error\|auth"
```

## Permissions Required

The app requests the following permissions:
- **Camera** - For document scanning and photo capture
- **Location** - For farm coordinate recording
- **Storage** - For document uploads
- **Biometric** - For secure authentication (optional)

## Security Notes

**Important:** This build uses a debug signing key. For production release to Google Play Store:

1. Generate a proper release keystore:
```bash
keytool -genkeypair -v -storetype PKCS12 -keystore agrischeme-release.keystore \
  -alias agrischeme -keyalg RSA -keysize 2048 -validity 10000
```

2. Update `android/app/build.gradle` to use the release keystore
3. Rebuild the APK with the release signing configuration

## Troubleshooting

### App Won't Install
- Uninstall any previous version first
- Ensure you have enough storage space (>100 MB)
- Check that USB debugging is enabled

### Can't Connect to Backend
- Verify internet connection
- Check if backend services are running (see service URLs above)
- Review app logs for error messages

### Build Fails
- Clean the build: `cd android && ./gradlew clean`
- Delete `node_modules` and reinstall: `yarn install`
- Clear Gradle cache: `rm -rf ~/.gradle/caches/`

## Support

For issues or questions:
- Check the app logs: `adb logcat`
- Review backend service health at: `/health` endpoint of each service
- Verify environment variables in `.env.production`

## Next Steps

After installation:
1. Launch the app
2. Create an account or log in
3. Complete your farmer profile
4. Register your first farm
5. Upload required documents
6. Start managing your agricultural operations
