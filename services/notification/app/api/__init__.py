"""API routes aggregation."""

from fastapi import APIRouter

from app.api.notifications import router as notifications_router
from app.api.preferences import router as preferences_router

router = APIRouter(prefix="/notifications")
router.include_router(notifications_router)
router.include_router(preferences_router)
