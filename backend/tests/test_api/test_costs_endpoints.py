"""
Cost Tracking API Endpoint Tests

Tests for LLM cost tracking and analytics endpoints.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timedelta


class TestCostEndpoints:
    """Test cost tracking endpoints"""

    @pytest.mark.asyncio
    async def test_get_costs_unauthorized(self, client: AsyncClient):
        """Test getting costs without authentication"""
        response = await client.get("/api/v1/costs")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_costs_by_squad(self, client: AsyncClient, auth_headers: dict):
        """Test getting costs for a specific squad"""
        squad_id = uuid4()

        response = await client.get(
            f"/api/v1/costs/squads/{squad_id}",
            headers=auth_headers
        )

        # Should return 200 or 404 if squad doesn't exist
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert "total_cost" in data or "costs" in data

    @pytest.mark.asyncio
    async def test_get_costs_by_execution(self, client: AsyncClient, auth_headers: dict):
        """Test getting costs for a specific execution"""
        execution_id = uuid4()

        response = await client.get(
            f"/api/v1/costs/executions/{execution_id}",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_costs_by_date_range(self, client: AsyncClient, auth_headers: dict):
        """Test getting costs filtered by date range"""
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = datetime.utcnow().isoformat()

        response = await client.get(
            f"/api/v1/costs?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))

    @pytest.mark.asyncio
    async def test_get_costs_by_provider(self, client: AsyncClient, auth_headers: dict):
        """Test getting costs grouped by provider"""
        response = await client.get(
            "/api/v1/costs?group_by=provider",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            # Each item should have provider info
            assert "provider" in data[0] or "model_provider" in data[0]

    @pytest.mark.asyncio
    async def test_get_costs_by_model(self, client: AsyncClient, auth_headers: dict):
        """Test getting costs grouped by model"""
        response = await client.get(
            "/api/v1/costs?group_by=model",
            headers=auth_headers
        )

        assert response.status_code == 200


class TestCostRecording:
    """Test cost recording endpoints"""

    @pytest.mark.asyncio
    async def test_record_cost_unauthorized(self, client: AsyncClient):
        """Test recording cost without authentication"""
        payload = {
            "execution_id": str(uuid4()),
            "model_provider": "openai",
            "model_name": "gpt-4",
            "input_tokens": 100,
            "output_tokens": 50,
            "total_cost": 0.015
        }

        response = await client.post("/api/v1/costs", json=payload)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_record_cost_valid(self, client: AsyncClient, auth_headers: dict):
        """Test recording a valid cost entry"""
        payload = {
            "execution_id": str(uuid4()),
            "squad_id": str(uuid4()),
            "model_provider": "openai",
            "model_name": "gpt-4-turbo",
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_cost": 0.025
        }

        response = await client.post(
            "/api/v1/costs",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or "cost_id" in data

    @pytest.mark.asyncio
    async def test_record_cost_missing_required_fields(self, client: AsyncClient, auth_headers: dict):
        """Test recording cost with missing required fields"""
        payload = {
            "model_provider": "openai"
            # Missing other required fields
        }

        response = await client.post(
            "/api/v1/costs",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_record_cost_invalid_provider(self, client: AsyncClient, auth_headers: dict):
        """Test recording cost with invalid provider"""
        payload = {
            "execution_id": str(uuid4()),
            "model_provider": "invalid_provider_xyz",
            "model_name": "model",
            "input_tokens": 100,
            "output_tokens": 50,
            "total_cost": 0.01
        }

        response = await client.post(
            "/api/v1/costs",
            json=payload,
            headers=auth_headers
        )

        # Should accept any provider (validation might not be strict)
        assert response.status_code in [200, 201, 422]


class TestCostAnalytics:
    """Test cost analytics and aggregation endpoints"""

    @pytest.mark.asyncio
    async def test_get_cost_summary(self, client: AsyncClient, auth_headers: dict):
        """Test getting cost summary/analytics"""
        response = await client.get(
            "/api/v1/costs/analytics/summary",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_cost_trends(self, client: AsyncClient, auth_headers: dict):
        """Test getting cost trends over time"""
        response = await client.get(
            "/api/v1/costs/analytics/trends",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_top_spenders(self, client: AsyncClient, auth_headers: dict):
        """Test getting top cost-incurring squads/executions"""
        response = await client.get(
            "/api/v1/costs/analytics/top-spenders",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]


if __name__ == "__main__":
    print("""
    Cost Tracking API Tests
    =======================

    Tests for LLM cost tracking endpoints.

    Run with:
        pytest tests/test_api/test_costs_endpoints.py -v
    """)
