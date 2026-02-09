# Quick Start: Install AgriScheme Pro Mobile App

## APK Details

- **File:** `apps/mobile/android/app/build/outputs/apk/release/app-release.apk`
- **Size:** 65 MB
- **MD5:** `342e15b6ae05a7133fdb7d4446f6e38c`
- **Package:** com.agrischeme.pro
- **Version:** 0.1.0

## Installation Methods

### Method 1: Install via ADB (Recommended for Development)

```bash
# Navigate to mobile app directory
cd apps/mobile

# Install on connected Android device
adb install android/app/build/outputs/apk/release/app-release.apk

# Or force reinstall (if app already installed)
adb install -r android/app/build/outputs/apk/release/app-release.apk
```

### Method 2: Manual Installation on Device

1. **Copy APK to your Android device:**
   ```bash
   # Using ADB
   adb push apps/mobile/android/app/build/outputs/apk/release/app-release.apk /sdcard/Download/

   # Or use Google Drive, email, or any file transfer method
   ```

2. **On your Android device:**
   - Open File Manager
   - Navigate to Downloads folder
   - Tap on `app-release.apk`
   - Allow installation from unknown sources if prompted
   - Tap "Install"
   - Wait for installation to complete
   - Tap "Open" to launch the app

### Method 3: Install via USB File Transfer

1. Connect your Android device to your computer via USB
2. Copy `apps/mobile/android/app/build/outputs/apk/release/app-release.apk` to your device's Downloads folder
3. Disconnect the device
4. Follow step 2 from Method 2 above

## Backend Services

The app is pre-configured to connect to deployed backend services on OVHcloud:

- ✓ Auth Service (eswo8kkw0owo8ckk00cgsc0g.213.32.19.116.sslip.io)
- ✓ Farmer Service (fswk00skcko8wgkcs840o4ok.213.32.19.116.sslip.io)
- ✓ GIS Service (ckscgcwgcckgk40g4sgkocsw.213.32.19.116.sslip.io)
- ✓ 12 additional services available

No configuration needed - just install and use!

## First Launch

1. **Launch the app** - Tap the AgriScheme Pro icon
2. **Register an account:**
   - Tap "Register"
   - Enter your details
   - Complete phone verification
   - Set up your password
3. **Log in** with your credentials
4. **Complete your farmer profile**
5. **Register your first farm**

## Troubleshooting

### "App not installed" error
- **Solution:** Uninstall any previous version first
  ```bash
  adb uninstall com.agrischeme.pro
  ```

### "Install blocked" or "Unknown sources"
- **Solution:** Enable installation from unknown sources
  - Go to Settings > Security
  - Enable "Unknown sources" or "Install unknown apps"
  - Try installation again

### Can't connect to backend
- **Check:** Internet connection is active
- **Verify:** Backend services are running (see Backend Services section)
- **Note:** The app requires active internet connection for API calls

### ADB not found
- **Install ADB:**
  - **Mac:** `brew install android-platform-tools`
  - **Linux:** `sudo apt-get install adb`
  - **Windows:** Download from Android Developer site

### Device not detected by ADB
- **Enable USB Debugging:**
  1. Go to Settings > About phone
  2. Tap "Build number" 7 times to enable Developer Options
  3. Go to Settings > Developer Options
  4. Enable "USB debugging"
  5. Connect device and allow USB debugging when prompted

## Rebuilding the APK

If you need to rebuild (e.g., after code changes):

```bash
cd apps/mobile
./build-release.sh
```

The build takes approximately 3-4 minutes.

## Device Requirements

- **Android:** 5.0 (Lollipop, API 21) or higher
- **Storage:** Minimum 100 MB free space
- **RAM:** Minimum 2 GB recommended
- **Internet:** Required for backend API calls
- **Permissions:** Camera, Location, Storage, Biometric (optional)

## Support

For detailed documentation, see:
- `apps/mobile/RELEASE.md` - Full release documentation
- `apps/mobile/README.md` - Development documentation

Backend service status: Check `/health` endpoint on any service URL
