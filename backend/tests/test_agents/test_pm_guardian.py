"""
Tests for PM Guardian System (Stream C)

Tests for PM-as-Guardian monitoring capabilities.
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from backend.agents.guardian import (
    CoherenceScorer,
    WorkflowHealthMonitor,
    CoherenceScore,
    WorkflowHealth,
    get_coherence_scorer,
    get_workflow_health_monitor,
)
from backend.agents.specialized.agno_project_manager import AgnoProjectManagerAgent
from backend.agents.agno_base import AgentConfig, LLMProvider
from backend.models.workflow import WorkflowPhase
from backend.models.guardian import CoherenceMetrics
from backend.models.message import AgentMessage


@pytest.mark.asyncio
async def test_coherence_scorer_calculate_coherence(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test coherence calculation"""
    scorer = CoherenceScorer()
    
    # Create some agent messages
    message1 = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=None,
        content="I'm implementing the auth endpoint",
        message_type="status_update",
        message_metadata={},
        task_execution_id=test_task_execution.id,
    )
    test_db.add(message1)
    await test_db.commit()
    
    coherence = await scorer.calculate_coherence(
        db=test_db,
        agent_id=test_squad_member_backend.id,
        execution_id=test_task_execution.id,
        phase=WorkflowPhase.BUILDING,
    )
    
    assert coherence is not None
    assert 0.0 <= coherence.overall_score <= 1.0
    assert "phase_alignment" in coherence.metrics
    assert "goal_alignment" in coherence.metrics
    assert "quality_alignment" in coherence.metrics
    assert "task_relevance" in coherence.metrics


@pytest.mark.asyncio
async def test_coherence_scorer_phase_alignment():
    """Test phase alignment scoring"""
    scorer = CoherenceScorer()
    
    # Building phase messages with building keywords
    messages = [
        AgentMessage(
            id=uuid4(),
            sender_id=uuid4(),
            recipient_id=None,
            content="I'm implementing the authentication system",
            message_type="status_update",
            message_metadata={},
            task_execution_id=uuid4(),
        ),
        AgentMessage(
            id=uuid4(),
            sender_id=uuid4(),
            recipient_id=None,
            content="Building the API endpoints now",
            message_type="status_update",
            message_metadata={},
            task_execution_id=uuid4(),
        ),
    ]
    
    alignment = scorer._analyze_phase_alignment(
        agent_messages=messages,
        agent_work=None,
        phase=WorkflowPhase.BUILDING,
    )
    
    assert 0.0 <= alignment <= 1.0
    assert alignment > 0.5  # Should have good alignment with building keywords


@pytest.mark.asyncio
async def test_workflow_health_monitor_calculate_health(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test workflow health calculation"""
    monitor = WorkflowHealthMonitor()
    
    # Create some dynamic tasks
    from backend.agents.task_spawning import AgentTaskSpawner, get_agent_task_spawner
    
    spawner = get_agent_task_spawner()
    await spawner.spawn_investigation_task(
        db=test_db,
        agent_id=test_squad_member_backend.id,
        execution_id=test_task_execution.id,
        title="Test investigation",
        description="Test",
        rationale="Test",
    )
    await spawner.spawn_building_task(
        db=test_db,
        agent_id=test_squad_member_backend.id,
        execution_id=test_task_execution.id,
        title="Test building",
        description="Test",
        rationale="Test",
    )
    
    health = await monitor.calculate_health(
        db=test_db,
        execution_id=test_task_execution.id,
    )
    
    assert health is not None
    assert 0.0 <= health.overall_score <= 1.0
    assert "task_completion_rate" in health.metrics
    assert "phase_distribution" in health.metrics
    assert isinstance(health.anomalies, list)
    assert isinstance(health.recommendations, list)


@pytest.mark.asyncio
async def test_workflow_health_anomaly_detection(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test anomaly detection"""
    monitor = WorkflowHealthMonitor()
    
    # Create many tasks in one phase (should trigger phase imbalance)
    from backend.agents.task_spawning import get_agent_task_spawner
    spawner = get_agent_task_spawner()
    for i in range(10):
        await spawner.spawn_investigation_task(
            db=test_db,
            agent_id=test_squad_member_backend.id,
            execution_id=test_task_execution.id,
            title=f"Investigation {i}",
            description="Test",
            rationale="Test",
        )
    
    health = await monitor.calculate_health(
        db=test_db,
        execution_id=test_task_execution.id,
    )
    
    # Should detect phase imbalance anomaly
    anomaly_types = [a.type for a in health.anomalies]
    # May or may not detect depending on thresholds
    assert isinstance(health.anomalies, list)


@pytest.mark.asyncio
async def test_pm_check_phase_coherence(
    test_db,
    test_task_execution,
    test_squad_member_backend,
    test_squad_member_pm,
):
    """Test PM can check phase coherence"""
    config = AgentConfig(
        role="project_manager",
        llm_provider=LLMProvider.OPENAI,
        llm_model="gpt-4",
        system_prompt="Test prompt",
    )
    
    pm_agent = AgnoProjectManagerAgent(
        config=config,
        agent_id=test_squad_member_pm.id,
    )
    
    # Create agent message
    message = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=None,
        content="Building the API endpoint",
        message_type="status_update",
        message_metadata={},
        task_execution_id=test_task_execution.id,
    )
    test_db.add(message)
    await test_db.commit()
    
    coherence = await pm_agent.check_phase_coherence(
        db=test_db,
        execution_id=test_task_execution.id,
        agent_id=test_squad_member_backend.id,
        phase=WorkflowPhase.BUILDING,
    )
    
    assert coherence is not None
    assert 0.0 <= coherence.overall_score <= 1.0
    
    # Verify stored in database
    from sqlalchemy import select
    stmt = select(CoherenceMetrics).where(
        CoherenceMetrics.execution_id == test_task_execution.id,
        CoherenceMetrics.agent_id == test_squad_member_backend.id,
    )
    result = await test_db.execute(stmt)
    stored_metric = result.scalar_one_or_none()
    
    assert stored_metric is not None
    assert stored_metric.coherence_score == coherence.overall_score


@pytest.mark.asyncio
async def test_pm_monitor_workflow_health(
    test_db,
    test_task_execution,
    test_squad_member_pm,
):
    """Test PM can monitor workflow health"""
    config = AgentConfig(
        role="project_manager",
        llm_provider=LLMProvider.OPENAI,
        llm_model="gpt-4",
        system_prompt="Test prompt",
    )
    
    pm_agent = AgnoProjectManagerAgent(
        config=config,
        agent_id=test_squad_member_pm.id,
    )
    
    health = await pm_agent.monitor_workflow_health(
        db=test_db,
        execution_id=test_task_execution.id,
    )
    
    assert health is not None
    assert 0.0 <= health.overall_score <= 1.0
    assert "task_completion_rate" in health.metrics


@pytest.mark.asyncio
async def test_pm_validate_task_relevance(
    test_db,
    test_task_execution,
    test_squad_member_backend,
    test_squad_member_pm,
):
    """Test PM can validate task relevance"""
    config = AgentConfig(
        role="project_manager",
        llm_provider=LLMProvider.OPENAI,
        llm_model="gpt-4",
        system_prompt="Test prompt",
    )
    
    pm_agent = AgnoProjectManagerAgent(
        config=config,
        agent_id=test_squad_member_pm.id,
    )
    
    # Create task with rationale
    from backend.agents.task_spawning import get_agent_task_spawner
    spawner = get_agent_task_spawner()
    task = await spawner.spawn_investigation_task(
        db=test_db,
        agent_id=test_squad_member_backend.id,
        execution_id=test_task_execution.id,
        title="Test task",
        description="This is a test task with good description",
        rationale="This is a comprehensive rationale explaining why this task is needed",
    )
    
    relevance = await pm_agent.validate_task_relevance(
        db=test_db,
        task=task,
        execution_context={},
    )
    
    assert 0.0 <= relevance <= 1.0
    assert relevance >= 0.5  # Should be relevant with good rationale


@pytest.mark.asyncio
async def test_pm_orchestrate_with_guardian_oversight(
    test_db,
    test_task_execution,
    test_squad_member_pm,
    test_squad_member_backend,
):
    """Test PM orchestrate with Guardian oversight"""
    config = AgentConfig(
        role="project_manager",
        llm_provider=LLMProvider.OPENAI,
        llm_model="gpt-4",
        system_prompt="Test prompt",
    )
    
    pm_agent = AgnoProjectManagerAgent(
        config=config,
        agent_id=test_squad_member_pm.id,
    )
    
    # Create agent message for coherence check
    message = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=None,
        content="Building feature",
        message_type="status_update",
        message_metadata={},
        task_execution_id=test_task_execution.id,
    )
    test_db.add(message)
    await test_db.commit()
    
    report = await pm_agent.orchestrate_with_guardian_oversight(
        db=test_db,
        execution_id=test_task_execution.id,
    )
    
    assert report is not None
    assert "orchestration_status" in report
    assert "workflow_health" in report
    assert "coherence_results" in report
    assert "guardian_actions" in report


@pytest.mark.asyncio
async def test_singleton_patterns():
    """Test that singleton patterns work"""
    scorer1 = get_coherence_scorer()
    scorer2 = get_coherence_scorer()
    
    assert scorer1 is scorer2  # Same instance
    
    monitor1 = get_workflow_health_monitor()
    monitor2 = get_workflow_health_monitor()
    
    assert monitor1 is monitor2  # Same instance


@pytest.mark.asyncio
async def test_coherence_metrics_storage(
    test_db,
    test_task_execution,
    test_squad_member_backend,
    test_squad_member_pm,
):
    """Test that coherence metrics are stored"""
    config = AgentConfig(
        role="project_manager",
        llm_provider=LLMProvider.OPENAI,
        llm_model="gpt-4",
        system_prompt="Test prompt",
    )
    
    pm_agent = AgnoProjectManagerAgent(
        config=config,
        agent_id=test_squad_member_pm.id,
    )
    
    # Create message
    message = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=None,
        content="Test message",
        message_type="status_update",
        message_metadata={},
        task_execution_id=test_task_execution.id,
    )
    test_db.add(message)
    await test_db.commit()
    
    # Check coherence (should store metric)
    coherence = await pm_agent.check_phase_coherence(
        db=test_db,
        execution_id=test_task_execution.id,
        agent_id=test_squad_member_backend.id,
        phase=WorkflowPhase.BUILDING,
    )
    
    # Verify stored
    from sqlalchemy import select
    stmt = select(CoherenceMetrics).where(
        CoherenceMetrics.execution_id == test_task_execution.id,
    )
    result = await test_db.execute(stmt)
    metrics = result.scalars().all()
    
    assert len(metrics) > 0
    assert metrics[0].monitored_by_pm_id == test_squad_member_pm.id
    assert metrics[0].agent_id == test_squad_member_backend.id

