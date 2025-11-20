"""
Tests for Cache Service

Tests Redis-based caching functionality including:
- Basic get/set/delete operations
- Batch operations
- Pattern invalidation
- TTL expiration
"""
import pytest
import asyncio
from backend.services.cache_service import get_cache, CacheService
from backend.core.redis import get_redis, close_redis


@pytest.fixture
async def redis_client():
    """Initialize Redis connection for tests"""
    client = await get_redis()
    yield client
    # Cleanup test keys after each test
    await client.flushdb()


@pytest.fixture
def cache_service():
    """Get cache service instance"""
    return get_cache(prefix="test")


@pytest.mark.asyncio
class TestCacheService:
    """Cache service tests"""

    async def test_set_and_get(self, cache_service, redis_client):
        """Test basic set and get operations"""
        # Set value
        success = await cache_service.set("test_key", {"data": "value"}, ttl=60)
        assert success is True

        # Get value
        value = await cache_service.get("test_key")
        assert value is not None
        assert value["data"] == "value"

    async def test_get_nonexistent_key(self, cache_service, redis_client):
        """Test getting nonexistent key returns None"""
        value = await cache_service.get("nonexistent_key")
        assert value is None

    async def test_delete_key(self, cache_service, redis_client):
        """Test deleting a key"""
        # Set value
        await cache_service.set("test_key", {"data": "value"}, ttl=60)

        # Delete key
        deleted = await cache_service.delete("test_key")
        assert deleted is True

        # Verify key is gone
        value = await cache_service.get("test_key")
        assert value is None

    async def test_delete_nonexistent_key(self, cache_service, redis_client):
        """Test deleting nonexistent key"""
        deleted = await cache_service.delete("nonexistent_key")
        assert deleted is False

    async def test_exists(self, cache_service, redis_client):
        """Test key existence check"""
        # Key doesn't exist
        exists = await cache_service.exists("test_key")
        assert exists is False

        # Set key
        await cache_service.set("test_key", {"data": "value"}, ttl=60)

        # Key exists
        exists = await cache_service.exists("test_key")
        assert exists is True

    async def test_ttl_expiration(self, cache_service, redis_client):
        """Test TTL expiration"""
        # Set key with 1 second TTL
        await cache_service.set("test_key", {"data": "value"}, ttl=1)

        # Key exists immediately
        value = await cache_service.get("test_key")
        assert value is not None

        # Wait for expiration
        await asyncio.sleep(2)

        # Key should be expired
        value = await cache_service.get("test_key")
        assert value is None

    async def test_clear_pattern(self, cache_service, redis_client):
        """Test clearing keys matching pattern"""
        # Set multiple keys
        await cache_service.set("user:1", {"id": 1}, ttl=60)
        await cache_service.set("user:2", {"id": 2}, ttl=60)
        await cache_service.set("squad:1", {"id": 1}, ttl=60)

        # Clear user keys
        deleted = await cache_service.clear_pattern("user:*")
        assert deleted == 2

        # Verify user keys are gone
        assert await cache_service.get("user:1") is None
        assert await cache_service.get("user:2") is None

        # Verify squad key still exists
        assert await cache_service.get("squad:1") is not None

    async def test_json_serialization(self, cache_service, redis_client):
        """Test JSON serialization of complex objects"""
        complex_data = {
            "id": 123,
            "name": "Test",
            "nested": {
                "key": "value",
                "list": [1, 2, 3]
            },
            "numbers": [1.5, 2.3, 3.7]
        }

        # Set complex data
        await cache_service.set("complex", complex_data, ttl=60)

        # Get and verify
        value = await cache_service.get("complex")
        assert value == complex_data

    async def test_prefix_isolation(self, redis_client):
        """Test that different prefixes are isolated"""
        cache1 = CacheService(prefix="prefix1")
        cache2 = CacheService(prefix="prefix2")

        # Set same key in both caches
        await cache1.set("test", {"prefix": 1}, ttl=60)
        await cache2.set("test", {"prefix": 2}, ttl=60)

        # Verify isolation
        value1 = await cache1.get("test")
        value2 = await cache2.get("test")

        assert value1["prefix"] == 1
        assert value2["prefix"] == 2

    async def test_default_ttl(self, cache_service, redis_client):
        """Test default TTL is applied"""
        from backend.core.config import settings

        # Set without TTL (should use default)
        await cache_service.set("test_key", {"data": "value"})

        # Verify key exists
        value = await cache_service.get("test_key")
        assert value is not None

        # Check TTL is set
        ttl = await redis_client.ttl(cache_service._make_key("test_key"))
        assert ttl > 0
        assert ttl <= settings.CACHE_DEFAULT_TTL

    async def test_generate_key_deterministic(self, cache_service):
        """Test key generation is deterministic"""
        key1 = cache_service._generate_key("prefix", "arg1", "arg2", param="value")
        key2 = cache_service._generate_key("prefix", "arg1", "arg2", param="value")
        assert key1 == key2

    async def test_generate_key_unique(self, cache_service):
        """Test different inputs generate different keys"""
        key1 = cache_service._generate_key("prefix", "arg1")
        key2 = cache_service._generate_key("prefix", "arg2")
        assert key1 != key2


@pytest.mark.asyncio
class TestCacheDecorator:
    """Tests for @cached decorator"""

    @pytest.fixture
    def cache_service(self):
        """Get cache service for decorator tests"""
        return get_cache(prefix="decorator_test")

    async def test_cached_decorator_basic(self, cache_service, redis_client):
        """Test basic @cached decorator functionality"""
        from backend.services.cache_service import cached

        call_count = 0

        @cached("test_func", ttl=60)
        async def expensive_function(arg1: str, arg2: int):
            nonlocal call_count
            call_count += 1
            return f"{arg1}:{arg2}"

        # First call - should execute function
        result1 = await expensive_function("hello", 123)
        assert result1 == "hello:123"
        assert call_count == 1

        # Second call - should use cache
        result2 = await expensive_function("hello", 123)
        assert result2 == "hello:123"
        assert call_count == 1  # Not incremented

    async def test_cached_decorator_different_args(self, cache_service, redis_client):
        """Test @cached decorator with different arguments"""
        from backend.services.cache_service import cached

        call_count = 0

        @cached("test_func", ttl=60)
        async def expensive_function(arg: str):
            nonlocal call_count
            call_count += 1
            return f"result:{arg}"

        # Call with different arguments
        result1 = await expensive_function("arg1")
        result2 = await expensive_function("arg2")
        result3 = await expensive_function("arg1")  # Should use cache

        assert result1 == "result:arg1"
        assert result2 == "result:arg2"
        assert result3 == "result:arg1"
        assert call_count == 2  # Only 2 unique calls

    async def test_cached_decorator_custom_key(self, cache_service, redis_client):
        """Test @cached decorator with custom key function"""
        from backend.services.cache_service import cached

        def custom_key(user_id: int):
            return f"user:{user_id}"

        call_count = 0

        @cached("custom", ttl=60, key_func=custom_key)
        async def get_user(user_id: int):
            nonlocal call_count
            call_count += 1
            return {"id": user_id, "name": f"User {user_id}"}

        # First call
        result1 = await get_user(123)
        assert result1["id"] == 123
        assert call_count == 1

        # Second call - should use cache
        result2 = await get_user(123)
        assert result2["id"] == 123
        assert call_count == 1


@pytest.mark.asyncio
async def test_cache_service_singleton():
    """Test get_cache returns singleton"""
    cache1 = get_cache()
    cache2 = get_cache()
    assert cache1 is cache2


@pytest.mark.asyncio
async def test_cache_service_custom_prefix():
    """Test get_cache with custom prefix creates new instance"""
    cache_default = get_cache()
    cache_custom = get_cache(prefix="custom")
    assert cache_default.prefix != cache_custom.prefix
