"""
Database Connection and Session Management with SQLAlchemy (Async)

Uses asyncpg for better performance with async operations.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from backend.core.config import settings
from backend.models.base import Base


# ============================================================================
# ASYNC DATABASE (Primary - Uses asyncpg)
# ============================================================================

# Create async engine with asyncpg
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Create async sessionmaker
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database - create all tables (async)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database connected and tables created (async)")


async def close_db() -> None:
    """Close database connections (async)"""
    await async_engine.dispose()
    print("✅ Database disconnected (async)")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency for FastAPI to get database session

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            users = result.scalars().all()
            return users
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database session

    Usage:
        async with get_db_context() as db:
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalar_one_or_none()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================================================
# SYNC DATABASE (For compatibility with sync code)
# ============================================================================

# Create sync engine (for migrations and sync operations)
sync_engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,
)

# Create sync sessionmaker
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


def get_sync_db() -> Generator[Session, None, None]:
    """
    Sync dependency for FastAPI (use only when async is not possible)

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_sync_db)):
            users = db.query(User).all()
            return users
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_sync_db_context() -> Generator[Session, None, None]:
    """
    Sync context manager for database session

    Usage:
        with get_sync_db_context() as db:
            user = db.query(User).filter(User.email == email).first()
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def init_sync_db() -> None:
    """Initialize database synchronously (for migrations/scripts)"""
    Base.metadata.create_all(bind=sync_engine)
    print("✅ Database tables created (sync)")


def close_sync_db() -> None:
    """Close sync database connections"""
    sync_engine.dispose()
    print("✅ Database disconnected (sync)")
