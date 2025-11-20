"""
Response Caching Service with Redis

Provides intelligent caching for API responses, database queries, and LLM outputs.
Integrates with centralized Redis client from backend.core.redis.
"""
import json
import hashlib
from typing import Any, Optional, Callable, Dict
from functools import wraps
import asyncio
from datetime import timedelta
from collections import defaultdict

from backend.core.redis import get_redis
from backend.core.config import settings


class CacheService:
    """
    Centralized caching service with Redis backend

    Uses the centralized Redis client from backend.core.redis for connection management.

    Features:
    - Async Redis operations
    - Automatic serialization/deserialization
    - TTL (time-to-live) support
    - Cache key generation
    - Prefix support for namespacing
    - Metrics tracking (hits, misses, hit rate by type)
    """

    # Class-level metrics (shared across instances)
    _metrics: Dict[str, Any] = {
        "hits": 0,
        "misses": 0,
        "hits_by_type": defaultdict(int),
        "misses_by_type": defaultdict(int)
    }

    def __init__(self, prefix: Optional[str] = None):
        """
        Initialize cache service.

        Args:
            prefix: Optional prefix for cache keys (default: CACHE_PREFIX from settings)
        """
        self.prefix = prefix or settings.CACHE_PREFIX

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.prefix}:{key}"

    def _generate_key(self, key_prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and parameters

        Example:
            _generate_key("api:user", user_id=123) -> "agent_squad:api:user:hash"
        """
        # Create deterministic hash from arguments
        key_data = f"{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:8]
        return self._make_key(f"{key_prefix}:{key_hash}")

    async def get(self, key: str, cache_type: str = "general") -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key
            cache_type: Type of cache for metrics tracking (default: "general")

        Returns:
            Cached value (deserialized from JSON) or None if not found
        """
        try:
            redis = await get_redis()
            value = await redis.get(self._make_key(key))

            # Track metrics
            if value:
                self._metrics["hits"] += 1
                self._metrics["hits_by_type"][cache_type] += 1
                return json.loads(value)
            else:
                self._metrics["misses"] += 1
                self._metrics["misses_by_type"][cache_type] += 1
                return None
        except Exception as e:
            print(f"Cache get error: {e}")
            self._metrics["misses"] += 1
            self._metrics["misses_by_type"][cache_type] += 1
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
            ttl: Time-to-live in seconds (default: CACHE_DEFAULT_TTL from settings)

        Returns:
            True if successful, False otherwise
        """
        try:
            redis = await get_redis()
            serialized = json.dumps(value, default=str)

            # Use default TTL from settings if not specified
            ttl = ttl or settings.CACHE_DEFAULT_TTL

            await redis.setex(self._make_key(key), ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found or error
        """
        try:
            redis = await get_redis()
            result = await redis.delete(self._make_key(key))
            return result > 0
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern

        Args:
            pattern: Pattern to match (e.g., "user:*", "api:user:*")

        Returns:
            Number of keys deleted

        Example:
            clear_pattern("user:*")  # Clear all user caches
        """
        try:
            redis = await get_redis()

            # Build prefixed pattern
            prefixed_pattern = self._make_key(pattern)

            keys = []
            async for key in redis.scan_iter(match=prefixed_pattern):
                keys.append(key)

            if keys:
                # Delete in batches of 1000
                deleted = 0
                batch_size = 1000
                for i in range(0, len(keys), batch_size):
                    batch = keys[i:i + batch_size]
                    deleted += await redis.delete(*batch)
                return deleted

            return 0
        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            redis = await get_redis()
            return await redis.exists(self._make_key(key)) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics

        Returns:
            Dictionary with metrics including hit rates by type
        """
        total_requests = self._metrics["hits"] + self._metrics["misses"]
        hit_rate_overall = (self._metrics["hits"] / total_requests * 100) if total_requests > 0 else 0.0

        # Calculate hit rates by type
        hit_rates_by_type = {}
        for cache_type in set(list(self._metrics["hits_by_type"].keys()) + list(self._metrics["misses_by_type"].keys())):
            hits = self._metrics["hits_by_type"][cache_type]
            misses = self._metrics["misses_by_type"][cache_type]
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0.0
            hit_rates_by_type[cache_type] = round(hit_rate, 2)

        return {
            "hit_rate_overall": round(hit_rate_overall, 2),
            "total_requests": total_requests,
            "cache_hits": self._metrics["hits"],
            "cache_misses": self._metrics["misses"],
            "hit_rates_by_type": hit_rates_by_type
        }

    async def get_redis_memory_usage(self) -> float:
        """
        Get Redis memory usage in MB

        Returns:
            Memory usage in megabytes
        """
        try:
            redis = await get_redis()
            info = await redis.info("memory")
            used_memory = info.get("used_memory", 0)
            return round(used_memory / (1024 * 1024), 2)  # Convert bytes to MB
        except Exception as e:
            print(f"Error getting Redis memory: {e}")
            return 0.0

    def reset_metrics(self):
        """
        Reset all metrics (useful for testing)
        """
        self._metrics["hits"] = 0
        self._metrics["misses"] = 0
        self._metrics["hits_by_type"] = defaultdict(int)
        self._metrics["misses_by_type"] = defaultdict(int)

    async def clear_all(self) -> int:
        """
        Clear all cache keys with this service's prefix

        Returns:
            Number of keys deleted
        """
        return await self.clear_pattern("*")


# Global cache instance
_cache_service: Optional[CacheService] = None


def get_cache(prefix: Optional[str] = None) -> CacheService:
    """
    Get cache service instance (singleton)

    Args:
        prefix: Optional custom prefix for cache keys

    Returns:
        CacheService instance

    Note: Redis connection management is handled by backend.core.redis.
          No need to connect/disconnect the cache service.
    """
    global _cache_service
    if _cache_service is None or prefix is not None:
        _cache_service = CacheService(prefix=prefix)
    return _cache_service


# Note: close_cache() is no longer needed.
# Redis connection lifecycle is managed by backend.core.redis:
#   - get_redis() initializes connection
#   - close_redis() closes connection (called in app shutdown)


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
            cache = get_cache()  # Synchronous call (no await)

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

    cache = get_cache()  # Synchronous call (no await)

    # Set value
    await cache.set("my_key", {"data": "value"}, ttl=300)

    # Get value
    value = await cache.get("my_key")

    # Delete value
    await cache.delete("my_key")

    # Clear pattern
    await cache.clear_pattern("api:user:*")


Example 5: Application lifecycle

    Note: Redis connection lifecycle is managed by backend.core.redis.
    No need to connect/disconnect the cache service.

    from backend.core.redis import get_redis, close_redis
    from backend.services.cache_service import get_cache

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        await get_redis()  # Initialize Redis connection
        cache = get_cache()  # Get cache service (no await needed)
        yield
        # Shutdown
        await close_redis()  # Close Redis connection
"""
