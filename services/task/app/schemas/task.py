"""Task schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class TaskCreate(BaseModel):
    farmer_id: UUID
    farm_id: UUID | None = None
    title: str = Field(max_length=300)
    description: str | None = None
    category: str = "general"
    priority: int = Field(default=5, ge=1, le=10)
    due_date: datetime | None = None
    assigned_to: str | None = None
    notes: str | None = None
    recurrence: str = "none"


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    description: str | None = None
    category: str | None = None
    priority: int | None = Field(default=None, ge=1, le=10)
    status: str | None = None
    due_date: datetime | None = None
    assigned_to: str | None = None
    notes: str | None = None
    recurrence: str | None = None
    farm_id: UUID | None = None


class TaskComplete(BaseModel):
    notes: str | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farmer_id: UUID
    farm_id: UUID | None = None
    title: str
    description: str | None = None
    category: str
    priority: int
    status: str
    due_date: datetime | None = None
    completed_at: datetime | None = None
    assigned_to: str | None = None
    notes: str | None = None
    recurrence: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    comments: list["TaskCommentResponse"] = []


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


class TaskCommentCreate(BaseModel):
    content: str
    author_id: UUID


class TaskCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    content: str
    author_id: UUID
    created_at: datetime


class TaskCommentListResponse(BaseModel):
    items: list[TaskCommentResponse]
    total: int


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TaskStats(BaseModel):
    total: int = 0
    pending: int = 0
    in_progress: int = 0
    completed: int = 0
    cancelled: int = 0
    overdue: int = 0
