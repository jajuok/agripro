import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Alert,
  ActivityIndicator,
  Modal,
  Platform,
} from 'react-native';

// Safely import expo-camera - it may not be available on all platforms
let CameraView: React.ComponentType<any> | null = null;
let useCameraPermissions: (() => [any, () => Promise<any>]) | null = null;
let cameraAvailable = false;

try {
  const cameraModule = require('expo-camera');
  CameraView = cameraModule.CameraView;
  useCameraPermissions = cameraModule.useCameraPermissions;
  cameraAvailable = true;
} catch {
  // expo-camera not available - will use gallery-only mode
  cameraAvailable = false;
}

type CameraFacing = 'back' | 'front';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';

type PhotoData = {
  uri: string;
  latitude: number | null;
  longitude: number | null;
  timestamp: string;
};

type PhotoCaptureProps = {
  onPhotoCapture: (photo: PhotoData) => void;
  onCancel?: () => void;
  showGalleryOption?: boolean;
  title?: string;
};

// Platform-aware location helper
const getGpsLocation = async (): Promise<{ latitude: number | null; longitude: number | null }> => {
  try {
    if (Platform.OS === 'web') {
      if (!navigator.geolocation) return { latitude: null, longitude: null };
      return new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
          () => resolve({ latitude: null, longitude: null }),
          { enableHighAccuracy: true, timeout: 10000 }
        );
      });
    }
    const Location = require('expo-location');
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') return { latitude: null, longitude: null };
    const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
    return { latitude: loc.coords.latitude, longitude: loc.coords.longitude };
  } catch {
    return { latitude: null, longitude: null };
  }
};

// Gallery-only fallback when camera is not available
const GalleryOnlyCapture: React.FC<PhotoCaptureProps> = ({
  onPhotoCapture,
  onCancel,
  title = 'Select Photo',
}) => {
  const [previewPhoto, setPreviewPhoto] = useState<PhotoData | null>(null);
  const webInputRef = useRef<HTMLInputElement | null>(null);

  const handleWebFileSelect = async (event: any) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const uri = URL.createObjectURL(file);
    const location = await getGpsLocation();
    setPreviewPhoto({
      uri,
      latitude: location.latitude,
      longitude: location.longitude,
      timestamp: new Date().toISOString(),
    });
  };

  const pickFromGallery = async () => {
    if (Platform.OS === 'web') {
      webInputRef.current?.click();
      return;
    }
    try {
      const ImagePicker = require('expo-image-picker');
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        const location = await getGpsLocation();
        const photoData: PhotoData = {
          uri: result.assets[0].uri,
          latitude: location.latitude,
          longitude: location.longitude,
          timestamp: new Date().toISOString(),
        };
        setPreviewPhoto(photoData);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick image from gallery.');
    }
  };

  const confirmPhoto = () => {
    if (previewPhoto) {
      onPhotoCapture(previewPhoto);
      setPreviewPhoto(null);
    }
  };

  const retakePhoto = () => {
    setPreviewPhoto(null);
  };

  // Preview mode
  if (previewPhoto) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Preview</Text>
        </View>

        <Image source={{ uri: previewPhoto.uri }} style={styles.previewImage} />

        {/* GPS info */}
        <View style={styles.gpsInfo}>
          {previewPhoto.latitude && previewPhoto.longitude ? (
            <Text style={styles.gpsText}>
              {previewPhoto.latitude.toFixed(6)}, {previewPhoto.longitude.toFixed(6)}
            </Text>
          ) : (
            <Text style={styles.gpsTextWarning}>No GPS data available</Text>
          )}
        </View>

        <View style={styles.previewActions}>
          <TouchableOpacity style={styles.retakeButton} onPress={retakePhoto}>
            <Text style={styles.retakeButtonText}>Choose Another</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.confirmButton} onPress={confirmPhoto}>
            <Text style={styles.confirmButtonText}>Use Photo</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Gallery selection mode
  return (
    <View style={styles.galleryOnlyContainer}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onCancel} style={styles.closeButton}>
          <Text style={styles.closeButtonText}>X</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{title}</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Hidden web file input */}
      {Platform.OS === 'web' && (
        <input
          ref={webInputRef as any}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleWebFileSelect}
          style={{ display: 'none' }}
        />
      )}

      <View style={styles.galleryOnlyContent}>
        <Text style={styles.galleryOnlyText}>
          {Platform.OS === 'web'
            ? 'Select a photo or take one with your camera.'
            : `Camera is not available on this device.\nPlease select a photo from your gallery.`}
        </Text>
        <TouchableOpacity style={styles.galleryOnlyButton} onPress={pickFromGallery}>
          <Text style={styles.galleryOnlyButtonText}>
            {Platform.OS === 'web' ? 'Choose Photo' : 'Open Gallery'}
          </Text>
        </TouchableOpacity>
        {onCancel && (
          <TouchableOpacity style={styles.cancelButton} onPress={onCancel}>
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

export const PhotoCapture: React.FC<PhotoCaptureProps> = ({
  onPhotoCapture,
  onCancel,
  showGalleryOption = true,
  title = 'Take Photo',
}) => {
  // Use camera permissions hook if available, otherwise use a dummy state
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const cameraPermissionResult = useCameraPermissions ? useCameraPermissions() : [null, async () => ({ granted: false })];
  const [permission, requestPermission] = cameraPermissionResult;
  const [facing, setFacing] = useState<CameraFacing>('back');
  const [isCapturing, setIsCapturing] = useState(false);
  const [previewPhoto, setPreviewPhoto] = useState<PhotoData | null>(null);
  const cameraRef = useRef<any>(null);

  // If camera is not available, show gallery-only mode
  if (!cameraAvailable) {
    return (
      <GalleryOnlyCapture
        onPhotoCapture={onPhotoCapture}
        onCancel={onCancel}
        title={title}
      />
    );
  }

  // Request permissions
  if (!permission) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>
          Camera permission is required to take photos.
        </Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>Grant Permission</Text>
        </TouchableOpacity>
        {onCancel && (
          <TouchableOpacity style={styles.cancelButton} onPress={onCancel}>
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  const takePhoto = async () => {
    if (!cameraRef.current || isCapturing) return;

    setIsCapturing(true);
    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        skipProcessing: false,
      });

      if (photo) {
        const location = await getGpsLocation();
        const photoData: PhotoData = {
          uri: photo.uri,
          latitude: location.latitude,
          longitude: location.longitude,
          timestamp: new Date().toISOString(),
        };
        setPreviewPhoto(photoData);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to take photo. Please try again.');
    } finally {
      setIsCapturing(false);
    }
  };

  const pickFromGallery = async () => {
    try {
      const ImagePicker = require('expo-image-picker');
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        const location = await getGpsLocation();
        const photoData: PhotoData = {
          uri: result.assets[0].uri,
          latitude: location.latitude,
          longitude: location.longitude,
          timestamp: new Date().toISOString(),
        };
        setPreviewPhoto(photoData);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick image from gallery.');
    }
  };

  const confirmPhoto = () => {
    if (previewPhoto) {
      onPhotoCapture(previewPhoto);
      setPreviewPhoto(null);
    }
  };

  const retakePhoto = () => {
    setPreviewPhoto(null);
  };

  const toggleFacing = () => {
    setFacing((current) => (current === 'back' ? 'front' : 'back'));
  };

  // Preview mode
  if (previewPhoto) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Preview</Text>
        </View>

        <Image source={{ uri: previewPhoto.uri }} style={styles.previewImage} />

        {/* GPS info */}
        <View style={styles.gpsInfo}>
          {previewPhoto.latitude && previewPhoto.longitude ? (
            <Text style={styles.gpsText}>
              📍 {previewPhoto.latitude.toFixed(6)}, {previewPhoto.longitude.toFixed(6)}
            </Text>
          ) : (
            <Text style={styles.gpsTextWarning}>⚠️ No GPS data available</Text>
          )}
        </View>

        <View style={styles.previewActions}>
          <TouchableOpacity style={styles.retakeButton} onPress={retakePhoto}>
            <Text style={styles.retakeButtonText}>Retake</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.confirmButton} onPress={confirmPhoto}>
            <Text style={styles.confirmButtonText}>Use Photo</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Camera mode
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onCancel} style={styles.closeButton}>
          <Text style={styles.closeButtonText}>✕</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{title}</Text>
        <View style={styles.placeholder} />
      </View>

      {CameraView && <CameraView ref={cameraRef} style={styles.camera} facing={facing}>
        {/* Overlay grid */}
        <View style={styles.gridOverlay}>
          <View style={styles.gridRow}>
            <View style={styles.gridCell} />
            <View style={[styles.gridCell, styles.gridCellBorder]} />
            <View style={styles.gridCell} />
          </View>
          <View style={[styles.gridRow, styles.gridRowBorder]}>
            <View style={styles.gridCell} />
            <View style={[styles.gridCell, styles.gridCellBorder]} />
            <View style={styles.gridCell} />
          </View>
          <View style={styles.gridRow}>
            <View style={styles.gridCell} />
            <View style={[styles.gridCell, styles.gridCellBorder]} />
            <View style={styles.gridCell} />
          </View>
        </View>
      </CameraView>}

      <View style={styles.controls}>
        {showGalleryOption && (
          <TouchableOpacity style={styles.galleryButton} onPress={pickFromGallery}>
            <Text style={styles.galleryButtonText}>Gallery</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity
          style={[styles.captureButton, isCapturing && styles.captureButtonDisabled]}
          onPress={takePhoto}
          disabled={isCapturing}
        >
          {isCapturing ? (
            <ActivityIndicator size="small" color={COLORS.white} />
          ) : (
            <View style={styles.captureButtonInner} />
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.flipButton} onPress={toggleFacing}>
          <Text style={styles.flipButtonText}>🔄</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// Compact photo picker component
type PhotoPickerProps = {
  photos: PhotoData[];
  onAddPhoto: () => void;
  onRemovePhoto: (index: number) => void;
  maxPhotos?: number;
};

export const PhotoPicker: React.FC<PhotoPickerProps> = ({
  photos,
  onAddPhoto,
  onRemovePhoto,
  maxPhotos = 5,
}) => {
  return (
    <View style={styles.pickerContainer}>
      <View style={styles.photoGrid}>
        {photos.map((photo, index) => (
          <View key={index} style={styles.photoItem}>
            <Image source={{ uri: photo.uri }} style={styles.photoThumbnail} />
            <TouchableOpacity
              style={styles.removeButton}
              onPress={() => onRemovePhoto(index)}
            >
              <Text style={styles.removeButtonText}>✕</Text>
            </TouchableOpacity>
            {photo.latitude && (
              <View style={styles.gpsIndicator}>
                <Text style={styles.gpsIndicatorText}>📍</Text>
              </View>
            )}
          </View>
        ))}

        {photos.length < maxPhotos && (
          <TouchableOpacity style={styles.addPhotoButton} onPress={onAddPhoto}>
            <Text style={styles.addPhotoIcon}>+</Text>
            <Text style={styles.addPhotoText}>Add Photo</Text>
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.photoCount}>
        {photos.length} / {maxPhotos} photos
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.black,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    backgroundColor: COLORS.black,
  },
  headerTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.white,
  },
  closeButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeButtonText: {
    fontSize: 24,
    color: COLORS.white,
  },
  placeholder: {
    width: 40,
  },
  camera: {
    flex: 1,
  },
  gridOverlay: {
    flex: 1,
  },
  gridRow: {
    flex: 1,
    flexDirection: 'row',
  },
  gridRowBorder: {
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  gridCell: {
    flex: 1,
  },
  gridCellBorder: {
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingVertical: SPACING.lg,
    backgroundColor: COLORS.black,
  },
  captureButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: COLORS.white,
    alignItems: 'center',
    justifyContent: 'center',
  },
  captureButtonDisabled: {
    opacity: 0.5,
  },
  captureButtonInner: {
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: COLORS.white,
    borderWidth: 3,
    borderColor: COLORS.black,
  },
  galleryButton: {
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
  },
  galleryButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
  },
  flipButton: {
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
  },
  flipButtonText: {
    fontSize: 24,
  },
  previewImage: {
    flex: 1,
    resizeMode: 'contain',
  },
  gpsInfo: {
    padding: SPACING.md,
    backgroundColor: COLORS.gray[900],
  },
  gpsText: {
    color: COLORS.success,
    fontSize: FONT_SIZES.sm,
    textAlign: 'center',
  },
  gpsTextWarning: {
    color: COLORS.warning,
    fontSize: FONT_SIZES.sm,
    textAlign: 'center',
  },
  previewActions: {
    flexDirection: 'row',
    padding: SPACING.md,
    gap: SPACING.md,
    backgroundColor: COLORS.black,
  },
  retakeButton: {
    flex: 1,
    paddingVertical: SPACING.md,
    borderRadius: 8,
    backgroundColor: COLORS.gray[700],
    alignItems: 'center',
  },
  retakeButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
  },
  confirmButton: {
    flex: 1,
    paddingVertical: SPACING.md,
    borderRadius: 8,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
  },
  confirmButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
  },
  permissionContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.xl,
    backgroundColor: COLORS.gray[100],
  },
  permissionText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[700],
    textAlign: 'center',
    marginBottom: SPACING.lg,
  },
  permissionButton: {
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
  },
  cancelButton: {
    marginTop: SPACING.md,
    paddingVertical: SPACING.sm,
  },
  cancelButtonText: {
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
  // Photo picker styles
  pickerContainer: {
    padding: SPACING.md,
  },
  photoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  photoItem: {
    position: 'relative',
  },
  photoThumbnail: {
    width: 80,
    height: 80,
    borderRadius: 8,
  },
  removeButton: {
    position: 'absolute',
    top: -8,
    right: -8,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: COLORS.error,
    alignItems: 'center',
    justifyContent: 'center',
  },
  removeButtonText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: 'bold',
  },
  gpsIndicator: {
    position: 'absolute',
    bottom: 4,
    left: 4,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    borderRadius: 4,
    padding: 2,
  },
  gpsIndicatorText: {
    fontSize: 10,
  },
  addPhotoButton: {
    width: 80,
    height: 80,
    borderRadius: 8,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: COLORS.gray[400],
    alignItems: 'center',
    justifyContent: 'center',
  },
  addPhotoIcon: {
    fontSize: 24,
    color: COLORS.gray[500],
  },
  addPhotoText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[500],
    marginTop: 2,
  },
  photoCount: {
    marginTop: SPACING.sm,
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
  },
  // Gallery-only mode styles
  galleryOnlyContainer: {
    flex: 1,
    backgroundColor: COLORS.gray[100],
  },
  galleryOnlyContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.xl,
  },
  galleryOnlyText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[700],
    textAlign: 'center',
    marginBottom: SPACING.xl,
    lineHeight: 24,
  },
  galleryOnlyButton: {
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    marginBottom: SPACING.md,
  },
  galleryOnlyButtonText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
  },
});

export default PhotoCapture;
