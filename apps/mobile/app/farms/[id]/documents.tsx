import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  Image,
  Modal,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as DocumentPicker from 'expo-document-picker';
import { COLORS, SPACING, FONT_SIZES } from '@/utils/constants';
import { useFarmStore } from '@/store/farm';
import { StepIndicatorCompact } from '@/components/StepIndicator';
import { PhotoCapture, PhotoPicker } from '@/components/PhotoCapture';
import { Button } from '@/components/Button';

const REGISTRATION_STEPS = [
  { key: 'location', label: 'Location' },
  { key: 'boundary', label: 'Boundary' },
  { key: 'land_details', label: 'Land' },
  { key: 'documents', label: 'Documents' },
  { key: 'soil_water', label: 'Soil & Water' },
  { key: 'crops', label: 'Crops' },
  { key: 'review', label: 'Review' },
];

const DOCUMENT_TYPES = [
  { value: 'title_deed', label: 'Title Deed', icon: '📜' },
  { value: 'lease_agreement', label: 'Lease Agreement', icon: '📋' },
  { value: 'sale_agreement', label: 'Sale Agreement', icon: '🤝' },
  { value: 'allotment_letter', label: 'Allotment Letter', icon: '📨' },
  { value: 'succession_certificate', label: 'Succession Certificate', icon: '📝' },
  { value: 'other', label: 'Other Document', icon: '📄' },
];

type PhotoData = {
  uri: string;
  latitude: number | null;
  longitude: number | null;
  timestamp: string;
};

type Document = {
  type: string;
  name: string;
  uri: string;
  mimeType?: string;
};

export default function DocumentsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { addDocument, updateDraft, isLoading } = useFarmStore();

  const [documents, setDocuments] = useState<Document[]>([]);
  const [farmPhotos, setFarmPhotos] = useState<PhotoData[]>([]);
  const [showCamera, setShowCamera] = useState(false);
  const [selectedDocType, setSelectedDocType] = useState<string | null>(null);

  const handlePickDocument = async (docType: string) => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/*'],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];
        const newDoc: Document = {
          type: docType,
          name: asset.name,
          uri: asset.uri,
          mimeType: asset.mimeType,
        };
        setDocuments((prev) => [...prev, newDoc]);
        setSelectedDocType(null);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick document.');
    }
  };

  const handleRemoveDocument = (index: number) => {
    Alert.alert(
      'Remove Document',
      'Are you sure you want to remove this document?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => setDocuments((prev) => prev.filter((_, i) => i !== index)),
        },
      ]
    );
  };

  const handlePhotoCapture = (photo: PhotoData) => {
    setFarmPhotos((prev) => [...prev, photo]);
    setShowCamera(false);
  };

  const handleRemovePhoto = (index: number) => {
    setFarmPhotos((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    if (!id) {
      Alert.alert('Error', 'Farm ID not found.');
      return;
    }

    try {
      // Upload documents
      for (const doc of documents) {
        await addDocument(id, {
          documentType: doc.type,
          name: doc.name,
          uri: doc.uri,
          mimeType: doc.mimeType,
        });
      }

      // Upload photos
      for (const photo of farmPhotos) {
        await addDocument(id, {
          documentType: 'farm_photo',
          name: `Farm Photo ${photo.timestamp}`,
          uri: photo.uri,
          latitude: photo.latitude,
          longitude: photo.longitude,
          capturedAt: photo.timestamp,
        });
      }

      router.push(`/farms/${id}/soil-water`);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to save documents.');
    }
  };

  const handleSkip = () => {
    Alert.alert(
      'Skip Documents',
      'You can add documents later. Continue without uploading?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Skip',
          onPress: () => router.push(`/farms/${id}/soil-water`),
        },
      ]
    );
  };

  const getDocTypeLabel = (value: string) => {
    const docType = DOCUMENT_TYPES.find((t) => t.value === value);
    return docType ? docType.label : value;
  };

  const getDocTypeIcon = (value: string) => {
    const docType = DOCUMENT_TYPES.find((t) => t.value === value);
    return docType ? docType.icon : '📄';
  };

  // Camera modal
  if (showCamera) {
    return (
      <Modal visible={showCamera} animationType="slide">
        <PhotoCapture
          onPhotoCapture={handlePhotoCapture}
          onCancel={() => setShowCamera(false)}
          title="Take Farm Photo"
        />
      </Modal>
    );
  }

  // Document type selection modal
  if (selectedDocType !== null) {
    return (
      <Modal visible={true} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Select Document Type</Text>

            {DOCUMENT_TYPES.map((type) => (
              <TouchableOpacity
                key={type.value}
                style={styles.docTypeOption}
                onPress={() => handlePickDocument(type.value)}
              >
                <Text style={styles.docTypeIcon}>{type.icon}</Text>
                <Text style={styles.docTypeLabel}>{type.label}</Text>
              </TouchableOpacity>
            ))}

            <TouchableOpacity
              style={styles.modalCancelButton}
              onPress={() => setSelectedDocType(null)}
            >
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    );
  }

  return (
    <View style={styles.container}>
      {/* Progress */}
      <StepIndicatorCompact
        steps={REGISTRATION_STEPS}
        currentStep="documents"
        completedSteps={['location', 'boundary', 'land_details']}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Documents & Photos</Text>
          <Text style={styles.subtitle}>
            Upload land ownership documents and photos of your farm.
          </Text>
        </View>

        {/* Land Documents Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Land Documents</Text>
          <Text style={styles.sectionSubtitle}>
            Upload title deed, lease agreement, or other ownership documents.
          </Text>

          {/* Document List */}
          {documents.length > 0 && (
            <View style={styles.documentList}>
              {documents.map((doc, index) => (
                <View key={index} style={styles.documentItem}>
                  <View style={styles.documentInfo}>
                    <Text style={styles.documentIcon}>{getDocTypeIcon(doc.type)}</Text>
                    <View style={styles.documentDetails}>
                      <Text style={styles.documentName} numberOfLines={1}>
                        {doc.name}
                      </Text>
                      <Text style={styles.documentType}>
                        {getDocTypeLabel(doc.type)}
                      </Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    onPress={() => handleRemoveDocument(index)}
                    style={styles.removeButton}
                  >
                    <Text style={styles.removeButtonText}>Remove</Text>
                  </TouchableOpacity>
                </View>
              ))}
            </View>
          )}

          {/* Add Document Button */}
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setSelectedDocType('')}
          >
            <Text style={styles.addButtonIcon}>+</Text>
            <Text style={styles.addButtonText}>Add Document</Text>
          </TouchableOpacity>
        </View>

        {/* Farm Photos Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Farm Photos</Text>
          <Text style={styles.sectionSubtitle}>
            Take GPS-tagged photos of your farm. These help verify your farm location.
          </Text>

          <PhotoPicker
            photos={farmPhotos}
            onAddPhoto={() => setShowCamera(true)}
            onRemovePhoto={handleRemovePhoto}
            maxPhotos={10}
          />
        </View>

        {/* Info Card */}
        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>Why upload documents?</Text>
          <Text style={styles.infoText}>
            Documents help verify your farm ownership and can be used for:
          </Text>
          <View style={styles.infoList}>
            <Text style={styles.infoListItem}>• Loan applications</Text>
            <Text style={styles.infoListItem}>• Subsidy eligibility</Text>
            <Text style={styles.infoListItem}>• Insurance claims</Text>
            <Text style={styles.infoListItem}>• Government programs</Text>
          </View>
        </View>

        {/* Navigation Buttons */}
        <View style={styles.buttonContainer}>
          <Button
            title="Save & Continue"
            onPress={handleSave}
            loading={isLoading}
            disabled={isLoading}
          />
        </View>

        <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
          <Text style={styles.skipButtonText}>Skip for now</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.gray[50],
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
  section: {
    marginBottom: SPACING.xl,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.gray[900],
    marginBottom: SPACING.xs,
  },
  sectionSubtitle: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
    marginBottom: SPACING.md,
  },
  documentList: {
    marginBottom: SPACING.md,
  },
  documentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.white,
    padding: SPACING.md,
    borderRadius: 8,
    marginBottom: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.gray[200],
  },
  documentInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  documentIcon: {
    fontSize: 24,
    marginRight: SPACING.sm,
  },
  documentDetails: {
    flex: 1,
  },
  documentName: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[900],
    fontWeight: '500',
  },
  documentType: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.gray[500],
    marginTop: 2,
  },
  removeButton: {
    padding: SPACING.xs,
  },
  removeButtonText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.error,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.md,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: COLORS.primary,
  },
  addButtonIcon: {
    fontSize: 24,
    color: COLORS.primary,
    marginRight: SPACING.xs,
  },
  addButtonText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.primary,
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: COLORS.info + '10',
    borderRadius: 12,
    padding: SPACING.lg,
    marginBottom: SPACING.xl,
    borderWidth: 1,
    borderColor: COLORS.info + '30',
  },
  infoTitle: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.info,
    marginBottom: SPACING.xs,
  },
  infoText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[700],
    marginBottom: SPACING.sm,
  },
  infoList: {
    marginLeft: SPACING.xs,
  },
  infoListItem: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.gray[600],
    marginBottom: 2,
  },
  buttonContainer: {
    marginBottom: SPACING.md,
  },
  skipButton: {
    alignItems: 'center',
    padding: SPACING.sm,
  },
  skipButtonText: {
    color: COLORS.primary,
    fontSize: FONT_SIZES.md,
  },
  backButton: {
    alignItems: 'center',
    padding: SPACING.md,
  },
  backButtonText: {
    color: COLORS.gray[600],
    fontSize: FONT_SIZES.md,
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: COLORS.white,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: SPACING.lg,
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: FONT_SIZES.lg,
    fontWeight: 'bold',
    color: COLORS.gray[900],
    marginBottom: SPACING.lg,
    textAlign: 'center',
  },
  docTypeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
    borderRadius: 8,
    marginBottom: SPACING.sm,
    backgroundColor: COLORS.gray[50],
  },
  docTypeIcon: {
    fontSize: 24,
    marginRight: SPACING.md,
  },
  docTypeLabel: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[800],
  },
  modalCancelButton: {
    alignItems: 'center',
    padding: SPACING.md,
    marginTop: SPACING.md,
  },
  modalCancelText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.gray[600],
  },
});
