"""
Tests for Kanban API Endpoints (Stream F)
"""
import pytest
from uuid import uuid4

from httpx import AsyncClient

from backend.models.workflow import DynamicTask
from backend.models.workflow import WorkflowPhase


@pytest.mark.asyncio
async def test_get_kanban_board(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test get Kanban board endpoint"""
    # Login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create tasks in different phases
    task1 = DynamicTask(
        id=uuid4(),
        parent_execution_id=test_task_execution.id,
        phase=WorkflowPhase.INVESTIGATION.value,
        spawned_by_agent_id=test_squad_member_backend.id,
        title="Investigation task",
        description="Test investigation",
        status="in_progress",
    )
    task2 = DynamicTask(
        id=uuid4(),
        parent_execution_id=test_task_execution.id,
        phase=WorkflowPhase.BUILDING.value,
        spawned_by_agent_id=test_squad_member_backend.id,
        title="Building task",
        description="Test building",
        status="pending",
    )
    task3 = DynamicTask(
        id=uuid4(),
        parent_execution_id=test_task_execution.id,
        phase=WorkflowPhase.VALIDATION.value,
        spawned_by_agent_id=test_squad_member_backend.id,
        title="Validation task",
        description="Test validation",
        status="completed",
    )
    
    test_db.add(task1)
    test_db.add(task2)
    test_db.add(task3)
    await test_db.commit()
    
    # Call endpoint
    response = await client.get(
        f"/api/v1/kanban/workflows/{test_task_execution.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "execution_id" in data
    assert "columns" in data
    assert "total_tasks" in data
    assert data["total_tasks"] == 3
    
    # Check columns
    assert len(data["columns"]) == 3
    column_phases = {col["phase"] for col in data["columns"]}
    assert "investigation" in column_phases
    assert "building" in column_phases
    assert "validation" in column_phases
    
    # Check task distribution
    investigation_col = next(c for c in data["columns"] if c["phase"] == "investigation")
    building_col = next(c for c in data["columns"] if c["phase"] == "building")
    validation_col = next(c for c in data["columns"] if c["phase"] == "validation")
    
    assert investigation_col["total_tasks"] == 1
    assert investigation_col["in_progress_tasks"] == 1
    assert building_col["total_tasks"] == 1
    assert building_col["pending_tasks"] == 1
    assert validation_col["total_tasks"] == 1
    assert validation_col["completed_tasks"] == 1


@pytest.mark.asyncio
async def test_get_kanban_board_empty(
    client: AsyncClient,
    test_user_data,
    test_task_execution,
):
    """Test Kanban board with no tasks"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    response = await client.get(
        f"/api/v1/kanban/workflows/{test_task_execution.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_tasks"] == 0
    assert all(col["total_tasks"] == 0 for col in data["columns"])


@pytest.mark.asyncio
async def test_get_kanban_board_not_found(
    client: AsyncClient,
    test_user_data,
):
    """Test Kanban board with invalid execution ID"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    response = await client.get(
        f"/api/v1/kanban/workflows/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_dependency_graph(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test get dependency graph endpoint"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create tasks with dependencies
    task1 = DynamicTask(
        id=uuid4(),
        parent_execution_id=test_task_execution.id,
        phase=WorkflowPhase.INVESTIGATION.value,
        spawned_by_agent_id=test_squad_member_backend.id,
        title="Task 1",
        description="Blocks task 2",
        status="in_progress",
    )
    task2 = DynamicTask(
        id=uuid4(),
        parent_execution_id=test_task_execution.id,
        phase=WorkflowPhase.BUILDING.value,
        spawned_by_agent_id=test_squad_member_backend.id,
        title="Task 2",
        description="Blocked by task 1",
        status="pending",
    )
    
    test_db.add(task1)
    test_db.add(task2)
    
    # Create dependency (task1 blocks task2)
    from backend.models.workflow import task_dependencies
    test_db.execute(
        task_dependencies.insert().values(
            blocking_task_id=task1.id,
            blocked_task_id=task2.id
        )
    )
    
    await test_db.commit()
    
    # Call endpoint
    response = await client.get(
        f"/api/v1/kanban/workflows/{test_task_execution.id}/dependencies",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "nodes" in data
    assert "edges" in data
    assert "execution_id" in data
    assert data["total_tasks"] == 2
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    
    # Check edge structure
    edge = data["edges"][0]
    assert "from" in edge
    assert "to" in edge
    assert edge["type"] == "blocks"
    assert edge["from"] == str(task1.id)
    assert edge["to"] == str(task2.id)

