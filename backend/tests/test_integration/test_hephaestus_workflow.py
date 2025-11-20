"""
End-to-End Integration Tests for Hephaestus-Style Workflows

Tests the complete flow: Discovery → Branching → Task Spawning → Kanban → Guardian
"""
import pytest
from uuid import uuid4
from datetime import datetime

from httpx import AsyncClient

from backend.models.workflow import DynamicTask, WorkflowPhase
from backend.models.message import AgentMessage
from backend.agents.discovery.discovery_engine import Discovery, WorkContext
from backend.agents.branching.branching_engine import get_branching_engine
from backend.agents.task_spawning import get_agent_task_spawner


@pytest.mark.asyncio
async def test_complete_discovery_to_branch_flow(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test complete flow: discovery → branch → task → kanban"""
    # Login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # 1. Create message with discovery
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
    
    # 2. Discover opportunity
    from backend.agents.discovery.discovery_engine import get_discovery_engine
    from sqlalchemy import select
    
    discovery_engine = get_discovery_engine()
    
    # Get messages
    stmt = select(AgentMessage).where(
        AgentMessage.task_execution_id == test_task_execution.id
    ).limit(10)
    result = await test_db.execute(stmt)
    messages = list(result.scalars().all())
    
    context = WorkContext(
        execution_id=test_task_execution.id,
        agent_id=test_squad_member_backend.id,
        phase=WorkflowPhase.VALIDATION,  # Found during validation
        recent_messages=messages,
        recent_tasks=[],
    )
    
    discoveries = await discovery_engine.analyze_work_context(test_db, context)
    assert len(discoveries) > 0
    
    # 3. Create branch from discovery
    branching_engine = get_branching_engine()
    branch = await branching_engine.create_branch_from_discovery(
        db=test_db,
        execution_id=test_task_execution.id,
        discovery=discoveries[0],
        branch_name="Caching Optimization Branch",
        initial_task_title="Analyze caching pattern",
        initial_task_description="Investigate how caching can be applied to 12 routes",
        agent_id=test_squad_member_backend.id,
    )
    
    assert branch.status == "active"
    assert branch.branch_phase == "investigation"
    
    # 4. Verify tasks in branch
    branch_tasks = await branching_engine.get_branch_tasks(test_db, branch.id)
    assert len(branch_tasks) >= 1
    
    # 5. Check Kanban board includes branch tasks
    response = await client.get(
        f"/api/v1/kanban/workflows/{test_task_execution.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    kanban_data = response.json()
    
    # Should have tasks
    all_tasks = [task for col in kanban_data["columns"] for task in col["tasks"]]
    assert len(all_tasks) >= 1


@pytest.mark.asyncio
async def test_guardian_monitors_branching_workflow(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test that Guardian monitors branching workflows"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create branch with tasks
    from backend.agents.branching.branching_engine import get_branching_engine
    from backend.agents.discovery.discovery_engine import Discovery
    
    branching_engine = get_branching_engine()
    discovery = Discovery(
        type="bug",
        description="Critical security issue found",
        value_score=0.9,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.9,
        context={},
    )
    
    branch = await branching_engine.create_branch_from_discovery(
        db=test_db,
        execution_id=test_task_execution.id,
        discovery=discovery,
        agent_id=test_squad_member_backend.id,
    )
    
    # Check Guardian detects anomalies
    response = await client.get(
        f"/api/v1/advanced-guardian/workflows/{test_task_execution.id}/anomalies",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    # May or may not have anomalies depending on task quality


@pytest.mark.asyncio
async def test_branch_merge_integration(
    client: AsyncClient,
    test_user_data,
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test complete branch lifecycle: create → work → merge"""
    await client.post("/api/v1/auth/register", json=test_user_data)
    login = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login.json()["access_token"]
    
    # Create branch
    from backend.agents.branching.branching_engine import get_branching_engine
    from backend.agents.discovery.discovery_engine import Discovery
    
    branching_engine = get_branching_engine()
    discovery = Discovery(
        type="optimization",
        description="Performance optimization found",
        value_score=0.8,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.8,
        context={},
    )
    
    branch = await branching_engine.create_branch_from_discovery(
        db=test_db,
        execution_id=test_task_execution.id,
        discovery=discovery,
        initial_task_title="Investigate optimization",
        initial_task_description="Study the optimization opportunity",
        agent_id=test_squad_member_backend.id,
    )
    
    # Complete tasks in branch
    tasks = await branching_engine.get_branch_tasks(test_db, branch.id)
    if tasks:
        from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
        workflow_engine = PhaseBasedWorkflowEngine()
        await workflow_engine.update_task_status(
            db=test_db,
            task_id=tasks[0].id,
            new_status="completed",
        )
    
    # Merge branch
    response = await client.post(
        f"/api/v1/branching/branches/{branch.id}/merge",
        headers={"Authorization": f"Bearer {token}"},
        json={"merge_summary": "Optimization analyzed and ready for implementation"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "merged"

