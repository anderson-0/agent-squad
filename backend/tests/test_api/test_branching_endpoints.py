"""
Tests for Branching API Endpoints (Stream E)
"""
import pytest
from uuid import uuid4

from httpx import AsyncClient

from backend.models.workflow import DynamicTask
from backend.models.workflow import WorkflowPhase


@pytest.mark.asyncio
async def test_create_branch_endpoint(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test create branch endpoint"""
    # Login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create branch
    response = await client.post(
        f"/api/v1/branching/workflows/{test_task_execution.id}/branches",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "discovery_id": str(uuid4()),
            "branch_name": "Optimization Branch",
            "initial_task_title": "Analyze caching",
            "initial_task_description": "Investigate caching optimization",
            "agent_id": str(test_squad_member_backend.id),
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["parent_execution_id"] == str(test_task_execution.id)
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_get_branches_endpoint(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test get branches endpoint"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create a branch first
    from backend.agents.branching.branching_engine import get_branching_engine
    from backend.agents.discovery.discovery_engine import Discovery
    
    engine = get_branching_engine()
    discovery = Discovery(
        type="bug",
        description="Test bug",
        value_score=0.8,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.9,
        context={},
    )
    
    branch = await engine.create_branch_from_discovery(
        db=test_db,
        execution_id=test_task_execution.id,
        discovery=discovery,
        agent_id=test_squad_member_backend.id,
    )
    
    # Get branches
    response = await client.get(
        f"/api/v1/branching/workflows/{test_task_execution.id}/branches",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    branches = response.json()
    assert isinstance(branches, list)
    assert len(branches) >= 1
    assert any(b["id"] == str(branch.id) for b in branches)


@pytest.mark.asyncio
async def test_merge_branch_endpoint(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test merge branch endpoint"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create branch
    from backend.agents.branching.branching_engine import get_branching_engine
    from backend.agents.discovery.discovery_engine import Discovery
    
    engine = get_branching_engine()
    discovery = Discovery(
        type="optimization",
        description="Test",
        value_score=0.7,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.8,
        context={},
    )
    
    branch = await engine.create_branch_from_discovery(
        db=test_db,
        execution_id=test_task_execution.id,
        discovery=discovery,
        agent_id=test_squad_member_backend.id,
    )
    
    # Merge branch
    response = await client.post(
        f"/api/v1/branching/branches/{branch.id}/merge",
        headers={"Authorization": f"Bearer {token}"},
        json={"merge_summary": "Successfully merged"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "merged"
    assert "merge_summary" in data["metadata"]


@pytest.mark.asyncio
async def test_get_branch_tasks_endpoint(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test get branch tasks endpoint"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create branch with task
    from backend.agents.branching.branching_engine import get_branching_engine
    from backend.agents.discovery.discovery_engine import Discovery
    
    engine = get_branching_engine()
    discovery = Discovery(
        type="optimization",
        description="Test",
        value_score=0.7,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.8,
        context={},
    )
    
    branch = await engine.create_branch_from_discovery(
        db=test_db,
        execution_id=test_task_execution.id,
        discovery=discovery,
        initial_task_title="Branch task",
        initial_task_description="Test",
        agent_id=test_squad_member_backend.id,
    )
    
    # Get branch tasks
    response = await client.get(
        f"/api/v1/branching/branches/{branch.id}/tasks",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "branch" in data
    assert "tasks" in data
    assert data["total_tasks"] >= 1

