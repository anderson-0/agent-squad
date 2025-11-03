"""
Response Caching Service with Redis

Provides intelligent caching for API responses, database queries, and LLM outputs.
"""
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import asyncio
from datetime import timedelta

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from backend.core.config import settings


class CacheService:
    """
    Centralized caching service with Redis backend

    Features:
    - Async Redis operations
    - Automatic serialization/deserialization
    - TTL (time-to-live) support
    - Cache key generation
    - Fallback to no-cache if Redis unavailable
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._enabled = REDIS_AVAILABLE and settings.REDIS_URL

    async def connect(self):
        """Initialize Redis connection"""
        if not self._enabled:
            print("⚠️ Redis caching disabled (Redis not available or not configured)")
            return

        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            # Test connection
            await self.redis_client.ping()
            print("✅ Redis cache connected")
        except Exception as e:
            print(f"⚠️ Redis connection failed, caching disabled: {e}")
            self.redis_client = None
            self._enabled = False

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            print("✅ Redis cache disconnected")

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and parameters

        Example:
            _generate_key("api", "user", user_id=123) -> "api:user:hash"
        """
        # Create deterministic hash from arguments
        key_data = f"{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:8]
        return f"{prefix}:{key_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._enabled or not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        """
        if not self._enabled or not self.redis_client:
            return False

        try:
            serialized = json.dumps(value)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                await self.redis_client.set(key, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._enabled or not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern

        Example:
            clear_pattern("api:user:*")  # Clear all user API caches
        """
        if not self._enabled or not self.redis_client:
            return 0

        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._enabled or not self.redis_client:
            return False

        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False


# Global cache instance
_cache_service: Optional[CacheService] = None


async def get_cache() -> CacheService:
    """Get cache service instance (singleton)"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service.connect()
    return _cache_service


async def close_cache():
    """Close cache service"""
    global _cache_service
    if _cache_service:
        await _cache_service.disconnect()
        _cache_service = None


# ============================================================================
# CACHE DECORATORS
# ============================================================================

def cached(
    prefix: str,
    ttl: int = 300,
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results

    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds (default: 5 minutes)
        key_func: Optional function to generate cache key from args

    Example:
        @cached("user_profile", ttl=600)
        async def get_user_profile(user_id: int):
            # Expensive database query
            return await db.execute(...)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = await get_cache()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._generate_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


# ============================================================================
# COMMON CACHE STRATEGIES
# ============================================================================

class CacheStrategy:
    """Pre-defined caching strategies for common use cases"""

    # API Response Caching
    API_SHORT = 60        # 1 minute - Frequently changing data
    API_MEDIUM = 300      # 5 minutes - Standard API responses
    API_LONG = 3600       # 1 hour - Rarely changing data

    # Database Query Caching
    DB_HOT = 30           # 30 seconds - Hot data (active sessions)
    DB_WARM = 300         # 5 minutes - Warm data (user profiles)
    DB_COLD = 3600        # 1 hour - Cold data (settings, configs)

    # LLM Response Caching
    LLM_SHORT = 1800      # 30 minutes - User-specific responses
    LLM_LONG = 86400      # 24 hours - Generic/reusable responses

    # Static Content
    STATIC = 604800       # 7 days - Static content (rarely changes)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Cache API endpoint response

    from backend.services.cache_service import cached, CacheStrategy

    @router.get("/users/{user_id}")
    @cached("api:user", ttl=CacheStrategy.API_MEDIUM)
    async def get_user(user_id: int):
        return await db.query(User).filter(User.id == user_id).first()


Example 2: Cache database query

    from backend.services.cache_service import cached, CacheStrategy

    @cached("db:squad_members", ttl=CacheStrategy.DB_WARM)
    async def get_squad_members(squad_id: str):
        result = await db.execute(
            select(SquadMember).filter(SquadMember.squad_id == squad_id)
        )
        return result.scalars().all()


Example 3: Cache LLM response with custom key

    from backend.services.cache_service import cached, CacheStrategy

    def llm_cache_key(prompt: str, model: str):
        # Create hash of prompt for cache key
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        return f"llm:{model}:{prompt_hash}"

    @cached("llm", ttl=CacheStrategy.LLM_LONG, key_func=llm_cache_key)
    async def call_llm(prompt: str, model: str):
        response = await openai.chat.completions.create(...)
        return response


Example 4: Manual cache operations

    from backend.services.cache_service import get_cache

    cache = await get_cache()

    # Set value
    await cache.set("my_key", {"data": "value"}, ttl=300)

    # Get value
    value = await cache.get("my_key")

    # Delete value
    await cache.delete("my_key")

    # Clear pattern
    await cache.clear_pattern("api:user:*")


Example 5: Application lifecycle

    from backend.services.cache_service import get_cache, close_cache

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        cache = await get_cache()  # Initialize cache
        yield
        # Shutdown
        await close_cache()  # Clean up
"""
