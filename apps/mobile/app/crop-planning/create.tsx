import { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Switch,
} from 'react-native';
import { router } from 'expo-router';
import { useCropPlanningStore } from '@/store/crop-planning';
import { useAuthStore } from '@/store/auth';
import { useFarmStore } from '@/store/farm';
import { COLORS, SEASONS, SEASON_LABELS } from '@/utils/constants';
import { StepIndicatorCompact } from '@/components/StepIndicator';
import type { CropCalendarTemplate } from '@/types/crop-planning';

const steps = [
  { key: 'farm', label: 'Farm & Crop' },
  { key: 'template', label: 'Template' },
  { key: 'details', label: 'Details' },
  { key: 'review', label: 'Review' },
];

const TENANT_ID = '00000000-0000-0000-0000-000000000001';

export default function CreatePlanScreen() {
  const user = useAuthStore((s) => s.user);
  const { farms, fetchFarms } = useFarmStore();
  const { templates, fetchTemplates, updateCreateDraft, createPlan, isLoading } = useCropPlanningStore();

  const [currentStep, setCurrentStep] = useState('farm');
  const [farmId, setFarmId] = useState('');
  const [farmName, setFarmName] = useState('');
  const [cropName, setCropName] = useState('');
  const [variety, setVariety] = useState('');
  const [season, setSeason] = useState('long_rains');
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [plantingDate, setPlantingDate] = useState('');
  const [harvestDate, setHarvestDate] = useState('');
  const [acreage, setAcreage] = useState('');
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [notes, setNotes] = useState('');
  const [generateActivities, setGenerateActivities] = useState(true);
  const [templateLoading, setTemplateLoading] = useState(false);

  useEffect(() => {
    if (user?.farmerId) fetchFarms(user.farmerId);
  }, [user?.farmerId]);

  // Fetch matching templates when crop name or season changes
  const fetchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (fetchTimeoutRef.current) clearTimeout(fetchTimeoutRef.current);
    if (cropName.trim().length >= 2) {
      fetchTimeoutRef.current = setTimeout(async () => {
        setTemplateLoading(true);
        try {
          await fetchTemplates(TENANT_ID, { cropName: cropName.trim(), season, pageSize: 20 });
        } catch {}
        setTemplateLoading(false);
      }, 300);
    }
    return () => { if (fetchTimeoutRef.current) clearTimeout(fetchTimeoutRef.current); };
  }, [cropName, season]);

  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId) || null;

  const selectTemplate = (template: CropCalendarTemplate) => {
    setSelectedTemplateId(template.id);
    if (template.variety && !variety) setVariety(template.variety);
    // Auto-compute harvest date from template if planting date exists
    if (plantingDate && template.totalDaysToHarvest) {
      const d = new Date(plantingDate);
      d.setDate(d.getDate() + template.totalDaysToHarvest);
      setHarvestDate(d.toISOString().split('T')[0]);
    }
  };

  const goNext = () => {
    if (currentStep === 'farm') {
      if (!farmId) return Alert.alert('Required', 'Please select a farm');
      if (!cropName.trim()) return Alert.alert('Required', 'Please enter a crop name');
      setCurrentStep('template');
    } else if (currentStep === 'template') {
      setCurrentStep('details');
    } else if (currentStep === 'details') {
      if (!plantingDate.trim()) return Alert.alert('Required', 'Please enter a planting date');
      if (!acreage.trim()) return Alert.alert('Required', 'Please enter acreage');
      // Auto-compute harvest date from template
      if (selectedTemplate && !harvestDate && plantingDate) {
        const d = new Date(plantingDate);
        d.setDate(d.getDate() + selectedTemplate.totalDaysToHarvest);
        setHarvestDate(d.toISOString().split('T')[0]);
      }
      setCurrentStep('review');
    }
  };

  const goBack = () => {
    if (currentStep === 'template') setCurrentStep('farm');
    else if (currentStep === 'details') setCurrentStep('template');
    else if (currentStep === 'review') setCurrentStep('details');
    else router.back();
  };

  const handleCreate = async () => {
    try {
      const planName = `${cropName} - ${SEASON_LABELS[season]} ${year}`;
      updateCreateDraft({
        farmerId: user!.farmerId!,
        farmId,
        templateId: selectedTemplateId || undefined,
        name: planName,
        cropName: cropName.trim(),
        variety: variety.trim() || undefined,
        season: season as any,
        year: parseInt(year),
        plannedPlantingDate: new Date(plantingDate).toISOString(),
        plannedAcreage: parseFloat(acreage),
        expectedHarvestDate: harvestDate ? new Date(harvestDate).toISOString() : undefined,
        notes: notes.trim() || undefined,
        generateActivities,
      });
      const plan = await createPlan();
      router.replace(`/crop-planning/${plan.id}`);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to create plan');
    }
  };

  // ---- Step 1: Farm & Crop ----
  const renderStep1 = () => (
    <View>
      <Text style={styles.label}>Select Farm *</Text>
      <View style={styles.chipRow}>
        {farms.map((f) => (
          <TouchableOpacity
            key={f.id}
            style={[styles.chip, farmId === f.id && styles.chipActive]}
            onPress={() => { setFarmId(f.id); setFarmName(f.name); }}
            testID={`cp-create-farm-${f.id}`}
          >
            <Text style={[styles.chipText, farmId === f.id && styles.chipTextActive]}>{f.name}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Crop Name *</Text>
      <TextInput
        style={styles.input}
        value={cropName}
        onChangeText={setCropName}
        placeholder="e.g. Maize, Beans, Potato"
        testID="cp-create-crop-name"
      />

      <Text style={styles.label}>Season *</Text>
      <View style={styles.chipRow}>
        {Object.entries(SEASONS).map(([key, val]) => (
          <TouchableOpacity
            key={key}
            style={[styles.chip, season === val && styles.chipActive]}
            onPress={() => setSeason(val)}
            testID={`cp-create-season-${val}`}
          >
            <Text style={[styles.chipText, season === val && styles.chipTextActive]}>
              {SEASON_LABELS[val]}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  // ---- Step 2: Template Selection ----
  const renderStep2 = () => (
    <View>
      <Text style={styles.label}>Crop Calendar Template</Text>
      <Text style={styles.helperText}>
        Select a template to auto-generate activities, or skip to create a blank plan.
      </Text>

      {templateLoading ? (
        <ActivityIndicator size="small" color={COLORS.primary} style={{ marginTop: 16 }} />
      ) : templates.length === 0 ? (
        <View style={styles.emptyTemplates}>
          <Text style={styles.emptyTemplatesIcon}>📋</Text>
          <Text style={styles.emptyTemplatesText}>
            No templates found for "{cropName}" ({SEASON_LABELS[season]})
          </Text>
          <Text style={styles.emptyTemplatesSubtext}>
            You can still create a plan without a template
          </Text>
        </View>
      ) : (
        templates.map((t) => (
          <TouchableOpacity
            key={t.id}
            style={[styles.templateCard, selectedTemplateId === t.id && styles.templateCardActive]}
            onPress={() => selectTemplate(t)}
            testID={`cp-create-template-${t.id}`}
          >
            <View style={styles.templateHeader}>
              <Text style={[styles.templateName, selectedTemplateId === t.id && { color: '#fff' }]}>
                {t.cropName}{t.variety ? ` - ${t.variety}` : ''}
              </Text>
              {selectedTemplateId === t.id && (
                <Text style={styles.templateCheck}>✓</Text>
              )}
            </View>
            <Text style={[styles.templateMeta, selectedTemplateId === t.id && { color: 'rgba(255,255,255,0.8)' }]}>
              {SEASON_LABELS[t.season] || t.season} · {t.totalDaysToHarvest} days to harvest
            </Text>
            {t.growthStages && (
              <Text style={[styles.templateStages, selectedTemplateId === t.id && { color: 'rgba(255,255,255,0.7)' }]}>
                {t.growthStages.length} stages · {t.growthStages.reduce((sum, s) => sum + (s.activities?.length || 0), 0)} activities
              </Text>
            )}
            {t.expectedYieldKgPerAcreMin != null && t.expectedYieldKgPerAcreMax != null && (
              <Text style={[styles.templateYield, selectedTemplateId === t.id && { color: 'rgba(255,255,255,0.7)' }]}>
                Expected yield: {t.expectedYieldKgPerAcreMin}-{t.expectedYieldKgPerAcreMax} kg/acre
              </Text>
            )}
          </TouchableOpacity>
        ))
      )}

      {selectedTemplateId && (
        <TouchableOpacity
          style={styles.clearTemplateBtn}
          onPress={() => setSelectedTemplateId(null)}
        >
          <Text style={styles.clearTemplateBtnText}>Clear selection (blank plan)</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  // ---- Step 3: Details ----
  const renderStep3 = () => (
    <View>
      <Text style={styles.label}>Variety</Text>
      <TextInput
        style={styles.input}
        value={variety}
        onChangeText={setVariety}
        placeholder="e.g. H614D, Purple Gold"
        testID="cp-create-variety"
      />

      <Text style={styles.label}>Planting Date * (YYYY-MM-DD)</Text>
      <TextInput
        style={styles.input}
        value={plantingDate}
        onChangeText={(val) => {
          setPlantingDate(val);
          // Auto-compute harvest date
          if (selectedTemplate && val.match(/^\d{4}-\d{2}-\d{2}$/)) {
            const d = new Date(val);
            if (!isNaN(d.getTime())) {
              d.setDate(d.getDate() + selectedTemplate.totalDaysToHarvest);
              setHarvestDate(d.toISOString().split('T')[0]);
            }
          }
        }}
        placeholder="2026-03-15"
        testID="cp-create-planting-date"
      />

      <Text style={styles.label}>Expected Harvest Date (YYYY-MM-DD)</Text>
      <TextInput
        style={styles.input}
        value={harvestDate}
        onChangeText={setHarvestDate}
        placeholder={selectedTemplate ? `Auto: +${selectedTemplate.totalDaysToHarvest} days` : '2026-09-15'}
        testID="cp-create-harvest-date"
      />

      <Text style={styles.label}>Acreage *</Text>
      <TextInput
        style={styles.input}
        value={acreage}
        onChangeText={setAcreage}
        placeholder="e.g. 2.5"
        keyboardType="decimal-pad"
        testID="cp-create-acreage"
      />

      <Text style={styles.label}>Year</Text>
      <TextInput
        style={styles.input}
        value={year}
        onChangeText={setYear}
        keyboardType="number-pad"
        testID="cp-create-year"
      />

      <Text style={styles.label}>Notes</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        value={notes}
        onChangeText={setNotes}
        placeholder="Optional notes..."
        multiline
        numberOfLines={3}
        testID="cp-create-notes"
      />
    </View>
  );

  // ---- Step 4: Review ----
  const renderStep4 = () => (
    <View>
      <View style={styles.reviewCard}>
        <Text style={styles.reviewTitle}>Plan Summary</Text>
        <View style={styles.reviewRow}>
          <Text style={styles.reviewLabel}>Farm</Text>
          <Text style={styles.reviewValue}>{farmName}</Text>
        </View>
        <View style={styles.reviewRow}>
          <Text style={styles.reviewLabel}>Crop</Text>
          <Text style={styles.reviewValue}>{cropName}{variety ? ` (${variety})` : ''}</Text>
        </View>
        <View style={styles.reviewRow}>
          <Text style={styles.reviewLabel}>Season</Text>
          <Text style={styles.reviewValue}>{SEASON_LABELS[season]} {year}</Text>
        </View>
        {selectedTemplate && (
          <View style={styles.reviewRow}>
            <Text style={styles.reviewLabel}>Template</Text>
            <Text style={styles.reviewValue}>
              {selectedTemplate.cropName}{selectedTemplate.variety ? ` - ${selectedTemplate.variety}` : ''}
            </Text>
          </View>
        )}
        <View style={styles.reviewRow}>
          <Text style={styles.reviewLabel}>Planting</Text>
          <Text style={styles.reviewValue}>{plantingDate}</Text>
        </View>
        {harvestDate ? (
          <View style={styles.reviewRow}>
            <Text style={styles.reviewLabel}>Harvest</Text>
            <Text style={styles.reviewValue}>{harvestDate}</Text>
          </View>
        ) : null}
        <View style={styles.reviewRow}>
          <Text style={styles.reviewLabel}>Acreage</Text>
          <Text style={styles.reviewValue}>{acreage} acres</Text>
        </View>
        {notes ? (
          <View style={styles.reviewRow}>
            <Text style={styles.reviewLabel}>Notes</Text>
            <Text style={styles.reviewValue}>{notes}</Text>
          </View>
        ) : null}
      </View>

      {selectedTemplate && (
        <View style={styles.toggleRow}>
          <View style={styles.toggleInfo}>
            <Text style={styles.toggleLabel}>Generate Activities</Text>
            <Text style={styles.toggleDesc}>
              Auto-create {selectedTemplate.growthStages?.reduce((sum, s) => sum + (s.activities?.length || 0), 0) || 0} tasks from template
            </Text>
          </View>
          <Switch
            value={generateActivities}
            onValueChange={setGenerateActivities}
            trackColor={{ true: COLORS.primaryLight }}
            thumbColor={generateActivities ? COLORS.primary : '#ccc'}
            testID="cp-create-gen-activities"
          />
        </View>
      )}

      {!selectedTemplate && (
        <View style={styles.noTemplateInfo}>
          <Text style={styles.noTemplateText}>
            No template selected. You can add activities manually after creating the plan.
          </Text>
        </View>
      )}
    </View>
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      testID="cp-create-screen"
    >
      <StepIndicatorCompact steps={steps} currentStep={currentStep} />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {currentStep === 'farm' && renderStep1()}
        {currentStep === 'template' && renderStep2()}
        {currentStep === 'details' && renderStep3()}
        {currentStep === 'review' && renderStep4()}
      </ScrollView>
      <View style={styles.footer}>
        <TouchableOpacity style={styles.backButton} onPress={goBack} testID="cp-create-back">
          <Text style={styles.backButtonText}>
            {currentStep === 'farm' ? 'Cancel' : 'Back'}
          </Text>
        </TouchableOpacity>
        {currentStep === 'review' ? (
          <TouchableOpacity
            style={[styles.nextButton, isLoading && { opacity: 0.6 }]}
            onPress={handleCreate}
            disabled={isLoading}
            testID="cp-create-submit"
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={styles.nextButtonText}>Create Plan</Text>
            )}
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.nextButton} onPress={goNext} testID="cp-create-next">
            <Text style={styles.nextButtonText}>
              {currentStep === 'template' && !selectedTemplateId ? 'Skip' : 'Next'}
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  content: { padding: 16, paddingBottom: 100 },
  label: { fontSize: 14, fontWeight: '600', color: '#333', marginTop: 16, marginBottom: 6 },
  helperText: { fontSize: 13, color: '#666', marginBottom: 8 },
  input: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  textArea: { minHeight: 80, textAlignVertical: 'top' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  chipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  chipText: { fontSize: 14, color: '#333' },
  chipTextActive: { color: '#fff', fontWeight: '600' },

  // Template cards
  templateCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 2,
    borderColor: '#E0E0E0',
  },
  templateCardActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  templateHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  templateName: { fontSize: 16, fontWeight: '600', color: '#333' },
  templateCheck: { fontSize: 18, color: '#fff', fontWeight: 'bold' },
  templateMeta: { fontSize: 13, color: '#666', marginTop: 4 },
  templateStages: { fontSize: 12, color: '#999', marginTop: 2 },
  templateYield: { fontSize: 12, color: '#999', marginTop: 2 },
  emptyTemplates: { alignItems: 'center', paddingVertical: 32 },
  emptyTemplatesIcon: { fontSize: 36, marginBottom: 8 },
  emptyTemplatesText: { fontSize: 14, color: '#666', textAlign: 'center' },
  emptyTemplatesSubtext: { fontSize: 12, color: '#999', marginTop: 4 },
  clearTemplateBtn: { alignItems: 'center', paddingVertical: 12, marginTop: 4 },
  clearTemplateBtnText: { fontSize: 13, color: COLORS.primary, fontWeight: '500' },

  // Review
  reviewCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
  },
  reviewTitle: { fontSize: 16, fontWeight: '700', color: '#333', marginBottom: 12 },
  reviewRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  reviewLabel: { fontSize: 14, color: '#666' },
  reviewValue: { fontSize: 14, fontWeight: '500', color: '#333', maxWidth: '60%', textAlign: 'right' },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
  },
  toggleInfo: { flex: 1 },
  toggleLabel: { fontSize: 14, fontWeight: '600', color: '#333' },
  toggleDesc: { fontSize: 12, color: '#666', marginTop: 2 },
  noTemplateInfo: {
    backgroundColor: '#FFF8E1',
    borderRadius: 10,
    padding: 14,
    marginTop: 12,
  },
  noTemplateText: { fontSize: 13, color: '#795548' },

  // Footer
  footer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
    gap: 12,
  },
  backButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    alignItems: 'center',
  },
  backButtonText: { fontSize: 16, color: '#666', fontWeight: '500' },
  nextButton: {
    flex: 2,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
  },
  nextButtonText: { fontSize: 16, color: '#fff', fontWeight: '600' },
});
