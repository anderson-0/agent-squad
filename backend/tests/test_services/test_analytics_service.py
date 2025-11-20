"""
Tests for Analytics Service (Stream K)
"""
import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.analytics_service import AnalyticsService, get_analytics_service
from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.models.project import TaskExecution
from backend.models.squad import Squad, SquadMember


@pytest.fixture
async def setup_analytics_test_data(db: AsyncSession):
    """Set up test data for analytics tests"""
    user_id = uuid4()
    org_id = uuid4()
    squad_id = uuid4()
    project_id = uuid4()
    task_id = uuid4()
    agent_id = uuid4()

    squad = Squad(id=squad_id, name="Test Squad", organization_id=org_id)
    db.add(squad)
    agent = SquadMember(id=agent_id, squad_id=squad_id, user_id=user_id, role="backend_developer", is_active=True)
    db.add(agent)
    execution = TaskExecution(id=uuid4(), task_id=task_id, squad_id=squad_id, status="in_progress")
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    await db.refresh(agent)
    return execution, agent


@pytest.mark.asyncio
async def test_analytics_service_initialization():
    """Test that AnalyticsService can be initialized"""
    service = get_analytics_service()
    assert service is not None
    assert isinstance(service, AnalyticsService)


@pytest.mark.asyncio
async def test_calculate_workflow_analytics(db: AsyncSession, setup_analytics_test_data):
    """Test workflow analytics calculation"""
    execution, agent = setup_analytics_test_data
    service = get_analytics_service()
    
    # Create some tasks
    from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
    engine = PhaseBasedWorkflowEngine()
    
    task1 = await engine.spawn_task(
        db=db,
        agent_id=agent.id,
        execution_id=execution.id,
        phase=WorkflowPhase.BUILDING,
        title="Task 1",
        description="First task",
    )
    
    task2 = await engine.spawn_task(
        db=db,
        agent_id=agent.id,
        execution_id=execution.id,
        phase=WorkflowPhase.BUILDING,
        title="Task 2",
        description="Second task",
    )
    
    await db.commit()
    
    # Calculate analytics
    analytics = await service.calculate_workflow_analytics(
        db=db,
        execution_id=execution.id,
    )
    
    assert analytics is not None
    assert analytics.execution_id == execution.id
    assert 0.0 <= analytics.completion_rate <= 1.0
    assert analytics.phase_distribution is not None
    assert isinstance(analytics.agent_performance, dict)


@pytest.mark.asyncio
async def test_get_workflow_graph_data(db: AsyncSession, setup_analytics_test_data):
    """Test workflow graph data generation"""
    execution, agent = setup_analytics_test_data
    service = get_analytics_service()
    
    # Create tasks with dependencies
    from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
    engine = PhaseBasedWorkflowEngine()
    
    task1 = await engine.spawn_task(
        db=db,
        agent_id=agent.id,
        execution_id=execution.id,
        phase=WorkflowPhase.BUILDING,
        title="Task 1",
        description="First task",
    )
    
    task2 = await engine.spawn_task(
        db=db,
        agent_id=agent.id,
        execution_id=execution.id,
        phase=WorkflowPhase.BUILDING,
        title="Task 2",
        description="Second task",
        blocking_task_ids=[task1.id],
    )
    
    await db.commit()
    
    # Get graph data
    graph_data = await service.get_workflow_graph_data(
        db=db,
        execution_id=execution.id,
    )
    
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert "branches" in graph_data
    assert "phases" in graph_data
    
    assert len(graph_data["nodes"]) >= 2
    assert len(graph_data["edges"]) >= 1  # Task 1 blocks Task 2
    assert len(graph_data["phases"]) == 3  # 3 phases


@pytest.mark.asyncio
async def test_analytics_with_no_tasks(db: AsyncSession, setup_analytics_test_data):
    """Test analytics calculation with no tasks"""
    execution, agent = setup_analytics_test_data
    service = get_analytics_service()
    
    analytics = await service.calculate_workflow_analytics(
        db=db,
        execution_id=execution.id,
    )
    
    assert analytics.completion_rate == 0.0
    assert analytics.phase_distribution["investigation"] == 0
    assert analytics.phase_distribution["building"] == 0
    assert analytics.phase_distribution["validation"] == 0

