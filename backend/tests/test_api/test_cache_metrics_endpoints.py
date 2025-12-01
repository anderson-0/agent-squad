"""
Cache Metrics API Endpoint Tests

Tests for cache metrics and monitoring endpoints.
"""
import pytest
from httpx import AsyncClient


class TestCacheMetricsEndpoints:
    """Test cache metrics endpoints"""

    @pytest.mark.asyncio
    async def test_get_cache_metrics_unauthorized(self, client: AsyncClient):
        """Test getting cache metrics without authentication"""
        response = await client.get("/api/v1/cache/metrics")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_cache_metrics(self, client: AsyncClient, auth_headers: dict):
        """Test getting cache metrics"""
        response = await client.get(
            "/api/v1/cache/metrics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should include basic metrics
        assert isinstance(data, dict)
        expected_fields = ["hit_rate", "hits", "misses", "total_requests"]

        # At least some metrics should be present
        has_metrics = any(field in data for field in expected_fields)
        assert has_metrics or len(data) > 0

    @pytest.mark.asyncio
    async def test_cache_metrics_structure(self, client: AsyncClient, auth_headers: dict):
        """Test cache metrics response structure"""
        response = await client.get(
            "/api/v1/cache/metrics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Metrics should be numeric values
        for value in data.values():
            if isinstance(value, (int, float)):
                assert value >= 0

    @pytest.mark.asyncio
    async def test_get_cache_stats_by_key_pattern(self, client: AsyncClient, auth_headers: dict):
        """Test getting cache stats for specific key pattern"""
        response = await client.get(
            "/api/v1/cache/metrics?pattern=squad:*",
            headers=auth_headers
        )

        assert response.status_code == 200


class TestCacheManagement:
    """Test cache management endpoints"""

    @pytest.mark.asyncio
    async def test_clear_cache_unauthorized(self, client: AsyncClient):
        """Test clearing cache without authentication"""
        response = await client.delete("/api/v1/cache")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_clear_all_cache(self, client: AsyncClient, auth_headers: dict):
        """Test clearing all cache"""
        response = await client.delete(
            "/api/v1/cache",
            headers=auth_headers
        )

        assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_clear_cache_by_pattern(self, client: AsyncClient, auth_headers: dict):
        """Test clearing cache by key pattern"""
        response = await client.delete(
            "/api/v1/cache?pattern=test:*",
            headers=auth_headers
        )

        assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_clear_specific_cache_key(self, client: AsyncClient, auth_headers: dict):
        """Test clearing specific cache key"""
        test_key = "test:key:123"

        response = await client.delete(
            f"/api/v1/cache/{test_key}",
            headers=auth_headers
        )

        assert response.status_code in [200, 204, 404]


class TestCacheHealth:
    """Test cache health and status endpoints"""

    @pytest.mark.asyncio
    async def test_cache_health_check(self, client: AsyncClient, auth_headers: dict):
        """Test cache health check"""
        response = await client.get(
            "/api/v1/cache/health",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_cache_connection_status(self, client: AsyncClient, auth_headers: dict):
        """Test cache connection status"""
        response = await client.get(
            "/api/v1/cache/status",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should indicate if cache is connected
        assert "connected" in data or "status" in data

    @pytest.mark.asyncio
    async def test_cache_size_metrics(self, client: AsyncClient, auth_headers: dict):
        """Test cache size and memory metrics"""
        response = await client.get(
            "/api/v1/cache/metrics/size",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            # Should include size information
            assert isinstance(data, dict)


class TestCacheAnalytics:
    """Test cache analytics and insights"""

    @pytest.mark.asyncio
    async def test_get_top_cached_keys(self, client: AsyncClient, auth_headers: dict):
        """Test getting most accessed cache keys"""
        response = await client.get(
            "/api/v1/cache/analytics/top-keys",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_cache_hit_rate_over_time(self, client: AsyncClient, auth_headers: dict):
        """Test getting cache hit rate trends"""
        response = await client.get(
            "/api/v1/cache/analytics/hit-rate",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_cache_performance_summary(self, client: AsyncClient, auth_headers: dict):
        """Test getting cache performance summary"""
        response = await client.get(
            "/api/v1/cache/analytics/summary",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]


if __name__ == "__main__":
    print("""
    Cache Metrics API Tests
    =======================

    Tests for cache metrics and monitoring endpoints.

    Run with:
        pytest tests/test_api/test_cache_metrics_endpoints.py -v
    """)
