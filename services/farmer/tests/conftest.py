"""Pytest fixtures for farmer service tests."""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.main import app
from app.models.farmer import Base, Farmer


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
