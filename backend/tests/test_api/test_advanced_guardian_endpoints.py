"""
Tests for Advanced Guardian API Endpoints (Stream G)
"""
import pytest
from uuid import uuid4

from httpx import AsyncClient

from backend.models.workflow import DynamicTask
from backend.models.workflow import WorkflowPhase


@pytest.mark.asyncio
async def test_detect_anomalies_endpoint(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test detect anomalies endpoint"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create scenario that triggers anomaly
    task = DynamicTask(
        id=uuid4(),
        parent_execution_id=test_task_execution.id,
        phase=WorkflowPhase.INVESTIGATION.value,
        spawned_by_agent_id=test_squad_member_backend.id,
        title="Vague task",
        description="Do things",  # Very brief
        status="pending",
    )
    test_db.add(task)
    await test_db.commit()
    
    # Detect anomalies
    response = await client.get(
        f"/api/v1/advanced-guardian/workflows/{test_task_execution.id}/anomalies",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    anomalies = response.json()
    assert isinstance(anomalies, list)


@pytest.mark.asyncio
async def test_get_recommendations_endpoint(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
):
    """Test get recommendations endpoint"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    response = await client.get(
        f"/api/v1/advanced-guardian/workflows/{test_task_execution.id}/recommendations",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    recommendations = response.json()
    assert isinstance(recommendations, list)
    
    # If recommendations found, validate structure
    if len(recommendations) > 0:
        rec = recommendations[0]
        assert "type" in rec
        assert "action" in rec
        assert "priority" in rec


@pytest.mark.asyncio
async def test_get_advanced_metrics_endpoint(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
):
    """Test get advanced metrics endpoint"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    response = await client.get(
        f"/api/v1/advanced-guardian/workflows/{test_task_execution.id}/advanced-metrics",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "anomalies" in data
    assert "recommendations" in data
    assert "coherence_scores" in data
    assert data["execution_id"] == str(test_task_execution.id)

