"""
Tests for Branching Engine (Stream E)

Comprehensive tests for workflow branching functionality.
"""
import pytest
from uuid import uuid4
from datetime import datetime

from backend.agents.branching.branching_engine import BranchingEngine, get_branching_engine
from backend.agents.discovery.discovery_engine import Discovery
from backend.models.workflow import WorkflowPhase
from backend.models.branching import WorkflowBranch
from backend.models.workflow import DynamicTask


@pytest.mark.asyncio
async def test_branching_engine_initialization():
    """Test BranchingEngine initialization"""
    engine = BranchingEngine()
    
    assert engine is not None
    assert engine.workflow_engine is not None


@pytest.mark.asyncio
async def test_get_branching_engine_singleton():
    """Test that get_branching_engine returns singleton"""
    engine1 = get_branching_engine()
    engine2 = get_branching_engine()
    
    assert engine1 is engine2  # Same instance


@pytest.mark.asyncio
async def test_create_branch_from_discovery(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test creating a branch from a discovery"""
    engine = BranchingEngine()
    
    discovery = Discovery(
        type="optimization",
        description="Caching pattern could apply to 12 routes for 40% speedup",
        value_score=0.7,
        suggested_phase=WorkflowPhase.INVESTIGATION,
        confidence=0.8,
        context={},
    )
    
    branch = await engine.create_branch_from_discovery(
        db=test_db,
        execution_id=test_task_execution.id,
        discovery=discovery,
        branch_name="Optimization Branch",
        initial_task_title="Analyze caching pattern",
        initial_task_description="Investigate caching optimization opportunity",
        agent_id=test_squad_member_backend.id,
    )
    
    assert branch is not None
    assert branch.id is not None
    assert branch.parent_execution_id == test_task_execution.id
    assert branch.branch_phase == "investigation"
    assert branch.discovery_origin_type == "optimization"
    assert branch.status == "active"
    assert "discovery_value_score" in branch.branch_metadata


@pytest.mark.asyncio
async def test_get_branches_for_execution(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test getting branches for an execution"""
    engine = BranchingEngine()
    
    # Create a branch
    discovery = Discovery(
        type="bug",
        description="Security vulnerability found",
        value_score=0.9,
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
    branches = await engine.get_branches_for_execution(
        db=test_db,
        execution_id=test_task_execution.id,
    )
    
    assert len(branches) >= 1
    assert any(b.id == branch.id for b in branches)


@pytest.mark.asyncio
async def test_get_branches_filtered_by_status(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test getting branches filtered by status"""
    engine = BranchingEngine()
    
    # Create branch
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
    
    # Get only active branches
    active_branches = await engine.get_branches_for_execution(
        db=test_db,
        execution_id=test_task_execution.id,
        status="active",
    )
    
    assert len(active_branches) >= 1
    assert all(b.status == "active" for b in active_branches)


@pytest.mark.asyncio
async def test_get_branch_tasks(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test getting tasks in a branch"""
    engine = BranchingEngine()
    
    # Create branch with initial task
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
        initial_task_description="Test task",
        agent_id=test_squad_member_backend.id,
    )
    
    # Get branch tasks
    tasks = await engine.get_branch_tasks(db=test_db, branch_id=branch.id)
    
    assert len(tasks) >= 1
    assert all(t.branch_id == branch.id for t in tasks)


@pytest.mark.asyncio
async def test_merge_branch(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test merging a branch"""
    engine = BranchingEngine()
    
    # Create branch
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
    merged = await engine.merge_branch(
        db=test_db,
        branch_id=branch.id,
        merge_summary="Optimization implemented successfully",
    )
    
    assert merged.status == "merged"
    assert "merge_summary" in merged.branch_metadata


@pytest.mark.asyncio
async def test_abandon_branch(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test abandoning a branch"""
    engine = BranchingEngine()
    
    # Create branch
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
    
    # Abandon branch
    abandoned = await engine.abandon_branch(
        db=test_db,
        branch_id=branch.id,
        reason="Not needed anymore",
    )
    
    assert abandoned.status == "abandoned"
    assert "abandon_reason" in abandoned.branch_metadata


@pytest.mark.asyncio
async def test_complete_branch(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test completing a branch"""
    engine = BranchingEngine()
    
    # Create branch with completed task
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
        initial_task_title="Complete this",
        initial_task_description="Task to complete",
        agent_id=test_squad_member_backend.id,
    )
    
    # Complete the task
    tasks = await engine.get_branch_tasks(db=test_db, branch_id=branch.id)
    if tasks:
        from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
        workflow_engine = PhaseBasedWorkflowEngine()
        await workflow_engine.update_task_status(
            db=test_db,
            task_id=tasks[0].id,
            new_status="completed",
        )
    
    # Complete branch
    completed = await engine.complete_branch(
        db=test_db,
        branch_id=branch.id,
    )
    
    assert completed.status == "completed"


@pytest.mark.asyncio
async def test_complete_branch_with_incomplete_tasks_fails(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test that completing branch with incomplete tasks fails"""
    engine = BranchingEngine()
    
    # Create branch with task
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
        initial_task_title="Incomplete task",
        initial_task_description="This task is not done",
        agent_id=test_squad_member_backend.id,
    )
    
    # Try to complete branch (should fail)
    with pytest.raises(ValueError, match="incomplete"):
        await engine.complete_branch(
            db=test_db,
            branch_id=branch.id,
        )


@pytest.mark.asyncio
async def test_merge_inactive_branch_fails(
    test_db,
    test_task_execution,
    test_squad_member_backend,
):
    """Test that merging non-active branch fails"""
    engine = BranchingEngine()
    
    # Create and abandon branch
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
    
    await engine.abandon_branch(db=test_db, branch_id=branch.id)
    
    # Try to merge abandoned branch (should fail)
    with pytest.raises(ValueError, match="not active"):
        await engine.merge_branch(
            db=test_db,
            branch_id=branch.id,
        )

