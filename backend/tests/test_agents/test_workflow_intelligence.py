"""
Tests for Workflow Intelligence System (Stream I)
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.intelligence import WorkflowIntelligence, get_workflow_intelligence
from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.models.project import TaskExecution
from backend.models.squad import Squad, SquadMember
from backend.models.branching import WorkflowBranch


@pytest.fixture
async def setup_intelligence_test_data(db: AsyncSession):
    """Set up test data for intelligence tests"""
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
async def test_workflow_intelligence_initialization():
    """Test that WorkflowIntelligence can be initialized"""
    intelligence = get_workflow_intelligence()
    assert intelligence is not None
    assert isinstance(intelligence, WorkflowIntelligence)


@pytest.mark.asyncio
async def test_suggest_next_tasks(db: AsyncSession, setup_intelligence_test_data):
    """Test task suggestion generation"""
    execution, agent = setup_intelligence_test_data
    intelligence = get_workflow_intelligence()
    
    suggestions = await intelligence.suggest_next_tasks(
        db=db,
        execution_id=execution.id,
        agent_id=agent.id,
        max_suggestions=5,
    )
    
    assert isinstance(suggestions, list)
    assert len(suggestions) <= 5
    
    if suggestions:
        suggestion = suggestions[0]
        assert hasattr(suggestion, 'title')
        assert hasattr(suggestion, 'phase')
        assert hasattr(suggestion, 'estimated_value')
        assert 0.0 <= suggestion.estimated_value <= 1.0


@pytest.mark.asyncio
async def test_predict_workflow_outcomes(db: AsyncSession, setup_intelligence_test_data):
    """Test workflow outcome prediction"""
    execution, agent = setup_intelligence_test_data
    intelligence = get_workflow_intelligence()
    
    prediction = await intelligence.predict_workflow_outcomes(
        db=db,
        execution_id=execution.id,
    )
    
    assert prediction is not None
    assert prediction.execution_id == execution.id
    assert 0.0 <= prediction.success_probability <= 1.0
    assert 0.0 <= prediction.confidence <= 1.0
    assert isinstance(prediction.risk_factors, list)
    assert isinstance(prediction.reasoning, str)


@pytest.mark.asyncio
async def test_optimize_task_ordering(db: AsyncSession, setup_intelligence_test_data):
    """Test task ordering optimization"""
    execution, agent = setup_intelligence_test_data
    intelligence = get_workflow_intelligence()
    
    # Create some test tasks
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
        blocking_task_ids=[task1.id],  # Task 2 depends on Task 1
    )
    
    await db.commit()
    
    # Optimize ordering
    ordered_tasks = await intelligence.optimize_task_ordering(
        db=db,
        execution_id=execution.id,
    )
    
    assert isinstance(ordered_tasks, list)
    assert len(ordered_tasks) >= 2
    
    # Task 1 should come before Task 2 (dependency)
    task1_index = next((i for i, t in enumerate(ordered_tasks) if t.id == task1.id), -1)
    task2_index = next((i for i, t in enumerate(ordered_tasks) if t.id == task2.id), -1)
    
    if task1.status != "completed" and task2.status != "completed":
        assert task1_index < task2_index, "Task 1 should come before Task 2 (dependency order)"


@pytest.mark.asyncio
async def test_determine_current_phase(db: AsyncSession, setup_intelligence_test_data):
    """Test phase determination logic"""
    execution, agent = setup_intelligence_test_data
    intelligence = get_workflow_intelligence()
    
    # Test with no tasks
    phase = intelligence._determine_current_phase([])
    assert phase == WorkflowPhase.INVESTIGATION
    
    # Test with tasks
    from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
    engine = PhaseBasedWorkflowEngine()
    
    await engine.spawn_task(
        db=db,
        agent_id=agent.id,
        execution_id=execution.id,
        phase=WorkflowPhase.BUILDING,
        title="Build task",
        description="Building",
    )
    
    await engine.spawn_task(
        db=db,
        agent_id=agent.id,
        execution_id=execution.id,
        phase=WorkflowPhase.BUILDING,
        title="Build task 2",
        description="More building",
    )
    
    await db.commit()
    
    all_tasks = await engine.get_tasks_for_execution(db=db, execution_id=execution.id)
    phase = intelligence._determine_current_phase(all_tasks)
    assert phase == WorkflowPhase.BUILDING


@pytest.mark.asyncio
async def test_suggest_from_workflow_gaps(db: AsyncSession, setup_intelligence_test_data):
    """Test workflow gap suggestions"""
    execution, agent = setup_intelligence_test_data
    intelligence = get_workflow_intelligence()
    
    from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
    engine = PhaseBasedWorkflowEngine()
    
    # Create many investigation tasks
    for i in range(5):
        await engine.spawn_task(
            db=db,
            agent_id=agent.id,
            execution_id=execution.id,
            phase=WorkflowPhase.INVESTIGATION,
            title=f"Investigation {i}",
            description="Investigation task",
        )
    
    await db.commit()
    
    all_tasks = await engine.get_tasks_for_execution(db=db, execution_id=execution.id)
    from backend.agents.guardian import get_workflow_health_monitor
    health_monitor = get_workflow_health_monitor()
    workflow_health = await health_monitor.calculate_health(db=db, execution_id=execution.id)
    
    suggestions = await intelligence._suggest_from_workflow_gaps(
        db=db,
        execution_id=execution.id,
        all_tasks=all_tasks,
        workflow_health=workflow_health,
        active_branches=[],
    )
    
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_deduplicate_suggestions():
    """Test suggestion deduplication"""
    intelligence = get_workflow_intelligence()
    
    from backend.agents.intelligence import TaskSuggestion
    
    suggestions = [
        TaskSuggestion(
            title="Test Task",
            description="Description",
            phase=WorkflowPhase.BUILDING,
            rationale="Rationale",
            estimated_value=0.7,
            priority="high",
            confidence=0.8,
            reasoning="Reasoning",
        ),
        TaskSuggestion(
            title="test task",  # Same title (case-insensitive)
            description="Different description",
            phase=WorkflowPhase.BUILDING,
            rationale="Different rationale",
            estimated_value=0.8,
            priority="high",
            confidence=0.9,
            reasoning="Different reasoning",
        ),
    ]
    
    deduplicated = intelligence._deduplicate_suggestions(suggestions)
    assert len(deduplicated) == 1  # Should be deduplicated


@pytest.mark.asyncio
async def test_build_dependency_graph(db: AsyncSession, setup_intelligence_test_data):
    """Test dependency graph building"""
    execution, agent = setup_intelligence_test_data
    intelligence = get_workflow_intelligence()
    
    from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
    engine = PhaseBasedWorkflowEngine()
    
    task1 = await engine.spawn_task(
        db=db,
        agent_id=agent.id,
        execution_id=execution.id,
        phase=WorkflowPhase.BUILDING,
        title="Task 1",
        description="Task 1",
    )
    
    task2 = await engine.spawn_task(
        db=db,
        agent_id=agent.id,
        execution_id=execution.id,
        phase=WorkflowPhase.BUILDING,
        title="Task 2",
        description="Task 2",
        blocking_task_ids=[task1.id],
    )
    
    await db.commit()
    
    all_tasks = await engine.get_tasks_for_execution(db=db, execution_id=execution.id, include_dependencies=True)
    graph = intelligence._build_dependency_graph(all_tasks)
    
    assert isinstance(graph, dict)
    assert task1.id in graph
    assert task2.id in graph

