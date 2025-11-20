"""
Tests for Discovery Engine (Stream D)

Comprehensive tests for the DiscoveryEngine that analyzes work context,
evaluates discovery value, and generates task suggestions.
"""
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, patch

from backend.agents.discovery.discovery_engine import (
    DiscoveryEngine,
    TaskSuggestion,
    WorkContext,
    get_discovery_engine,
)
from backend.agents.discovery.discovery_detector import Discovery
from backend.models.workflow import WorkflowPhase
from backend.models.message import AgentMessage
from backend.models.project import TaskExecution
from backend.models.workflow import DynamicTask


@pytest.mark.asyncio
async def test_discovery_engine_initialization():
    """Test DiscoveryEngine initialization"""
    engine = DiscoveryEngine()
    
    assert engine is not None
    assert engine.detector is not None
    assert engine.task_spawner is not None


@pytest.mark.asyncio
async def test_get_discovery_engine_singleton():
    """Test that get_discovery_engine returns singleton"""
    engine1 = get_discovery_engine()
    engine2 = get_discovery_engine()
    
    assert engine1 is engine2  # Same instance


@pytest.mark.asyncio
async def test_analyze_work_context_with_messages(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test analyzing work context with agent messages"""
    engine = DiscoveryEngine()
    
    # Create messages with discoveries
    message1 = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=None,
        content="I noticed this caching pattern could apply to 12 other API routes for 40% speedup",
        message_type="status_update",
        message_metadata={},
        task_execution_id=test_task_execution.id,
    )
    test_db.add(message1)
    
    message2 = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=None,
        content="Found a bug in the auth system",
        message_type="status_update",
        message_metadata={},
        task_execution_id=test_task_execution.id,
    )
    test_db.add(message2)
    await test_db.commit()
    
    # Reload messages
    from sqlalchemy import select
    stmt = select(AgentMessage).where(
        AgentMessage.task_execution_id == test_task_execution.id
    ).limit(10)
    result = await test_db.execute(stmt)
    messages = list(result.scalars().all())
    
    # Create work context
    context = WorkContext(
        execution_id=test_task_execution.id,
        agent_id=test_squad_member_backend.id,
        phase=WorkflowPhase.INVESTIGATION,
        recent_messages=messages,
        recent_tasks=[],
    )
    
    # Analyze
    discoveries = await engine.analyze_work_context(test_db, context)
    
    assert len(discoveries) > 0
    # Should detect optimization and bug
    discovery_types = {d.type for d in discoveries}
    assert "optimization" in discovery_types or "bug" in discovery_types


@pytest.mark.asyncio
async def test_evaluate_discovery_value_phase_alignment():
    """Test value evaluation boosts when phase matches"""
    engine = DiscoveryEngine()
    
    discovery = Discovery(
        type="optimization",
        description="Could apply caching to 12 routes for 40% speedup",
        value_score=0.6,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.7,
        context={},
    )
    
    context = WorkContext(
        execution_id=uuid4(),
        agent_id=uuid4(),
        phase=WorkflowPhase.INVESTIGATION,  # Matches discovery phase
        recent_messages=[],
        recent_tasks=[],
    )
    
    # Mock db (not actually used in evaluation)
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    evaluated_value = await engine.evaluate_discovery_value(mock_db, discovery, context)
    
    # Should be boosted (original 0.6 * 1.15 for phase match)
    assert evaluated_value > discovery.value_score
    assert evaluated_value <= 1.0


@pytest.mark.asyncio
async def test_evaluate_discovery_value_impact_indicators():
    """Test value evaluation boosts with impact indicators"""
    engine = DiscoveryEngine()
    
    discovery = Discovery(
        type="optimization",
        description="This optimization could apply to 15 routes and improve performance by 50%",
        value_score=0.6,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.7,
        context={},
    )
    
    context = WorkContext(
        execution_id=uuid4(),
        agent_id=uuid4(),
        phase=WorkflowPhase.INVESTIGATION,
        recent_messages=[],
        recent_tasks=[],
    )
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    evaluated_value = await engine.evaluate_discovery_value(mock_db, discovery, context)
    
    # Should be boosted due to impact indicators ("apply to", numbers)
    assert evaluated_value > 0.6
    assert evaluated_value <= 1.0


@pytest.mark.asyncio
async def test_suggest_task_from_discovery():
    """Test generating task suggestion from discovery"""
    engine = DiscoveryEngine()
    
    discovery = Discovery(
        type="optimization",
        description="Caching pattern could apply to 12 other API routes for 40% speedup",
        value_score=0.7,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.8,
        context={},
    )
    
    context = WorkContext(
        execution_id=uuid4(),
        agent_id=uuid4(),
        phase=WorkflowPhase.INVESTIGATION,
        recent_messages=[],
        recent_tasks=[],
    )
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    suggestion = await engine.suggest_task_from_discovery(mock_db, discovery, context)
    
    assert isinstance(suggestion, TaskSuggestion)
    assert suggestion.title is not None
    assert len(suggestion.title) > 0
    assert suggestion.description is not None
    assert suggestion.phase == WorkflowPhase.INVESTIGATION
    assert suggestion.estimated_value == discovery.value_score
    assert suggestion.priority in ["low", "medium", "high", "urgent"]


@pytest.mark.asyncio
async def test_suggest_task_priority_mapping():
    """Test task priority mapping from value score"""
    engine = DiscoveryEngine()
    
    # High value discovery
    high_value = Discovery(
        type="bug",
        description="Critical bug found",
        value_score=0.9,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.9,
        context={},
    )
    
    # Medium value discovery
    medium_value = Discovery(
        type="optimization",
        description="Performance optimization opportunity",
        value_score=0.65,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.7,
        context={},
    )
    
    # Low value discovery
    low_value = Discovery(
        type="refactoring",
        description="Minor refactoring needed",
        value_score=0.4,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.6,
        context={},
    )
    
    context = WorkContext(
        execution_id=uuid4(),
        agent_id=uuid4(),
        phase=WorkflowPhase.INVESTIGATION,
        recent_messages=[],
        recent_tasks=[],
    )
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    high_suggestion = await engine.suggest_task_from_discovery(mock_db, high_value, context)
    medium_suggestion = await engine.suggest_task_from_discovery(mock_db, medium_value, context)
    low_suggestion = await engine.suggest_task_from_discovery(mock_db, low_value, context)
    
    assert high_suggestion.priority in ["high", "urgent"]
    assert medium_suggestion.priority == "medium"
    assert low_suggestion.priority == "low"


@pytest.mark.asyncio
async def test_discover_and_suggest_tasks_complete_flow(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test complete discover-and-suggest flow"""
    engine = DiscoveryEngine()
    
    # Create message with discovery
    message = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=None,
        content="Found optimization: could apply caching to 15 routes for 50% speedup",
        message_type="status_update",
        message_metadata={},
        task_execution_id=test_task_execution.id,
    )
    test_db.add(message)
    await test_db.commit()
    
    # Get messages
    from sqlalchemy import select
    stmt = select(AgentMessage).where(
        AgentMessage.task_execution_id == test_task_execution.id
    ).limit(10)
    result = await test_db.execute(stmt)
    messages = list(result.scalars().all())
    
    context = WorkContext(
        execution_id=test_task_execution.id,
        agent_id=test_squad_member_backend.id,
        phase=WorkflowPhase.INVESTIGATION,
        recent_messages=messages,
        recent_tasks=[],
    )
    
    # Discover and suggest
    suggestions = await engine.discover_and_suggest_tasks(
        db=test_db,
        context=context,
        min_value_threshold=0.5,
    )
    
    assert len(suggestions) > 0
    assert all(isinstance(s, TaskSuggestion) for s in suggestions)
    assert all(s.estimated_value >= 0.5 for s in suggestions)
    # Should be sorted by value (highest first)
    values = [s.estimated_value for s in suggestions]
    assert values == sorted(values, reverse=True)


@pytest.mark.asyncio
async def test_discover_and_suggest_tasks_filters_by_threshold():
    """Test that min_value_threshold filters suggestions"""
    engine = DiscoveryEngine()
    
    context = WorkContext(
        execution_id=uuid4(),
        agent_id=uuid4(),
        phase=WorkflowPhase.INVESTIGATION,
        recent_messages=[],
        recent_tasks=[],
        work_output="Minor optimization opportunity (low value)",
    )
    
    from unittest.mock import MagicMock
    mock_db = MagicMock()
    
    # With high threshold
    high_threshold = await engine.discover_and_suggest_tasks(
        db=mock_db,
        context=context,
        min_value_threshold=0.8,
    )
    
    # With low threshold
    low_threshold = await engine.discover_and_suggest_tasks(
        db=mock_db,
        context=context,
        min_value_threshold=0.3,
    )
    
    # Low threshold should return more or equal suggestions
    assert len(low_threshold) >= len(high_threshold)


@pytest.mark.asyncio
async def test_analyze_task_patterns_phase_imbalance(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test task pattern analysis detects phase imbalance"""
    engine = DiscoveryEngine()
    
    # Create many tasks in one phase
    tasks = []
    for i in range(6):
        task = DynamicTask(
            id=uuid4(),
            parent_execution_id=test_task_execution.id,
            phase=WorkflowPhase.INVESTIGATION.value,
            spawned_by_agent_id=test_squad_member_backend.id,
            title=f"Investigation task {i}",
            description="Test",
            status="pending",
        )
        tasks.append(task)
        test_db.add(task)
    
    await test_db.commit()
    
    context = WorkContext(
        execution_id=test_task_execution.id,
        agent_id=test_squad_member_backend.id,
        phase=WorkflowPhase.INVESTIGATION,
        recent_messages=[],
        recent_tasks=tasks,
    )
    
    discoveries = await engine._analyze_task_patterns(test_db, context)
    
    # Should detect phase imbalance
    imbalance_discoveries = [d for d in discoveries if d.type == "workflow_balance"]
    assert len(imbalance_discoveries) > 0


@pytest.mark.asyncio
async def test_deduplicate_discoveries():
    """Test discovery deduplication"""
    engine = DiscoveryEngine()
    
    discovery1 = Discovery(
        type="optimization",
        description="Caching pattern could apply to 12 routes",
        value_score=0.6,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.7,
        context={},
    )
    
    discovery2 = Discovery(
        type="optimization",
        description="Caching pattern could apply to 12 routes",  # Same description
        value_score=0.8,  # Higher value
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.8,
        context={},
    )
    
    discoveries = engine._deduplicate_discoveries([discovery1, discovery2])
    
    # Should deduplicate and keep higher value
    assert len(discoveries) == 1
    assert discoveries[0].value_score == 0.8


@pytest.mark.asyncio
async def test_find_blocking_tasks_investigation_phase(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test finding blocking tasks for investigation phase"""
    engine = DiscoveryEngine()
    
    # Create in-progress investigation task
    blocking_task = DynamicTask(
        id=uuid4(),
        parent_execution_id=test_task_execution.id,
        phase=WorkflowPhase.INVESTIGATION.value,
        spawned_by_agent_id=test_squad_member_backend.id,
        title="In progress investigation",
        description="Test",
        status="in_progress",
    )
    test_db.add(blocking_task)
    await test_db.commit()
    
    context = WorkContext(
        execution_id=test_task_execution.id,
        agent_id=test_squad_member_backend.id,
        phase=WorkflowPhase.INVESTIGATION,
        recent_messages=[],
        recent_tasks=[blocking_task],
    )
    
    discovery = Discovery(
        type="optimization",
        description="Test discovery",
        value_score=0.7,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.7,
        context={},
    )
    
    blocking_ids = await engine._find_blocking_tasks(test_db, context, discovery)
    
    # Should find in-progress investigation task
    assert len(blocking_ids) > 0
    assert blocking_task.id in blocking_ids


@pytest.mark.asyncio
async def test_enhance_discovery_with_context():
    """Test enhancing discovery with work context"""
    engine = DiscoveryEngine()
    
    discovery = Discovery(
        type="optimization",
        description="Test",
        value_score=0.7,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.7,
        context={},
    )
    
    execution_id = uuid4()
    agent_id = uuid4()
    
    context = WorkContext(
        execution_id=execution_id,
        agent_id=agent_id,
        phase=WorkflowPhase.INVESTIGATION,
        recent_messages=[AgentMessage(
            id=uuid4(),
            sender_id=agent_id,
            recipient_id=None,
            content="Test",
            message_type="status_update",
            message_metadata={},
            task_execution_id=execution_id,
        )],
        recent_tasks=[],
    )
    
    enhanced = engine._enhance_discovery_with_context(discovery, context)
    
    assert enhanced.context["execution_id"] == str(execution_id)
    assert enhanced.context["agent_id"] == str(agent_id)
    assert enhanced.context["current_phase"] == "investigation"
    assert enhanced.context["message_count"] == 1
    assert enhanced.context["task_count"] == 0

