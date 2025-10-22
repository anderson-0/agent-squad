"""
Test configuration and fixtures
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from backend.core.app import app
from backend.core.database import get_db
from backend.models.base import Base


# Test database URL - use postgres hostname when running in Docker
import os
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/agent_squad_test"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

# Create test session maker
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database for each test function.
    """
    # Create all tables (skip drop since tables exist from migrations)
    async with test_engine.begin() as conn:
        # Only create tables that don't exist yet
        # Note: This assumes migrations have been run
        # If tables already exist, this will silently continue
        try:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        except Exception:
            # Tables may already exist from migrations
            pass

    # Create session
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # Clean up test data after each test
            await session.rollback()
            # Delete all data from test tables in correct order (respecting foreign keys)
            try:
                from sqlalchemy import text
                # Order matters due to foreign key constraints
                await session.execute(text("DELETE FROM conversation_events"))
                await session.execute(text("DELETE FROM agent_conversations"))
                await session.execute(text("DELETE FROM routing_rules"))
                await session.execute(text("DELETE FROM default_routing_templates"))
                await session.execute(text("DELETE FROM agent_messages"))
                await session.execute(text("DELETE FROM task_executions"))
                await session.execute(text("DELETE FROM tasks"))
                await session.execute(text("DELETE FROM projects"))
                await session.execute(text("DELETE FROM squad_members"))
                await session.execute(text("DELETE FROM squads"))
                await session.execute(text("DELETE FROM organizations"))
                await session.execute(text("DELETE FROM users"))
                await session.commit()
            except Exception:
                # Tables may not exist yet or other errors
                await session.rollback()


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override get_db dependency for tests"""
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client
    """
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpass123"
    }


@pytest.fixture
def test_user_data_2():
    """Second test user data"""
    return {
        "email": "test2@example.com",
        "name": "Test User 2",
        "password": "testpass456"
    }
