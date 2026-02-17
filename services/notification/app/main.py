"""Notification Service Main Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import async_session_maker
from app.services.seed_templates import seed_templates

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed default templates on startup."""
    logger.info("Notification service starting up")
    try:
        async with async_session_maker() as session:
            await seed_templates(session)
    except Exception as e:
        logger.warning("Template seeding skipped: %s", e)
    yield
    logger.info("Notification service shutting down")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Notification Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/")
    async def root():
        return {"service": "notification-service", "status": "operational"}

    @application.get("/health")
    async def health():
        return {"status": "healthy"}

    from app.api import router

    application.include_router(router, prefix="/api/v1")

    return application


app = create_app()
