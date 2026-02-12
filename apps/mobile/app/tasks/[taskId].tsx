import { useCallback, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Alert, TextInput, KeyboardAvoidingView, Platform,
} from 'react-native';
import { router, useLocalSearchParams, useFocusEffect } from 'expo-router';
import { useTaskStore } from '@/store/task';
import { useAuthStore } from '@/store/auth';
import {
  TASK_CATEGORY_LABELS, TASK_CATEGORY_ICONS, TASK_STATUS_COLORS, COLORS,
} from '@/utils/constants';

const priorityLabels: Record<string, string> = {
  '1': 'Critical', '2': 'Very High', '3': 'High',
  '4': 'Medium-High', '5': 'Medium', '6': 'Medium-Low',
  '7': 'Low', '8': 'Low', '9': 'Very Low', '10': 'Minimal',
};

export default function TaskDetailScreen() {
  const { taskId } = useLocalSearchParams<{ taskId: string }>();
  const user = useAuthStore((s) => s.user);
  const {
    selectedTask, fetchTask, completeTask, deleteTask,
    comments, fetchComments, addComment, isLoading,
  } = useTaskStore();
  const [commentText, setCommentText] = useState('');

  useFocusEffect(
    useCallback(() => {
      if (taskId) {
        fetchTask(taskId);
        fetchComments(taskId);
      }
    }, [taskId])
  );

  const handleComplete = () => {
    Alert.alert('Complete Task', 'Mark this task as completed?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Complete',
        onPress: async () => {
          await completeTask(taskId!);
          router.back();
        },
      },
    ]);
  };

  const handleDelete = () => {
    Alert.alert('Delete Task', 'Are you sure you want to delete this task?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          await deleteTask(taskId!);
          router.back();
        },
      },
    ]);
  };

  const handleAddComment = async () => {
    if (!commentText.trim() || !user?.id) return;
    await addComment(taskId!, commentText.trim(), user.id);
    setCommentText('');
  };

  if (isLoading && !selectedTask) {
    return (
      <View style={styles.loader}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (!selectedTask) {
    return (
      <View style={styles.loader}>
        <Text>Task not found</Text>
      </View>
    );
  }

  const task = selectedTask;
  const icon = TASK_CATEGORY_ICONS[task.category] || '📌';
  const statusColor = TASK_STATUS_COLORS[task.status] || '#999';
  const isCompleted = task.status === 'completed' || task.status === 'cancelled';

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={{ fontSize: 36 }}>{icon}</Text>
          <View style={[styles.statusBadge, { backgroundColor: statusColor + '20' }]}>
            <Text style={[styles.statusBadgeText, { color: statusColor }]}>
              {task.status.replace('_', ' ')}
            </Text>
          </View>
        </View>

        <Text style={styles.title}>{task.title}</Text>

        {task.description ? (
          <Text style={styles.description}>{task.description}</Text>
        ) : null}

        {/* Details */}
        <View style={styles.detailsCard}>
          <DetailRow label="Category" value={TASK_CATEGORY_LABELS[task.category] || task.category} />
          <DetailRow label="Priority" value={priorityLabels[String(task.priority)] || `${task.priority}/10`} />
          {task.dueDate ? (
            <DetailRow label="Due Date" value={new Date(task.dueDate).toLocaleDateString()} />
          ) : null}
          {task.completedAt ? (
            <DetailRow label="Completed" value={new Date(task.completedAt).toLocaleDateString()} />
          ) : null}
          {task.assignedTo ? <DetailRow label="Assigned To" value={task.assignedTo} /> : null}
          {task.recurrence !== 'none' ? <DetailRow label="Recurrence" value={task.recurrence} /> : null}
        </View>

        {task.notes ? (
          <View style={styles.notesCard}>
            <Text style={styles.notesLabel}>Notes</Text>
            <Text style={styles.notesText}>{task.notes}</Text>
          </View>
        ) : null}

        {/* Actions */}
        {!isCompleted && (
          <View style={styles.actions}>
            <TouchableOpacity style={styles.completeBtn} onPress={handleComplete}>
              <Text style={styles.completeBtnText}>Mark Complete</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.deleteBtn} onPress={handleDelete}>
              <Text style={styles.deleteBtnText}>Delete</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Comments */}
        <View style={styles.commentsSection}>
          <Text style={styles.commentsTitle}>Comments ({comments.length})</Text>
          {comments.map((c) => (
            <View key={c.id} style={styles.commentCard}>
              <Text style={styles.commentText}>{c.content}</Text>
              <Text style={styles.commentDate}>{new Date(c.createdAt).toLocaleString()}</Text>
            </View>
          ))}
          <View style={styles.commentInput}>
            <TextInput
              style={styles.commentTextInput}
              placeholder="Add a comment..."
              value={commentText}
              onChangeText={setCommentText}
              multiline
            />
            <TouchableOpacity style={styles.commentSendBtn} onPress={handleAddComment}>
              <Text style={styles.commentSendText}>Send</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  content: { padding: 16, paddingBottom: 40 },
  loader: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  statusBadge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  statusBadgeText: { fontSize: 13, fontWeight: '600', textTransform: 'capitalize' },
  title: { fontSize: 22, fontWeight: '700', color: '#333', marginBottom: 8 },
  description: { fontSize: 15, color: '#555', lineHeight: 22, marginBottom: 16 },
  detailsCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12 },
  detailRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: '#eee' },
  detailLabel: { fontSize: 14, color: '#666' },
  detailValue: { fontSize: 14, fontWeight: '500', color: '#333' },
  notesCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12 },
  notesLabel: { fontSize: 14, fontWeight: '600', color: '#333', marginBottom: 4 },
  notesText: { fontSize: 14, color: '#555', lineHeight: 20 },
  actions: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  completeBtn: { flex: 1, backgroundColor: '#4CAF50', borderRadius: 10, padding: 14, alignItems: 'center' },
  completeBtnText: { color: '#fff', fontWeight: '600', fontSize: 15 },
  deleteBtn: { backgroundColor: '#fff', borderRadius: 10, padding: 14, alignItems: 'center', borderWidth: 1, borderColor: '#D32F2F' },
  deleteBtnText: { color: '#D32F2F', fontWeight: '600', fontSize: 15 },
  commentsSection: { marginTop: 8 },
  commentsTitle: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 8 },
  commentCard: { backgroundColor: '#fff', borderRadius: 10, padding: 12, marginBottom: 8 },
  commentText: { fontSize: 14, color: '#333' },
  commentDate: { fontSize: 11, color: '#999', marginTop: 4 },
  commentInput: { flexDirection: 'row', alignItems: 'flex-end', marginTop: 4, gap: 8 },
  commentTextInput: { flex: 1, backgroundColor: '#fff', borderRadius: 10, padding: 12, fontSize: 14, maxHeight: 80, borderWidth: 1, borderColor: '#ddd' },
  commentSendBtn: { backgroundColor: '#1B5E20', borderRadius: 10, paddingHorizontal: 16, paddingVertical: 12 },
  commentSendText: { color: '#fff', fontWeight: '600' },
});
