"""
Database connection and session management
"""
from prisma import Prisma
from backend.core.config import settings

# Global Prisma client instance
db = Prisma(
    datasource={"url": settings.DATABASE_URL}
)


async def init_db():
    """Initialize database connection"""
    await db.connect()
    print("✅ Database connected")


async def close_db():
    """Close database connection"""
    await db.disconnect()
    print("✅ Database disconnected")


async def get_db() -> Prisma:
    """Dependency for getting database session"""
    return db
