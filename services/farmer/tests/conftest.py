"""Pytest fixtures for farmer service tests."""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.main import app
from app.models.farmer import Base, Farmer
import app.services.storage_service as storage_module


# Use SQLite for testing (no server required)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Enable foreign key support in SQLite
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()

    # Clean up tables after each test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden database dependency."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_farmer(db_session: AsyncSession) -> Farmer:
    """Create a test farmer."""
    farmer = Farmer(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        first_name="John",
        last_name="Doe",
        phone_number="+254700000000",
        national_id="12345678",
        email="john.doe@example.com",
        county="Nairobi",
        kyc_status="pending",
    )
    db_session.add(farmer)
    await db_session.commit()
    await db_session.refresh(farmer)
    return farmer


@pytest_asyncio.fixture
async def test_farmer_with_bank(db_session: AsyncSession) -> Farmer:
    """Create a test farmer with bank details."""
    farmer = Farmer(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        first_name="Jane",
        last_name="Smith",
        phone_number="+254700000001",
        national_id="87654321",
        email="jane.smith@example.com",
        county="Kiambu",
        kyc_status="pending",
        bank_name="KCB",
        bank_account="1234567890",
        bank_branch="Nairobi",
    )
    db_session.add(farmer)
    await db_session.commit()
    await db_session.refresh(farmer)
    return farmer


class MockStorageService:
    """Mock storage service for testing without S3."""

    async def upload_file(self, file: Any, folder: str, farmer_id: Any, encrypt: bool = True) -> dict:
        """Mock file upload."""
        content = await file.read()
        await file.seek(0)
        return {
            "file_path": f"{folder}/{farmer_id}/test_file.jpg",
            "file_hash": "mockhash123456",
            "file_size": len(content),
            "mime_type": file.content_type or "application/octet-stream",
            "original_name": file.filename,
        }

    async def upload_bytes(
        self, content: bytes, file_path: str, content_type: str = "application/octet-stream", encrypt: bool = True
    ) -> dict:
        """Mock bytes upload."""
        return {
            "file_path": file_path,
            "file_hash": "mockhash123456",
            "file_size": len(content),
        }

    async def download_file(self, file_path: str) -> bytes:
        """Mock file download."""
        return b"mock file content"

    async def get_presigned_url(self, file_path: str, expiration_minutes: int = 60, for_upload: bool = False) -> str:
        """Mock presigned URL generation."""
        return f"https://mock-s3.example.com/{file_path}?signed=true"

    async def delete_file(self, file_path: str) -> bool:
        """Mock file deletion."""
        return True

    async def file_exists(self, file_path: str) -> bool:
        """Mock file existence check."""
        return True


@pytest.fixture(autouse=True)
def mock_storage_service():
    """Mock the storage service singleton for all tests."""
    mock_service = MockStorageService()
    original_service = storage_module._storage_service
    storage_module._storage_service = mock_service
    yield mock_service
    storage_module._storage_service = original_service
