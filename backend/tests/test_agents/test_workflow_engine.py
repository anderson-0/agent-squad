"""
Tests for WorkflowEngine - Task Execution State Machine
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Mock problematic imports before importing WorkflowEngine
import sys
sys.modules['backend.database'] = MagicMock()
sys.modules['backend.models.agent'] = MagicMock()
mock_pinecone = MagicMock()
mock_pinecone.Pinecone = MagicMock()
mock_pinecone.ServerlessSpec = MagicMock()
sys.modules['pinecone'] = mock_pinecone

from backend.agents.orchestration.workflow_engine import WorkflowEngine, WorkflowState


@pytest.mark.asyncio
async def test_init():
    """Test WorkflowEngine initialization"""
    engine = WorkflowEngine()

    assert engine._state_actions == {}


@pytest.mark.asyncio
async def test_register_state_action():
    """Test registering a state action"""
    engine = WorkflowEngine()

    async def mock_action(db, execution_id, metadata):
        pass

    engine.register_state_action(WorkflowState.PLANNING, mock_action)

    assert WorkflowState.PLANNING in engine._state_actions
    assert engine._state_actions[WorkflowState.PLANNING] == mock_action


@pytest.mark.asyncio
async def test_is_valid_transition_success():
    """Test valid state transition check"""
    engine = WorkflowEngine()

    # Valid: PENDING -> ANALYZING
    assert engine.is_valid_transition(WorkflowState.PENDING, WorkflowState.ANALYZING) is True

    # Valid: ANALYZING -> PLANNING
    assert engine.is_valid_transition(WorkflowState.ANALYZING, WorkflowState.PLANNING) is True

    # Valid: IN_PROGRESS -> COMPLETED
    assert engine.is_valid_transition(WorkflowState.IN_PROGRESS, WorkflowState.COMPLETED) is True


@pytest.mark.asyncio
async def test_is_valid_transition_failure():
    """Test invalid state transition check"""
    engine = WorkflowEngine()

    # Invalid: PENDING -> COMPLETED
    assert engine.is_valid_transition(WorkflowState.PENDING, WorkflowState.COMPLETED) is False

    # Invalid: COMPLETED -> IN_PROGRESS (terminal state)
    assert engine.is_valid_transition(WorkflowState.COMPLETED, WorkflowState.IN_PROGRESS) is False

    # Invalid: ANALYZING -> IN_PROGRESS
    assert engine.is_valid_transition(WorkflowState.ANALYZING, WorkflowState.IN_PROGRESS) is False


@pytest.mark.asyncio
async def test_get_valid_transitions():
    """Test getting valid transitions for a state"""
    engine = WorkflowEngine()

    # PENDING can go to ANALYZING or FAILED
    valid = engine.get_valid_transitions(WorkflowState.PENDING)
    assert WorkflowState.ANALYZING in valid
    assert WorkflowState.FAILED in valid
    assert len(valid) == 2

    # COMPLETED has no valid transitions (terminal)
    valid = engine.get_valid_transitions(WorkflowState.COMPLETED)
    assert len(valid) == 0


@pytest.mark.asyncio
async def test_transition_state_success():
    """Test successful state transition"""
    engine = WorkflowEngine()
    execution_id = uuid4()

    with patch('backend.agents.orchestration.workflow_engine.TaskExecutionService') as mock_service:
        mock_service.update_execution_status = AsyncMock()

        success = await engine.transition_state(
            db=AsyncMock(),
            execution_id=execution_id,
            from_state=WorkflowState.PENDING,
            to_state=WorkflowState.ANALYZING,
            reason="Starting analysis",
        )

        assert success is True
        mock_service.update_execution_status.assert_called_once()
        call_args = mock_service.update_execution_status.call_args[1]
        assert call_args["execution_id"] == execution_id
        assert call_args["status"] == WorkflowState.ANALYZING.value
        assert "Starting analysis" in call_args["log_message"]


@pytest.mark.asyncio
async def test_transition_state_invalid():
    """Test invalid state transition raises error"""
    engine = WorkflowEngine()
    execution_id = uuid4()

    with pytest.raises(ValueError, match="Invalid transition"):
        await engine.transition_state(
            db=AsyncMock(),
            execution_id=execution_id,
            from_state=WorkflowState.PENDING,
            to_state=WorkflowState.COMPLETED,  # Invalid jump
        )


@pytest.mark.asyncio
async def test_transition_state_with_metadata():
    """Test state transition with metadata"""
    engine = WorkflowEngine()
    execution_id = uuid4()

    with patch('backend.agents.orchestration.workflow_engine.TaskExecutionService') as mock_service:
        mock_service.update_execution_status = AsyncMock()
        mock_service.add_log = AsyncMock()

        metadata = {"plan_id": "123", "complexity": 5}

        await engine.transition_state(
            db=AsyncMock(),
            execution_id=execution_id,
            from_state=WorkflowState.ANALYZING,
            to_state=WorkflowState.PLANNING,
            metadata=metadata,
        )

        # Verify metadata was logged
        mock_service.add_log.assert_called_once()
        call_args = mock_service.add_log.call_args[1]
        assert call_args["execution_id"] == execution_id
        assert "plan_id" in call_args["metadata"]
        assert call_args["metadata"]["plan_id"] == "123"


@pytest.mark.asyncio
async def test_transition_state_executes_action():
    """Test state transition executes registered action"""
    engine = WorkflowEngine()
    execution_id = uuid4()

    # Register action for PLANNING state
    action_called = False
    received_metadata = {}

    async def mock_action(db, exec_id, metadata):
        nonlocal action_called, received_metadata
        action_called = True
        received_metadata = metadata

    engine.register_state_action(WorkflowState.PLANNING, mock_action)

    with patch('backend.agents.orchestration.workflow_engine.TaskExecutionService') as mock_service:
        mock_service.update_execution_status = AsyncMock()
        mock_service.add_log = AsyncMock()

        metadata = {"test": "data"}

        await engine.transition_state(
            db=AsyncMock(),
            execution_id=execution_id,
            from_state=WorkflowState.ANALYZING,
            to_state=WorkflowState.PLANNING,
            metadata=metadata,
        )

        # Verify action was called
        assert action_called is True
        assert received_metadata == metadata


@pytest.mark.asyncio
async def test_execute_state_actions():
    """Test executing state actions"""
    engine = WorkflowEngine()
    execution_id = uuid4()

    action_result = {"result": "success"}

    async def mock_action(db, exec_id, context):
        return action_result

    engine.register_state_action(WorkflowState.IN_PROGRESS, mock_action)

    # Test action execution
    result = await engine.execute_state_actions(
        db=AsyncMock(),
        execution_id=execution_id,
        state=WorkflowState.IN_PROGRESS,
        context={"data": "test"},
    )

    assert result == action_result


@pytest.mark.asyncio
async def test_execute_state_actions_no_action():
    """Test executing state with no registered action"""
    engine = WorkflowEngine()
    execution_id = uuid4()

    # No action registered for PENDING
    result = await engine.execute_state_actions(
        db=AsyncMock(),
        execution_id=execution_id,
        state=WorkflowState.PENDING,
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_workflow_progress_completed():
    """Test workflow progress for completed state"""
    engine = WorkflowEngine()

    progress = engine.get_workflow_progress(WorkflowState.COMPLETED)

    assert progress["state"] == "completed"
    assert progress["progress_percentage"] == 100
    assert progress["is_terminal"] is True
    assert progress["is_blocked"] is False


@pytest.mark.asyncio
async def test_get_workflow_progress_failed():
    """Test workflow progress for failed state"""
    engine = WorkflowEngine()

    progress = engine.get_workflow_progress(WorkflowState.FAILED)

    assert progress["state"] == "failed"
    assert progress["progress_percentage"] == 0
    assert progress["is_terminal"] is True
    assert progress["is_blocked"] is False


@pytest.mark.asyncio
async def test_get_workflow_progress_blocked():
    """Test workflow progress for blocked state"""
    engine = WorkflowEngine()

    progress = engine.get_workflow_progress(WorkflowState.BLOCKED)

    assert progress["state"] == "blocked"
    assert progress["progress_percentage"] == 50
    assert progress["is_terminal"] is False
    assert progress["is_blocked"] is True


@pytest.mark.asyncio
async def test_get_workflow_progress_in_progress():
    """Test workflow progress calculation for active states"""
    engine = WorkflowEngine()

    # Test various states
    progress = engine.get_workflow_progress(WorkflowState.ANALYZING)
    assert progress["progress_percentage"] > 0
    assert progress["progress_percentage"] < 100
    assert progress["is_terminal"] is False
    assert progress["is_blocked"] is False

    # IN_PROGRESS should be further along
    progress_in_prog = engine.get_workflow_progress(WorkflowState.IN_PROGRESS)
    progress_analyzing = engine.get_workflow_progress(WorkflowState.ANALYZING)
    assert progress_in_prog["progress_percentage"] > progress_analyzing["progress_percentage"]


@pytest.mark.asyncio
async def test_get_state_description():
    """Test getting state descriptions"""
    engine = WorkflowEngine()

    desc = engine.get_state_description(WorkflowState.PENDING)
    assert "queued" in desc.lower()

    desc = engine.get_state_description(WorkflowState.ANALYZING)
    assert "analyzing" in desc.lower() or "manager" in desc.lower()

    desc = engine.get_state_description(WorkflowState.COMPLETED)
    assert "completed" in desc.lower() or "success" in desc.lower()


@pytest.mark.asyncio
async def test_get_workflow_metrics_empty():
    """Test workflow metrics with empty history"""
    engine = WorkflowEngine()

    metrics = engine.get_workflow_metrics([])

    assert metrics["total_transitions"] == 0
    assert metrics["time_in_each_state"] == {}
    assert metrics["total_duration_seconds"] == 0


@pytest.mark.asyncio
async def test_get_workflow_metrics():
    """Test workflow metrics calculation"""
    engine = WorkflowEngine()

    # Create fake state history
    base_time = datetime(2025, 10, 13, 10, 0, 0)

    state_history = [
        {
            "state": "pending",
            "timestamp": base_time.isoformat(),
        },
        {
            "state": "analyzing",
            "timestamp": base_time.replace(minute=5).isoformat(),  # 5 min later
        },
        {
            "state": "planning",
            "timestamp": base_time.replace(minute=15).isoformat(),  # 10 min later
        },
        {
            "state": "in_progress",
            "timestamp": base_time.replace(minute=45).isoformat(),  # 30 min later
        },
    ]

    metrics = engine.get_workflow_metrics(state_history)

    assert metrics["total_transitions"] == 4
    assert "time_in_each_state_seconds" in metrics

    # Verify time calculations
    time_in_states = metrics["time_in_each_state_seconds"]
    assert time_in_states["pending"] == 300  # 5 minutes
    assert time_in_states["analyzing"] == 600  # 10 minutes
    assert time_in_states["planning"] == 1800  # 30 minutes

    # Total duration should be 45 minutes (2700 seconds)
    assert metrics["total_duration_seconds"] == 2700

    # Average time per state
    assert metrics["average_time_per_state_seconds"] == 2700 / 4


@pytest.mark.asyncio
async def test_workflow_complete_path():
    """Test complete workflow path"""
    engine = WorkflowEngine()

    # Test typical happy path transitions
    assert engine.is_valid_transition(WorkflowState.PENDING, WorkflowState.ANALYZING)
    assert engine.is_valid_transition(WorkflowState.ANALYZING, WorkflowState.PLANNING)
    assert engine.is_valid_transition(WorkflowState.PLANNING, WorkflowState.DELEGATED)
    assert engine.is_valid_transition(WorkflowState.DELEGATED, WorkflowState.IN_PROGRESS)
    assert engine.is_valid_transition(WorkflowState.IN_PROGRESS, WorkflowState.REVIEWING)
    assert engine.is_valid_transition(WorkflowState.REVIEWING, WorkflowState.TESTING)
    assert engine.is_valid_transition(WorkflowState.TESTING, WorkflowState.COMPLETED)


@pytest.mark.asyncio
async def test_workflow_failure_path():
    """Test workflow failure transitions"""
    engine = WorkflowEngine()

    # Any state can transition to FAILED
    assert engine.is_valid_transition(WorkflowState.ANALYZING, WorkflowState.FAILED)
    assert engine.is_valid_transition(WorkflowState.PLANNING, WorkflowState.FAILED)
    assert engine.is_valid_transition(WorkflowState.IN_PROGRESS, WorkflowState.FAILED)


@pytest.mark.asyncio
async def test_workflow_blocked_and_recovery():
    """Test blocked state and recovery paths"""
    engine = WorkflowEngine()

    # Can transition to BLOCKED from several states
    assert engine.is_valid_transition(WorkflowState.ANALYZING, WorkflowState.BLOCKED)
    assert engine.is_valid_transition(WorkflowState.PLANNING, WorkflowState.BLOCKED)
    assert engine.is_valid_transition(WorkflowState.IN_PROGRESS, WorkflowState.BLOCKED)

    # Can recover from BLOCKED
    assert engine.is_valid_transition(WorkflowState.BLOCKED, WorkflowState.ANALYZING)
    assert engine.is_valid_transition(WorkflowState.BLOCKED, WorkflowState.PLANNING)
    assert engine.is_valid_transition(WorkflowState.BLOCKED, WorkflowState.IN_PROGRESS)


@pytest.mark.asyncio
async def test_workflow_review_feedback_loop():
    """Test review feedback loop"""
    engine = WorkflowEngine()

    # Reviewing can send back to IN_PROGRESS for changes
    assert engine.is_valid_transition(WorkflowState.REVIEWING, WorkflowState.IN_PROGRESS)

    # Testing can also send back for bug fixes
    assert engine.is_valid_transition(WorkflowState.TESTING, WorkflowState.IN_PROGRESS)

    # Testing can request re-review
    assert engine.is_valid_transition(WorkflowState.TESTING, WorkflowState.REVIEWING)
