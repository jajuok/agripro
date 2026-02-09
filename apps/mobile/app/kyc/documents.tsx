import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Image,
  TextInput,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useAuthStore } from '@/store/auth';
import { useKYCStore } from '@/store/kyc';
import { Button } from '@/components/Button';

type DocumentType = {
  type: string;
  label: string;
  icon: string;
  description: string;
  required: boolean;
};

const DOCUMENT_TYPES: DocumentType[] = [
  {
    type: 'national_id',
    label: 'National ID',
    icon: '🆔',
    description: 'Government issued ID card',
    required: true,
  },
  {
    type: 'land_title',
    label: 'Land Title Deed',
    icon: '📄',
    description: 'Proof of land ownership',
    required: false,
  },
  {
    type: 'lease_agreement',
    label: 'Lease Agreement',
    icon: '📋',
    description: 'If leasing the land',
    required: false,
  },
  {
    type: 'bank_statement',
    label: 'Bank Statement',
    icon: '🏦',
    description: 'Recent bank statement',
    required: false,
  },
  {
    type: 'tax_id',
    label: 'Tax ID (PIN)',
    icon: '💳',
    description: 'KRA PIN certificate',
    required: false,
  },
];

export default function DocumentsScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { status, isLoading, uploadDocument, getStatus, completeStep } = useKYCStore();

  const [selectedDocument, setSelectedDocument] = useState<DocumentType | null>(null);
  const [documentNumber, setDocumentNumber] = useState('');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [uploadingDoc, setUploadingDoc] = useState(false);

  const farmerId = user?.id;

  useEffect(() => {
    if (farmerId && !status) {
      getStatus(farmerId);
    }
  }, [farmerId]);

  const requestCameraPermission = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert(
        'Permission Required',
        'Camera permission is required to capture documents'
      );
      return false;
    }
    return true;
  };

  const requestMediaLibraryPermission = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert(
        'Permission Required',
        'Photo library permission is required to select documents'
      );
      return false;
    }
    return true;
  };

  const handleSelectDocument = (doc: DocumentType) => {
    setSelectedDocument(doc);
    setDocumentNumber('');
    setSelectedImage(null);
  };

  const handleTakePhoto = async () => {
    const hasPermission = await requestCameraPermission();
    if (!hasPermission) return;

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setSelectedImage(result.assets[0].uri);
    }
  };

  const handlePickImage = async () => {
    const hasPermission = await requestMediaLibraryPermission();
    if (!hasPermission) return;

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setSelectedImage(result.assets[0].uri);
    }
  };

  const handleUpload = async () => {
    if (!selectedDocument || !selectedImage || !farmerId) {
      Alert.alert('Error', 'Please select a document type and capture/select an image');
      return;
    }

    setUploadingDoc(true);
    try {
      // Create form data with image file
      const fileUri = selectedImage;
      const filename = fileUri.split('/').pop() || 'document.jpg';
      const match = /\.(\w+)$/.exec(filename);
      const type = match ? `image/${match[1]}` : 'image/jpeg';

      const file = {
        uri: fileUri,
        name: filename,
        type,
      };

      await uploadDocument(farmerId, file, selectedDocument.type, documentNumber || undefined);

      Alert.alert('Success', 'Document uploaded successfully');
      setSelectedDocument(null);
      setDocumentNumber('');
      setSelectedImage(null);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to upload document');
    } finally {
      setUploadingDoc(false);
    }
  };

  const handleCompleteStep = async () => {
    if (!farmerId) return;

    try {
      await completeStep(farmerId, 'documents');
      Alert.alert('Success', 'Document step completed', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to complete step');
    }
  };

  const isDocumentSubmitted = (docType: string): boolean => {
    return status?.documents_submitted?.some((d) => d.document_type === docType && d.is_submitted) || false;
  };

  const getDocumentStatus = (docType: string) => {
    const doc = status?.documents_submitted?.find((d) => d.document_type === docType);
    if (!doc || !doc.is_submitted) return null;
    return doc.is_verified ? 'Verified' : 'Pending Review';
  };

  if (!status && isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Upload Documents</Text>
          <Text style={styles.subtitle}>
            Upload clear photos or scans of your documents for verification
          </Text>
        </View>

        {/* Document Types List */}
        <View style={styles.documentList}>
          {DOCUMENT_TYPES.map((doc) => {
            const isSubmitted = isDocumentSubmitted(doc.type);
            const docStatus = getDocumentStatus(doc.type);

            return (
              <TouchableOpacity
                key={doc.type}
                style={[
                  styles.documentCard,
                  selectedDocument?.type === doc.type && styles.documentCardSelected,
                  isSubmitted && styles.documentCardSubmitted,
                ]}
                onPress={() => !isSubmitted && handleSelectDocument(doc)}
                disabled={isSubmitted}
              >
                <View style={styles.documentHeader}>
                  <Text style={styles.documentIcon}>{doc.icon}</Text>
                  <View style={styles.documentInfo}>
                    <View style={styles.documentTitleRow}>
                      <Text style={styles.documentLabel}>{doc.label}</Text>
                      {doc.required && (
                        <View style={styles.requiredBadge}>
                          <Text style={styles.requiredText}>Required</Text>
                        </View>
                      )}
                      {isSubmitted && (
                        <View style={styles.statusBadge}>
                          <Text style={styles.statusBadgeText}>
                            {docStatus === 'Verified' ? '✓' : '⏳'} {docStatus}
                          </Text>
                        </View>
                      )}
                    </View>
                    <Text style={styles.documentDescription}>{doc.description}</Text>
                  </View>
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Upload Form */}
        {selectedDocument && (
          <View style={styles.uploadForm}>
            <Text style={styles.formTitle}>
              Upload {selectedDocument.label}
            </Text>

            {/* Document Number Input */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                Document Number (Optional)
              </Text>
              <TextInput
                style={styles.input}
                value={documentNumber}
                onChangeText={setDocumentNumber}
                placeholder={`Enter ${selectedDocument.label.toLowerCase()} number`}
                placeholderTextColor={COLORS.gray[400]}
              />
            </View>

            {/* Image Preview */}
            {selectedImage && (
              <View style={styles.imagePreview}>
                <Image source={{ uri: selectedImage }} style={styles.previewImage} />
                <TouchableOpacity
                  style={styles.removeImageButton}
                  onPress={() => setSelectedImage(null)}
                >
                  <Text style={styles.removeImageText}>×</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Capture Buttons */}
            {!selectedImage && (
              <View style={styles.captureButtons}>
                <TouchableOpacity style={styles.captureButton} onPress={handleTakePhoto}>
                  <Text style={styles.captureButtonIcon}>📷</Text>
                  <Text style={styles.captureButtonText}>Take Photo</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.captureButton} onPress={handlePickImage}>
                  <Text style={styles.captureButtonIcon}>🖼️</Text>
                  <Text style={styles.captureButtonText}>Choose from Gallery</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Upload Button */}
            {selectedImage && (
              <Button
                title="Upload Document"
                onPress={handleUpload}
                loading={uploadingDoc}
                disabled={uploadingDoc}
              />
            )}

            <TouchableOpacity
              style={styles.cancelButton}
              onPress={() => {
                setSelectedDocument(null);
                setDocumentNumber('');
                setSelectedImage(null);
              }}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Complete Step Button */}
        {!selectedDocument && status && status.documents_submitted.length > 0 && (
          <View style={styles.completeSection}>
            <Text style={styles.completeText}>
              {status.missing_documents.length === 0
                ? 'All required documents uploaded!'
                : `${status.missing_documents.length} required document(s) remaining`}
            </Text>

            {status.missing_documents.length === 0 && (
              <Button
                title="Complete Document Step"
                onPress={handleCompleteStep}
                loading={isLoading}
                disabled={isLoading}
              />
            )}

            <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
              <Text style={styles.backButtonText}>Back to Dashboard</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.gray[50],
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: SPACING.lg,
  },
  header: {
    marginBottom: SPACING.xl,
  },
  title: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: SPACING.xs,
  },
  subtitle: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[600],
    lineHeight: 22,
  },
  documentList: {
    marginBottom: SPACING.xl,
  },
  documentCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderWidth: 2,
    borderColor: COLORS.gray[200],
  },
  documentCardSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  documentCardSubmitted: {
    borderColor: COLORS.success,
    backgroundColor: COLORS.success + '05',
  },
  documentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  documentIcon: {
    fontSize: 32,
    marginRight: SPACING.sm,
  },
  documentInfo: {
    flex: 1,
  },
  documentTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.xs / 2,
  },
  documentLabel: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginRight: SPACING.xs,
  },
  requiredBadge: {
    backgroundColor: COLORS.error,
    paddingHorizontal: SPACING.xs,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: SPACING.xs,
  },
  requiredText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.xs,
    fontWeight: '500',
  },
  statusBadge: {
    backgroundColor: COLORS.success,
    paddingHorizontal: SPACING.xs,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusBadgeText: {
    color: COLORS.white,
    fontSize: FONT_SIZES.xs,
    fontWeight: '500',
  },
  documentDescription: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
  },
  uploadForm: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.lg,
    marginBottom: SPACING.xl,
  },
  formTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.md,
  },
  inputGroup: {
    marginBottom: SPACING.md,
  },
  inputLabel: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '500',
    color: COLORS.gray[700],
    marginBottom: SPACING.xs,
  },
  input: {
    backgroundColor: COLORS.gray[50],
    borderWidth: 1,
    borderColor: COLORS.gray[300],
    borderRadius: 8,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[900],
  },
  imagePreview: {
    position: 'relative',
    marginBottom: SPACING.md,
  },
  previewImage: {
    width: '100%',
    height: 200,
    borderRadius: 8,
    resizeMode: 'cover',
  },
  removeImageButton: {
    position: 'absolute',
    top: SPACING.xs,
    right: SPACING.xs,
    backgroundColor: COLORS.error,
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeImageText: {
    color: COLORS.white,
    fontSize: 24,
    fontWeight: 'bold',
  },
  captureButtons: {
    flexDirection: 'row',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  captureButton: {
    flex: 1,
    backgroundColor: COLORS.gray[100],
    borderRadius: 8,
    padding: SPACING.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.gray[300],
  },
  captureButtonIcon: {
    fontSize: 32,
    marginBottom: SPACING.xs,
  },
  captureButtonText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
    fontWeight: '500',
  },
  cancelButton: {
    alignItems: 'center',
    padding: SPACING.sm,
    marginTop: SPACING.sm,
  },
  cancelButtonText: {
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
  completeSection: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: SPACING.lg,
  },
  completeText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[700],
    textAlign: 'center',
    marginBottom: SPACING.md,
  },
  backButton: {
    alignItems: 'center',
    padding: SPACING.md,
    marginTop: SPACING.sm,
  },
  backButtonText: {
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
});
