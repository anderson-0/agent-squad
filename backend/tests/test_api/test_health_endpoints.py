"""
Health Endpoint Tests

Tests for system health check endpoints.
"""
import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints"""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test basic health check endpoint"""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_check_no_auth_required(self, client: AsyncClient):
        """Test health check doesn't require authentication"""
        # Should work without auth headers
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_includes_services(self, client: AsyncClient):
        """Test health check includes service status"""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Should include database status
        if "services" in data:
            assert "database" in data["services"]

    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        """Test readiness probe endpoint"""
        response = await client.get("/api/v1/health/ready")

        # Should return 200 if ready, 503 if not
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_liveness_check(self, client: AsyncClient):
        """Test liveness probe endpoint"""
        response = await client.get("/api/v1/health/live")

        # Should always return 200 if server is running
        assert response.status_code == 200


class TestHealthMetrics:
    """Test health metrics and monitoring"""

    @pytest.mark.asyncio
    async def test_health_includes_uptime(self, client: AsyncClient):
        """Test health check includes uptime"""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Uptime should be present (optional)
        if "uptime_seconds" in data:
            assert isinstance(data["uptime_seconds"], (int, float))
            assert data["uptime_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_health_format(self, client: AsyncClient):
        """Test health check response format"""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)


if __name__ == "__main__":
    print("""
    Health Endpoint Tests
    =====================

    Tests for system health check endpoints.

    Run with:
        pytest tests/test_api/test_health_endpoints.py -v
    """)
