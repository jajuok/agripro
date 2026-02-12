"""Task service layer."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskComment


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def create_task(self, data: dict) -> Task:
        task = Task(**data)
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task, attribute_names=["comments"])
        return task

    async def get_task(self, task_id: UUID) -> Task | None:
        stmt = (
            select(Task)
            .options(selectinload(Task.comments))
            .where(Task.id == task_id, Task.is_deleted == False)  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        farmer_id: UUID,
        status: str | None = None,
        category: str | None = None,
        priority_min: int | None = None,
        priority_max: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        base = select(Task).where(
            Task.farmer_id == farmer_id,
            Task.is_deleted == False,  # noqa: E712
        )

        if status:
            base = base.where(Task.status == status)
        if category:
            base = base.where(Task.category == category)
        if priority_min is not None:
            base = base.where(Task.priority >= priority_min)
        if priority_max is not None:
            base = base.where(Task.priority <= priority_max)

        # Count
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Fetch
        stmt = (
            base.options(selectinload(Task.comments))
            .order_by(
                Task.due_date.asc().nulls_last(),
                Task.priority.asc(),
                Task.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def update_task(self, task_id: UUID, data: dict) -> Task | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        data["updated_at"] = datetime.now(timezone.utc)
        for key, value in data.items():
            setattr(task, key, value)
        await self.db.flush()
        await self.db.refresh(task, attribute_names=["comments"])
        return task

    async def complete_task(self, task_id: UUID, notes: str | None = None) -> Task | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        if notes:
            task.notes = notes
        await self.db.flush()
        await self.db.refresh(task, attribute_names=["comments"])
        return task

    async def soft_delete_task(self, task_id: UUID) -> bool:
        task = await self.get_task(task_id)
        if not task:
            return False
        task.is_deleted = True
        task.status = "cancelled"
        task.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    async def add_comment(self, task_id: UUID, data: dict) -> TaskComment | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        comment = TaskComment(task_id=task_id, **data)
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def list_comments(self, task_id: UUID) -> list[TaskComment]:
        stmt = (
            select(TaskComment)
            .where(TaskComment.task_id == task_id)
            .order_by(TaskComment.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_stats(self, farmer_id: UUID) -> dict:
        base = select(Task).where(
            Task.farmer_id == farmer_id,
            Task.is_deleted == False,  # noqa: E712
        )

        total_q = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(total_q)).scalar() or 0

        async def count_status(status: str) -> int:
            q = select(func.count()).select_from(
                base.where(Task.status == status).subquery()
            )
            return (await self.db.execute(q)).scalar() or 0

        pending = await count_status("pending")
        in_progress = await count_status("in_progress")
        completed = await count_status("completed")
        cancelled = await count_status("cancelled")

        # Overdue: pending or in_progress with due_date in the past
        now = datetime.now(timezone.utc)
        overdue_q = select(func.count()).select_from(
            base.where(
                Task.status.in_(["pending", "in_progress"]),
                Task.due_date < now,
                Task.due_date.is_not(None),
            ).subquery()
        )
        overdue = (await self.db.execute(overdue_q)).scalar() or 0

        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "cancelled": cancelled,
            "overdue": overdue,
        }
