"""Task Service Main Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title="Task Service",
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)

    @application.get("/")
    async def root():
        return {"service": "task-service", "status": "operational"}

    @application.get("/health")
    async def health():
        return {"status": "healthy"}

    return application


app = create_app()
