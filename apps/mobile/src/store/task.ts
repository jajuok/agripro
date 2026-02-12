import { create } from 'zustand';
import { taskApi } from '@/services/api';
import type { Task, TaskComment, TaskStats, TaskCreateData, TaskUpdateData } from '@/types/task';

// =============================================================================
// snake_case API -> camelCase TS mappers
// =============================================================================

const mapComment = (d: any): TaskComment => ({
  id: d.id,
  taskId: d.task_id,
  content: d.content,
  authorId: d.author_id,
  createdAt: d.created_at,
});

const mapTask = (d: any): Task => ({
  id: d.id,
  farmerId: d.farmer_id,
  farmId: d.farm_id ?? null,
  title: d.title,
  description: d.description ?? null,
  category: d.category,
  priority: d.priority,
  status: d.status,
  dueDate: d.due_date ?? null,
  completedAt: d.completed_at ?? null,
  assignedTo: d.assigned_to ?? null,
  notes: d.notes ?? null,
  recurrence: d.recurrence,
  isDeleted: d.is_deleted ?? false,
  createdAt: d.created_at,
  updatedAt: d.updated_at,
  comments: (d.comments || []).map(mapComment),
});

const mapStats = (d: any): TaskStats => ({
  total: d.total ?? 0,
  pending: d.pending ?? 0,
  inProgress: d.in_progress ?? 0,
  completed: d.completed ?? 0,
  cancelled: d.cancelled ?? 0,
  overdue: d.overdue ?? 0,
});

// camelCase -> snake_case for API
const toSnake = (data: TaskCreateData): Record<string, any> => ({
  farmer_id: data.farmerId,
  farm_id: data.farmId ?? null,
  title: data.title,
  description: data.description ?? null,
  category: data.category ?? 'general',
  priority: data.priority ?? 5,
  due_date: data.dueDate ?? null,
  assigned_to: data.assignedTo ?? null,
  notes: data.notes ?? null,
  recurrence: data.recurrence ?? 'none',
});

const updateToSnake = (data: TaskUpdateData): Record<string, any> => {
  const out: Record<string, any> = {};
  if (data.title !== undefined) out.title = data.title;
  if (data.description !== undefined) out.description = data.description;
  if (data.category !== undefined) out.category = data.category;
  if (data.priority !== undefined) out.priority = data.priority;
  if (data.status !== undefined) out.status = data.status;
  if (data.dueDate !== undefined) out.due_date = data.dueDate;
  if (data.assignedTo !== undefined) out.assigned_to = data.assignedTo;
  if (data.notes !== undefined) out.notes = data.notes;
  if (data.recurrence !== undefined) out.recurrence = data.recurrence;
  if (data.farmId !== undefined) out.farm_id = data.farmId;
  return out;
};

// =============================================================================
// Store Type
// =============================================================================

type TaskState = {
  tasks: Task[];
  selectedTask: Task | null;
  stats: TaskStats | null;
  comments: TaskComment[];
  total: number;
  isLoading: boolean;
  error: string | null;

  fetchTasks: (farmerId: string, params?: { status?: string; category?: string; limit?: number; offset?: number }) => Promise<void>;
  createTask: (data: TaskCreateData) => Promise<Task>;
  fetchTask: (taskId: string) => Promise<void>;
  updateTask: (taskId: string, data: TaskUpdateData) => Promise<void>;
  deleteTask: (taskId: string) => Promise<void>;
  completeTask: (taskId: string, notes?: string) => Promise<void>;
  fetchComments: (taskId: string) => Promise<void>;
  addComment: (taskId: string, content: string, authorId: string) => Promise<void>;
  fetchStats: (farmerId: string) => Promise<void>;
  clearError: () => void;
};

// =============================================================================
// Store
// =============================================================================

export const useTaskStore = create<TaskState>()((set, get) => ({
  tasks: [],
  selectedTask: null,
  stats: null,
  comments: [],
  total: 0,
  isLoading: false,
  error: null,

  fetchTasks: async (farmerId, params) => {
    set({ isLoading: true, error: null });
    try {
      const response = await taskApi.list(farmerId, params);
      const tasks = (response.items || []).map(mapTask);
      set({ tasks, total: response.total ?? 0, isLoading: false });
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch tasks', isLoading: false });
      throw error;
    }
  },

  createTask: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await taskApi.create(toSnake(data));
      const task = mapTask(response);
      set((state) => ({ tasks: [task, ...state.tasks], isLoading: false }));
      return task;
    } catch (error: any) {
      set({ error: error.message || 'Failed to create task', isLoading: false });
      throw error;
    }
  },

  fetchTask: async (taskId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await taskApi.get(taskId);
      set({ selectedTask: mapTask(response), isLoading: false });
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch task', isLoading: false });
      throw error;
    }
  },

  updateTask: async (taskId, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await taskApi.update(taskId, updateToSnake(data));
      const updated = mapTask(response);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === taskId ? updated : t)),
        selectedTask: state.selectedTask?.id === taskId ? updated : state.selectedTask,
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message || 'Failed to update task', isLoading: false });
      throw error;
    }
  },

  deleteTask: async (taskId) => {
    set({ isLoading: true, error: null });
    try {
      await taskApi.delete(taskId);
      set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== taskId),
        selectedTask: state.selectedTask?.id === taskId ? null : state.selectedTask,
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message || 'Failed to delete task', isLoading: false });
      throw error;
    }
  },

  completeTask: async (taskId, notes) => {
    set({ isLoading: true, error: null });
    try {
      const response = await taskApi.complete(taskId, notes);
      const updated = mapTask(response);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === taskId ? updated : t)),
        selectedTask: state.selectedTask?.id === taskId ? updated : state.selectedTask,
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message || 'Failed to complete task', isLoading: false });
      throw error;
    }
  },

  fetchComments: async (taskId) => {
    try {
      const response = await taskApi.listComments(taskId);
      const comments = (response.items || []).map(mapComment);
      set({ comments });
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch comments' });
    }
  },

  addComment: async (taskId, content, authorId) => {
    try {
      const response = await taskApi.addComment(taskId, { content, author_id: authorId });
      const comment = mapComment(response);
      set((state) => ({ comments: [...state.comments, comment] }));
    } catch (error: any) {
      set({ error: error.message || 'Failed to add comment' });
    }
  },

  fetchStats: async (farmerId) => {
    try {
      const response = await taskApi.getStats(farmerId);
      set({ stats: mapStats(response) });
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch stats' });
    }
  },

  clearError: () => set({ error: null }),
}));
