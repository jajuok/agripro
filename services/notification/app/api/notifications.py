"""Notification CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.notification import (
    NotificationBulkCreate,
    NotificationCreate,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    user_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    items, total, unread_count = await svc.list_notifications(
        user_id=user_id, page=page, page_size=page_size, unread_only=unread_only
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    count = await svc.get_unread_count(user_id)
    return UnreadCountResponse(unread_count=count)


@router.post("/", response_model=NotificationResponse, status_code=201)
async def create_notification(
    payload: NotificationCreate,
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    notification = await svc.create_notification(
        user_id=payload.user_id,
        title=payload.title,
        body=payload.body,
        notification_type=payload.notification_type,
        priority=payload.priority,
        data=payload.data,
        template_code=payload.template_code,
        template_variables=payload.template_variables,
        channels=payload.channels,
    )
    return NotificationResponse.model_validate(notification)


@router.post("/bulk", response_model=list[NotificationResponse], status_code=201)
async def create_bulk_notifications(
    payload: NotificationBulkCreate,
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    notifications = []
    for uid in payload.user_ids:
        n = await svc.create_notification(
            user_id=uid,
            title=payload.title,
            body=payload.body,
            notification_type=payload.notification_type,
            priority=payload.priority,
            data=payload.data,
            template_code=payload.template_code,
            template_variables=payload.template_variables,
            channels=payload.channels,
        )
        notifications.append(NotificationResponse.model_validate(n))
    return notifications


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: UUID,
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    notification = await svc.mark_as_read(notification_id, user_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse.model_validate(notification)


@router.post("/mark-all-read")
async def mark_all_as_read(
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    count = await svc.mark_all_as_read(user_id)
    return {"marked_count": count}
