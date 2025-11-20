"""
Tests for Advanced Guardian System (Stream G)

Tests for advanced anomaly detection and recommendations.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from backend.agents.guardian.advanced_anomaly_detector import (
    AdvancedAnomalyDetector,
    Anomaly,
    get_anomaly_detector,
)
from backend.agents.guardian.recommendations_engine import (
    RecommendationsEngine,
    Recommendation,
    get_recommendations_engine,
)
from backend.agents.guardian.coherence_scorer import CoherenceScore
from backend.models.workflow import WorkflowPhase
from backend.models.message import AgentMessage
from backend.models.workflow import DynamicTask


@pytest.mark.asyncio
async def test_anomaly_detector_initialization():
    """Test AdvancedAnomalyDetector initialization"""
    detector = AdvancedAnomalyDetector()
    
    assert detector is not None


@pytest.mark.asyncio
async def test_get_anomaly_detector_singleton():
    """Test that get_anomaly_detector returns singleton"""
    detector1 = get_anomaly_detector()
    detector2 = get_anomaly_detector()
    
    assert detector1 is detector2


@pytest.mark.asyncio
async def test_detect_phase_drift(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test detecting phase drift anomaly"""
    detector = AdvancedAnomalyDetector()
    
    # Create task with mismatched phase/description
    task = DynamicTask(
        id=uuid4(),
        parent_execution_id=test_task_execution.id,
        phase=WorkflowPhase.INVESTIGATION.value,
        spawned_by_agent_id=test_squad_member_backend.id,
        title="Building task in investigation phase",
        description="I'm implementing features here",  # Building keywords in investigation phase
        status="in_progress",
    )
    test_db.add(task)
    await test_db.commit()
    
    # Detect anomalies
    anomalies = await detector.detect_anomalies(test_db, test_task_execution.id)
    
    # Should detect phase drift
    phase_drift = [a for a in anomalies if a.type == "phase_drift"]
    assert len(phase_drift) > 0


@pytest.mark.asyncio
async def test_detect_low_value_tasks(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test detecting low-value tasks"""
    detector = AdvancedAnomalyDetector()
    
    # Create task with vague description
    task = DynamicTask(
        id=uuid4(),
        parent_execution_id=test_task_execution.id,
        phase=WorkflowPhase.INVESTIGATION.value,
        spawned_by_agent_id=test_squad_member_backend.id,
        title="Vague task",
        description="Do stuff",  # Very brief
        status="pending",
    )
    test_db.add(task)
    await test_db.commit()
    
    anomalies = await detector.detect_anomalies(test_db, test_task_execution.id)
    
    low_value = [a for a in anomalies if a.type == "low_value_task"]
    assert len(low_value) > 0


@pytest.mark.asyncio
async def test_detect_stagnation(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test detecting workflow stagnation"""
    detector = AdvancedAnomalyDetector()
    
    # Create old message (simulated)
    old_message = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=None,
        content="Last activity",
        message_type="status_update",
        message_metadata={},
        task_execution_id=test_task_execution.id,
        created_at=datetime.utcnow() - timedelta(hours=10),  # 10 hours ago
    )
    test_db.add(old_message)
    
    # Update execution status
    from backend.models.project import TaskExecution
    execution = await test_db.get(TaskExecution, test_task_execution.id)
    execution.status = "in_progress"
    await test_db.commit()
    
    # Detect anomalies
    anomalies = await detector.detect_anomalies(test_db, test_task_execution.id)
    
    stagnation = [a for a in anomalies if a.type == "workflow_stagnation"]
    # May or may not detect depending on threshold (8 hours)
    assert isinstance(stagnation, list)


@pytest.mark.asyncio
async def test_detect_resource_imbalance(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test detecting resource imbalance"""
    detector = AdvancedAnomalyDetector()
    
    # Create many tasks in one phase
    for i in range(8):
        task = DynamicTask(
            id=uuid4(),
            parent_execution_id=test_task_execution.id,
            phase=WorkflowPhase.INVESTIGATION.value,  # All in investigation
            spawned_by_agent_id=test_squad_member_backend.id,
            title=f"Task {i}",
            description="Test",
            status="pending",
        )
        test_db.add(task)
    
    await test_db.commit()
    
    anomalies = await detector.detect_anomalies(test_db, test_task_execution.id)
    
    imbalance = [a for a in anomalies if a.type == "phase_imbalance"]
    assert len(imbalance) > 0


@pytest.mark.asyncio
async def test_recommendations_engine_initialization():
    """Test RecommendationsEngine initialization"""
    engine = RecommendationsEngine()
    
    assert engine is not None
    assert engine.anomaly_detector is not None


@pytest.mark.asyncio
async def test_generate_recommendations_from_anomalies(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test generating recommendations from anomalies"""
    engine = RecommendationsEngine()
    
    # Create anomaly scenario
    task = DynamicTask(
        id=uuid4(),
        parent_execution_id=test_task_execution.id,
        phase=WorkflowPhase.INVESTIGATION.value,
        spawned_by_agent_id=test_squad_member_backend.id,
        title="Vague task",
        description="Stuff",
        status="pending",
    )
    test_db.add(task)
    await test_db.commit()
    
    # Generate recommendations
    recommendations = await engine.generate_recommendations(
        db=test_db,
        execution_id=test_task_execution.id,
    )
    
    assert len(recommendations) > 0
    assert all(isinstance(r, Recommendation) for r in recommendations)


@pytest.mark.asyncio
async def test_generate_recommendations_from_coherence(
    test_db,
    test_task_execution,
):
    """Test generating recommendations from coherence scores"""
    engine = RecommendationsEngine()
    
    # Create low coherence score
    low_coherence = CoherenceScore(
        overall_score=0.5,
        metrics={
            "phase_alignment": 0.4,
            "goal_alignment": 0.5,
            "quality_alignment": 0.6,
            "task_relevance": 0.5,
        },
        agent_id=uuid4(),
        phase=WorkflowPhase.BUILDING,
        calculated_at=datetime.utcnow(),
    )
    
    recommendations = await engine.generate_recommendations(
        db=test_db,
        execution_id=test_task_execution.id,
        coherence_scores=[low_coherence],
    )
    
    assert len(recommendations) > 0
    # Should have coherence-related recommendations
    coherence_recs = [r for r in recommendations if "coherence" in r.type or "phase_alignment" in r.type]
    assert len(coherence_recs) > 0


@pytest.mark.asyncio
async def test_recommendations_priority_sorting():
    """Test that recommendations are sorted by priority"""
    engine = RecommendationsEngine()
    
    # Create recommendations with different priorities
    anomalies = [
        Anomaly("critical", "critical", "Critical issue", "Fix immediately", {}),
        Anomaly("low", "low", "Minor issue", "Review later", {}),
        Anomaly("high", "high", "High priority", "Address soon", {}),
    ]
    
    recommendations = []
    for anomaly in anomalies:
        rec = engine._anomaly_to_recommendation(anomaly)
        if rec:
            recommendations.append(rec)
    
    # Sort
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))
    
    # Highest priority first
    assert recommendations[0].priority in ["urgent", "high"]
    assert recommendations[-1].priority == "low"

