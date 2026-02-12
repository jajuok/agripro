"""Task API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.task import (
    TaskCommentCreate,
    TaskCommentListResponse,
    TaskCommentResponse,
    TaskComplete,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStats,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    return TaskService(db)


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    farmer_id: UUID = Query(...),
    status: str | None = Query(None),
    category: str | None = Query(None),
    priority_min: int | None = Query(None, ge=1, le=10),
    priority_max: int | None = Query(None, ge=1, le=10),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svc: TaskService = Depends(get_service),
):
    items, total = await svc.list_tasks(
        farmer_id=farmer_id,
        status=status,
        category=category,
        priority_min=priority_min,
        priority_max=priority_max,
        limit=limit,
        offset=offset,
    )
    return TaskListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    body: TaskCreate,
    svc: TaskService = Depends(get_service),
):
    task = await svc.create_task(body.model_dump())
    return task


@router.get("/stats", response_model=TaskStats)
async def get_stats(
    farmer_id: UUID = Query(...),
    svc: TaskService = Depends(get_service),
):
    return await svc.get_stats(farmer_id)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    svc: TaskService = Depends(get_service),
):
    task = await svc.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    body: TaskUpdate,
    svc: TaskService = Depends(get_service),
):
    task = await svc.update_task(task_id, body.model_dump(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    svc: TaskService = Depends(get_service),
):
    deleted = await svc.soft_delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    body: TaskComplete | None = None,
    svc: TaskService = Depends(get_service),
):
    task = await svc.complete_task(task_id, notes=body.notes if body else None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}/comments", response_model=TaskCommentListResponse)
async def list_comments(
    task_id: UUID,
    svc: TaskService = Depends(get_service),
):
    comments = await svc.list_comments(task_id)
    return TaskCommentListResponse(items=comments, total=len(comments))


@router.post("/{task_id}/comments", response_model=TaskCommentResponse, status_code=201)
async def add_comment(
    task_id: UUID,
    body: TaskCommentCreate,
    svc: TaskService = Depends(get_service),
):
    comment = await svc.add_comment(task_id, body.model_dump())
    if not comment:
        raise HTTPException(status_code=404, detail="Task not found")
    return comment
