"""
Branching Engine for Stream E

Manages workflow branches spawned from discoveries.
Enables parallel investigation/optimization tracks.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.workflow import WorkflowPhase, DynamicTask
from backend.models.branching import WorkflowBranch
from backend.models.project import TaskExecution
from backend.agents.discovery.discovery_engine import Discovery
from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
from backend.core.logging import logger


class BranchingEngine:
    """
    Engine for managing workflow branches.
    
    Branches are created when agents discover opportunities or issues
    that warrant parallel investigation/optimization tracks.
    """
    
    def __init__(self):
        """Initialize branching engine"""
        self.workflow_engine = PhaseBasedWorkflowEngine()
    
    async def create_branch_from_discovery(
        self,
        db: AsyncSession,
        execution_id: UUID,
        discovery: Discovery,
        branch_name: Optional[str] = None,
        initial_task_title: Optional[str] = None,
        initial_task_description: Optional[str] = None,
        agent_id: UUID = None,
    ) -> WorkflowBranch:
        """
        Create a new workflow branch from a discovery.
        
        This enables Hephaestus-style branching where discoveries
        lead to parallel investigation tracks.
        
        Args:
            db: Database session
            execution_id: Parent task execution
            discovery: Discovery that triggered the branch
            branch_name: Optional custom branch name
            initial_task_title: Title for initial branch task
            initial_task_description: Description for initial branch task
            agent_id: Agent creating the branch
            
        Returns:
            Created WorkflowBranch
            
        Raises:
            ValueError: If execution doesn't exist
        """
        # Validate execution exists
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")
        
        # Generate branch name if not provided
        if not branch_name:
            branch_name = f"{discovery.type.title()} Branch: {discovery.description[:50]}"
        
        # Get suggested phase from discovery
        branch_phase = discovery.suggested_phase.value if discovery.suggested_phase else WorkflowPhase.INVESTIGATION.value
        
        # Create branch
        branch = WorkflowBranch(
            parent_execution_id=execution_id,
            branch_name=branch_name,
            branch_phase=branch_phase,
            discovery_origin_type=discovery.type,
            discovery_description=discovery.description,
            status="active",
            branch_metadata={
                "discovery_value_score": discovery.value_score,
                "discovery_confidence": discovery.confidence,
                "discovery_context": discovery.context,
            },
        )
        
        db.add(branch)
        await db.flush()  # Get the ID
        
        # Create initial task in the branch if provided
        if initial_task_title and initial_task_description and agent_id:
            initial_task = await self.workflow_engine.spawn_task(
                db=db,
                agent_id=agent_id,
                execution_id=execution_id,
                phase=discovery.suggested_phase or WorkflowPhase.INVESTIGATION,
                title=initial_task_title,
                description=initial_task_description,
                rationale=f"Initial task for branch created from {discovery.type} discovery",
            )
            
            # Associate task with branch
            initial_task.branch_id = branch.id
            await db.commit()
        else:
            await db.commit()
        
        await db.refresh(branch)
        
        logger.info(
            f"Created workflow branch: {branch.id} "
            f"(execution={execution_id}, phase={branch_phase}, discovery={discovery.type})"
        )
        
        return branch
    
    async def get_branches_for_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        status: Optional[str] = None,
    ) -> List[WorkflowBranch]:
        """
        Get all branches for an execution.
        
        Args:
            db: Database session
            execution_id: Task execution ID
            status: Optional status filter (active, merged, abandoned, completed)
            
        Returns:
            List of WorkflowBranch instances
        """
        query = select(WorkflowBranch).where(
            WorkflowBranch.parent_execution_id == execution_id
        )
        
        if status:
            query = query.where(WorkflowBranch.status == status)
        
        query = query.order_by(WorkflowBranch.created_at)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_branch_tasks(
        self,
        db: AsyncSession,
        branch_id: UUID,
    ) -> List[DynamicTask]:
        """
        Get all tasks in a branch.
        
        Args:
            db: Database session
            branch_id: Branch ID
            
        Returns:
            List of DynamicTask instances in the branch
        """
        from sqlalchemy import select
        
        query = select(DynamicTask).where(
            DynamicTask.branch_id == branch_id
        ).order_by(DynamicTask.created_at)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def merge_branch(
        self,
        db: AsyncSession,
        branch_id: UUID,
        merge_summary: Optional[str] = None,
    ) -> WorkflowBranch:
        """
        Merge a branch back into the parent workflow.
        
        This marks the branch as merged and optionally creates
        a summary task or updates parent tasks with branch results.
        
        Args:
            db: Database session
            branch_id: Branch to merge
            merge_summary: Optional summary of merge results
            
        Returns:
            Updated WorkflowBranch
            
        Raises:
            ValueError: If branch not found
        """
        branch = await db.get(WorkflowBranch, branch_id)
        if not branch:
            raise ValueError(f"Workflow branch {branch_id} not found")
        
        if branch.status != "active":
            raise ValueError(f"Branch {branch_id} is not active (status: {branch.status})")
        
        # Update branch status
        branch.status = "merged"
        
        # Add merge summary to metadata
        if merge_summary:
            branch.branch_metadata["merge_summary"] = merge_summary
            branch.branch_metadata["merged_at"] = branch.updated_at.isoformat()
        
        await db.commit()
        await db.refresh(branch)
        
        logger.info(f"Merged workflow branch: {branch_id}")
        
        return branch
    
    async def abandon_branch(
        self,
        db: AsyncSession,
        branch_id: UUID,
        reason: Optional[str] = None,
    ) -> WorkflowBranch:
        """
        Mark a branch as abandoned.
        
        Args:
            db: Database session
            branch_id: Branch to abandon
            reason: Optional reason for abandonment
            
        Returns:
            Updated WorkflowBranch
        """
        branch = await db.get(WorkflowBranch, branch_id)
        if not branch:
            raise ValueError(f"Workflow branch {branch_id} not found")
        
        branch.status = "abandoned"
        
        if reason:
            branch.branch_metadata["abandon_reason"] = reason
        
        await db.commit()
        await db.refresh(branch)
        
        logger.info(f"Abandoned workflow branch: {branch_id}")
        
        return branch
    
    async def complete_branch(
        self,
        db: AsyncSession,
        branch_id: UUID,
    ) -> WorkflowBranch:
        """
        Mark a branch as completed.
        
        Args:
            db: Database session
            branch_id: Branch to complete
            
        Returns:
            Updated WorkflowBranch
        """
        branch = await db.get(WorkflowBranch, branch_id)
        if not branch:
            raise ValueError(f"Workflow branch {branch_id} not found")
        
        # Check if all tasks in branch are completed
        branch_tasks = await self.get_branch_tasks(db, branch_id)
        if branch_tasks:
            incomplete = [t for t in branch_tasks if t.status not in ["completed", "failed"]]
            if incomplete:
                raise ValueError(
                    f"Cannot complete branch {branch_id}: "
                    f"{len(incomplete)} tasks still incomplete"
                )
        
        branch.status = "completed"
        await db.commit()
        await db.refresh(branch)
        
        logger.info(f"Completed workflow branch: {branch_id}")
        
        return branch


# Singleton instance
_branching_engine: Optional[BranchingEngine] = None


def get_branching_engine() -> BranchingEngine:
    """Get or create branching engine instance"""
    global _branching_engine
    if _branching_engine is None:
        _branching_engine = BranchingEngine()
    return _branching_engine

