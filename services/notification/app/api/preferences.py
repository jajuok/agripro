"""Notification preferences endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.notification import (
    PreferenceResponse,
    PreferenceUpdate,
    PushSubscription,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/preferences")


@router.get("", response_model=PreferenceResponse)
async def get_preferences(
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    pref = await svc.get_preferences(user_id)
    if pref is None:
        # Return default preferences by creating them
        pref = await svc.upsert_preferences(user_id, {})
    return PreferenceResponse.model_validate(pref)


@router.put("", response_model=PreferenceResponse)
async def update_preferences(
    payload: PreferenceUpdate,
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    updates = payload.model_dump(exclude_none=True)
    pref = await svc.upsert_preferences(user_id, updates)
    return PreferenceResponse.model_validate(pref)


@router.post("/push-subscription", response_model=PreferenceResponse)
async def save_push_subscription(
    payload: PushSubscription,
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    pref = await svc.save_push_subscription(
        user_id, {"endpoint": payload.endpoint, "keys": payload.keys}
    )
    return PreferenceResponse.model_validate(pref)
