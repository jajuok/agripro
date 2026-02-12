// Task types (camelCase)

export interface Task {
  id: string;
  farmerId: string;
  farmId: string | null;
  title: string;
  description: string | null;
  category: string;
  priority: number;
  status: string;
  dueDate: string | null;
  completedAt: string | null;
  assignedTo: string | null;
  notes: string | null;
  recurrence: string;
  isDeleted: boolean;
  createdAt: string;
  updatedAt: string;
  comments: TaskComment[];
}

export interface TaskComment {
  id: string;
  taskId: string;
  content: string;
  authorId: string;
  createdAt: string;
}

export interface TaskStats {
  total: number;
  pending: number;
  inProgress: number;
  completed: number;
  cancelled: number;
  overdue: number;
}

export interface TaskCreateData {
  farmerId: string;
  farmId?: string | null;
  title: string;
  description?: string | null;
  category?: string;
  priority?: number;
  dueDate?: string | null;
  assignedTo?: string | null;
  notes?: string | null;
  recurrence?: string;
}

export interface TaskUpdateData {
  title?: string;
  description?: string | null;
  category?: string;
  priority?: number;
  status?: string;
  dueDate?: string | null;
  assignedTo?: string | null;
  notes?: string | null;
  recurrence?: string;
  farmId?: string | null;
}
