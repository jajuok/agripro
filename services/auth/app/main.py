"""Main application entry point for Auth Service."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.middleware.tenant import TenantMiddleware

# Import all models to ensure they're registered with Base.metadata
import app.models.user  # noqa: F401
import app.models.audit  # noqa: F401
import app.models.login_attempt  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    configure_logging()

    # Initialize database schema
    from app.core.database import engine, Base
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info("Creating database tables if they don't exist...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ready")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

    yield
    # Cleanup resources
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AgriScheme Pro - Auth Service",
        description="Authentication and Authorization Service",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add multi-tenancy middleware
    app.add_middleware(TenantMiddleware)

    # Include routers
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "healthy", "service": "auth"}

    return app


app = create_app()
