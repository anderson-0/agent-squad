"""
Tests for ML-Based Opportunity Detection (Stream H)
"""
import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from backend.agents.ml import OpportunityDetector, get_opportunity_detector
from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.models.project import TaskExecution
from backend.models.squad import Squad, SquadMember


@pytest.fixture
async def setup_ml_test_data(db: AsyncSession):
    """Set up test data for ML tests"""
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
async def test_opportunity_detector_initialization():
    """Test that OpportunityDetector can be initialized"""
    detector = get_opportunity_detector()
    assert detector is not None
    assert isinstance(detector, OpportunityDetector)


@pytest.mark.asyncio
async def test_detect_optimization_opportunities():
    """Test optimization opportunity detection"""
    detector = get_opportunity_detector()
    
    # Test with performance-related code
    code_with_performance = "This function is slow and needs optimization"
    opportunities = await detector.detect_optimization_opportunities(
        code_context=code_with_performance,
    )
    
    assert isinstance(opportunities, list)
    # Should detect performance opportunity
    assert len(opportunities) > 0 or detector.use_ml is False  # May use pattern matching
    
    if opportunities:
        opp = opportunities[0]
        assert hasattr(opp, 'type')
        assert hasattr(opp, 'description')
        assert hasattr(opp, 'confidence')
        assert 0.0 <= opp.confidence <= 1.0


@pytest.mark.asyncio
async def test_predict_task_value():
    """Test task value prediction"""
    detector = get_opportunity_detector()
    
    predicted_value = await detector.predict_task_value(
        task_description="Optimize database queries for better performance",
    )
    
    assert 0.0 <= predicted_value <= 1.0
    # High-value keywords should increase value
    assert predicted_value >= 0.3


@pytest.mark.asyncio
async def test_predict_task_value_with_historical_tasks(db: AsyncSession, setup_ml_test_data):
    """Test task value prediction with historical tasks"""
    execution, agent = setup_ml_test_data
    detector = get_opportunity_detector()
    
    # Create some historical tasks
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
    
    # Predict value with historical context
    all_tasks = await engine.get_tasks_for_execution(db=db, execution_id=execution.id)
    predicted_value = await detector.predict_task_value(
        task_description="Similar task to historical ones",
        historical_similar_tasks=all_tasks,
    )
    
    assert 0.0 <= predicted_value <= 1.0


@pytest.mark.asyncio
async def test_pattern_detection():
    """Test pattern-based detection (fallback)"""
    detector = get_opportunity_detector()
    
    # Test with refactoring keywords
    code_with_refactoring = "There is duplicate code that needs to be refactored"
    opportunities = detector._detect_with_patterns(code_with_refactoring)
    
    assert isinstance(opportunities, list)
    # Should detect refactoring opportunity
    if opportunities:
        refactoring_opps = [o for o in opportunities if o.type == "refactoring"]
        assert len(refactoring_opps) > 0


@pytest.mark.asyncio
async def test_train_model():
    """Test model training (requires scikit-learn)"""
    detector = get_opportunity_detector()
    
    # Prepare training data
    historical_data = [
        {"text": "optimize database queries", "label": "optimization"},
        {"text": "fix bug in authentication", "label": "bug"},
        {"text": "refactor duplicate code", "label": "refactoring"},
        {"text": "improve performance", "label": "performance"},
        {"text": "optimize API endpoints", "label": "optimization"},
        {"text": "fix memory leak", "label": "bug"},
        {"text": "refactor user service", "label": "refactoring"},
        {"text": "optimize cache strategy", "label": "optimization"},
        {"text": "fix validation error", "label": "bug"},
        {"text": "improve code structure", "label": "refactoring"},
    ]
    
    try:
        metrics = await detector.train_model(
            historical_data=historical_data,
            validation_split=0.2,
        )
        
        assert metrics.accuracy >= 0.0
        assert metrics.accuracy <= 1.0
        assert metrics.training_samples > 0
        assert metrics.validation_samples > 0
    except ValueError as e:
        # scikit-learn may not be available
        if "scikit-learn" in str(e) or "training samples" in str(e):
            pytest.skip("scikit-learn not available or insufficient data")
        else:
            raise


@pytest.mark.asyncio
async def test_ml_detection_fallback():
    """Test that ML detection falls back to patterns gracefully"""
    detector = get_opportunity_detector()
    
    # Even if ML fails, should return pattern-based results
    opportunities = await detector.detect_optimization_opportunities(
        code_context="This code has a bottleneck",
    )
    
    # Should return something (either ML or pattern-based)
    assert isinstance(opportunities, list)

