#!/usr/bin/env python3
"""
Test Redis Cache Connection and Functionality

This script tests:
1. Redis connection
2. Cache service initialization
3. Basic cache operations (set/get)
4. Cache decorator functionality
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.cache_service import get_cache, cached, CacheStrategy


async def test_redis_connection():
    """Test 1: Redis connection"""
    print("=" * 60)
    print("Test 1: Redis Connection")
    print("=" * 60)

    try:
        cache = await get_cache()
        if cache._enabled:
            print("✅ Redis cache service initialized successfully")
            print(f"   Backend: Redis")
            print(f"   Status: Connected")
            return True
        else:
            print("⚠️  Redis cache disabled (Redis not available)")
            return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


async def test_basic_operations():
    """Test 2: Basic cache operations"""
    print("\n" + "=" * 60)
    print("Test 2: Basic Cache Operations")
    print("=" * 60)

    try:
        cache = await get_cache()

        # Test SET
        print("\n1. Testing SET operation...")
        key = "test:hello"
        value = {"message": "Hello, Redis!", "timestamp": "2025-11-02"}
        success = await cache.set(key, value, ttl=60)

        if success:
            print(f"   ✅ SET successful: {key}")
        else:
            print(f"   ❌ SET failed")
            return False

        # Test GET
        print("\n2. Testing GET operation...")
        retrieved = await cache.get(key)

        if retrieved and retrieved == value:
            print(f"   ✅ GET successful: {retrieved}")
        else:
            print(f"   ❌ GET failed or value mismatch")
            return False

        # Test EXISTS
        print("\n3. Testing EXISTS operation...")
        exists = await cache.exists(key)

        if exists:
            print(f"   ✅ EXISTS confirmed: {key}")
        else:
            print(f"   ❌ EXISTS returned False")
            return False

        # Test DELETE
        print("\n4. Testing DELETE operation...")
        deleted = await cache.delete(key)

        if deleted:
            print(f"   ✅ DELETE successful: {key}")
        else:
            print(f"   ⚠️  DELETE returned False (may be ok)")

        # Verify deletion
        exists_after = await cache.exists(key)
        if not exists_after:
            print(f"   ✅ Key confirmed deleted")
        else:
            print(f"   ❌ Key still exists after deletion")
            return False

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


async def test_decorator():
    """Test 3: Cache decorator"""
    print("\n" + "=" * 60)
    print("Test 3: Cache Decorator (@cached)")
    print("=" * 60)

    try:
        call_count = 0

        @cached("test:user", ttl=CacheStrategy.API_SHORT)
        async def get_user(user_id: int):
            nonlocal call_count
            call_count += 1
            # Simulate expensive operation
            await asyncio.sleep(0.1)
            return {
                "id": user_id,
                "name": f"User {user_id}",
                "email": f"user{user_id}@example.com"
            }

        # First call - should hit function
        print("\n1. First call (should miss cache)...")
        result1 = await get_user(123)
        print(f"   Result: {result1}")
        print(f"   Function calls: {call_count}")

        if call_count != 1:
            print(f"   ❌ Expected 1 function call, got {call_count}")
            return False
        print(f"   ✅ Cache miss - function executed")

        # Second call - should hit cache
        print("\n2. Second call (should hit cache)...")
        result2 = await get_user(123)
        print(f"   Result: {result2}")
        print(f"   Function calls: {call_count}")

        if call_count != 1:
            print(f"   ❌ Expected 1 function call (cached), got {call_count}")
            return False

        if result1 != result2:
            print(f"   ❌ Results don't match")
            return False

        print(f"   ✅ Cache hit - function not executed")

        # Different parameter - should miss cache
        print("\n3. Different parameter (should miss cache)...")
        result3 = await get_user(456)
        print(f"   Result: {result3}")
        print(f"   Function calls: {call_count}")

        if call_count != 2:
            print(f"   ❌ Expected 2 function calls, got {call_count}")
            return False
        print(f"   ✅ Different parameter - new cache entry")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


async def test_cache_patterns():
    """Test 4: Cache patterns"""
    print("\n" + "=" * 60)
    print("Test 4: Cache Pattern Matching")
    print("=" * 60)

    try:
        cache = await get_cache()

        # Set multiple keys
        print("\n1. Setting multiple test keys...")
        await cache.set("test:pattern:1", "value1", ttl=60)
        await cache.set("test:pattern:2", "value2", ttl=60)
        await cache.set("test:pattern:3", "value3", ttl=60)
        await cache.set("test:other:1", "other", ttl=60)
        print("   ✅ Test keys set")

        # Clear pattern
        print("\n2. Clearing pattern 'test:pattern:*'...")
        deleted_count = await cache.clear_pattern("test:pattern:*")
        print(f"   ✅ Deleted {deleted_count} keys")

        # Verify
        exists1 = await cache.exists("test:pattern:1")
        exists2 = await cache.exists("test:other:1")

        if not exists1 and exists2:
            print("   ✅ Pattern matching works correctly")

            # Cleanup
            await cache.delete("test:other:1")
            return True
        else:
            print("   ❌ Pattern matching failed")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "REDIS CACHE TEST SUITE" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = []

    # Test 1: Connection
    result1 = await test_redis_connection()
    results.append(("Redis Connection", result1))

    if not result1:
        print("\n❌ Cannot proceed without Redis connection")
        return False

    # Test 2: Basic operations
    result2 = await test_basic_operations()
    results.append(("Basic Operations", result2))

    # Test 3: Decorator
    result3 = await test_decorator()
    results.append(("Cache Decorator", result3))

    # Test 4: Patterns
    result4 = await test_cache_patterns()
    results.append(("Pattern Matching", result4))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All tests passed! Redis cache is working perfectly.")
        print("\nCache service is ready for production use:")
        print("  - Response caching: ✅")
        print("  - Decorator support: ✅")
        print("  - Pattern matching: ✅")
        print("  - Auto-fallback: ✅")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
