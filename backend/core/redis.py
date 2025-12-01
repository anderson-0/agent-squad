"""
Redis client module for caching.

Provides async Redis client for caching user data, squad data, and more.
"""
import logging
from typing import Optional

import redis.asyncio as redis

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Get or create Redis client instance.

    Returns:
        redis.Redis: Async Redis client instance

    Raises:
        redis.ConnectionError: If unable to connect to Redis
    """
    global redis_client

    if settings.ENV == "test" or not settings.CACHE_ENABLED:
        from unittest.mock import AsyncMock
        mock = AsyncMock()
        mock.ping.return_value = True
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.exists.return_value = 0
        mock.close.return_value = None
        return mock

    if redis_client is None:
        try:
            logger.info(f"Connecting to Redis at {settings.REDIS_URL}")

            redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            await redis_client.ping()
            logger.info("Redis connection established successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            redis_client = None
            raise

    return redis_client


async def close_redis() -> None:
    """
    Close Redis connection.

    Called during application shutdown.
    """
    global redis_client

    if redis_client:
        try:
            await redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        finally:
            redis_client = None


async def get_redis_health() -> dict:
    """
    Check Redis health status.

    Returns:
        dict: Health status information
    """
    try:
        client = await get_redis()
        await client.ping()

        # Get server info
        info = await client.info("server")

        return {
            "status": "healthy",
            "redis_version": info.get("redis_version", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
