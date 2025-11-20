"""
Tests for Discovery API Endpoints (Stream D)
"""
import pytest
from uuid import uuid4
from datetime import datetime

from httpx import AsyncClient

from backend.models.message import AgentMessage
from backend.models.project import TaskExecution
from backend.models.workflow import WorkflowPhase


@pytest.mark.asyncio
async def test_analyze_work_context_endpoint(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test analyze work context endpoint"""
    # Login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create message
    message = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=None,
        content="Found optimization: could apply caching to 12 routes for 40% speedup",
        message_type="status_update",
        message_metadata={},
        task_execution_id=test_task_execution.id,
    )
    test_db.add(message)
    await test_db.commit()
    
    # Call endpoint
    response = await client.get(
        f"/api/v1/discovery/workflows/{test_task_execution.id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "agent_id": str(test_squad_member_backend.id),
            "phase": "investigation",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "discoveries" in data
    assert "total" in data
    assert data["execution_id"] == str(test_task_execution.id)
    assert data["agent_id"] == str(test_squad_member_backend.id)


@pytest.mark.asyncio
async def test_get_task_suggestions_endpoint(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test get task suggestions endpoint"""
    # Login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create message
    message = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=None,
        content="Performance issue detected: slow endpoint needs optimization",
        message_type="status_update",
        message_metadata={},
        task_execution_id=test_task_execution.id,
    )
    test_db.add(message)
    await test_db.commit()
    
    # Call endpoint
    response = await client.get(
        f"/api/v1/discovery/workflows/{test_task_execution.id}/suggestions",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "agent_id": str(test_squad_member_backend.id),
            "phase": "investigation",
            "min_value": 0.5,
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert "total" in data
    assert isinstance(data["suggestions"], list)
    
    # If suggestions found, validate structure
    if len(data["suggestions"]) > 0:
        suggestion = data["suggestions"][0]
        assert "title" in suggestion
        assert "description" in suggestion
        assert "phase" in suggestion
        assert "estimated_value" in suggestion
        assert "priority" in suggestion


@pytest.mark.asyncio
async def test_analyze_work_context_endpoint_not_found(
    client: AsyncClient,
    test_user_data,
):
    """Test analyze endpoint with invalid execution ID"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    response = await client.get(
        f"/api/v1/discovery/workflows/{uuid4()}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "agent_id": str(uuid4()),
            "phase": "investigation",
        }
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_suggestions_min_value_validation(
    client: AsyncClient,
    test_user_data,
    test_task_execution,
    test_squad_member_backend,
):
    """Test suggestions endpoint validates min_value parameter"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Invalid min_value (> 1.0)
    response = await client.get(
        f"/api/v1/discovery/workflows/{test_task_execution.id}/suggestions",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "agent_id": str(test_squad_member_backend.id),
            "phase": "investigation",
            "min_value": 1.5,  # Invalid
        }
    )
    
    assert response.status_code == 422  # Validation error
    
    # Valid min_value
    response = await client.get(
        f"/api/v1/discovery/workflows/{test_task_execution.id}/suggestions",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "agent_id": str(test_squad_member_backend.id),
            "phase": "investigation",
            "min_value": 0.7,
        }
    )
    
    assert response.status_code in [200, 404]  # 404 if execution not found, otherwise OK

