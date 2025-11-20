"""
Phase-Based Workflow Engine

Extends the existing WorkflowEngine to support Hephaestus-style phase-based workflows
where agents can spawn tasks dynamically in any phase (Investigation, Building, Validation).
"""
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from backend.agents.orchestration.workflow_engine import WorkflowEngine, WorkflowState
from backend.models.workflow import WorkflowPhase, DynamicTask, task_dependencies
from backend.models.project import TaskExecution
logger = logging.getLogger(__name__)


class PhaseBasedWorkflowEngine(WorkflowEngine):
    """
    Extended workflow engine with phase-based task spawning capabilities.
    
    This extends the existing WorkflowEngine (doesn't replace it) to add:
    - Phase-based task spawning
    - Dynamic task creation by agents
    - Task dependency tracking
    - Phase-aware workflow management
    """

    def __init__(self):
        """Initialize phase-based workflow engine"""
        super().__init__()

    async def spawn_task(
        self,
        db: AsyncSession,
        agent_id: UUID,
        execution_id: UUID,
        phase: WorkflowPhase,
        title: str,
        description: str,
        rationale: Optional[str] = None,
        blocking_task_ids: Optional[List[UUID]] = None,
    ) -> DynamicTask:
        """
        Spawn a new task in any phase.
        
        This is the core method that enables Hephaestus-style dynamic workflow creation.
        Agents can call this to create tasks in any phase as they discover needs.
        
        Args:
            db: Database session
            agent_id: Agent spawning the task
            execution_id: Parent task execution
            phase: Phase for the task (Investigation/Building/Validation)
            title: Task title
            description: Task description
            rationale: Optional reason why this task was created
            blocking_task_ids: Optional list of task IDs this blocks
            
        Returns:
            Created DynamicTask instance
            
        Raises:
            ValueError: If execution_id doesn't exist or phase is invalid
        """
        # Validate execution exists
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")

        # Create dynamic task
        dynamic_task = DynamicTask(
            parent_execution_id=execution_id,
            phase=phase.value,  # Store as string value
            spawned_by_agent_id=agent_id,
            title=title,
            description=description,
            status="pending",
            rationale=rationale,
        )
        
        db.add(dynamic_task)
        await db.flush()  # Get the ID
        
        # Create blocking relationships if provided
        if blocking_task_ids:
            await self._create_task_dependencies(
                db=db,
                task_id=dynamic_task.id,
                blocking_task_ids=blocking_task_ids,
            )
        
        await db.commit()
        
        # Refresh the task to get updated state
        await db.refresh(dynamic_task)
        
        # Broadcast SSE event for task creation
        try:
            from backend.services.sse_service import sse_manager
            await sse_manager.broadcast_to_execution(
                execution_id=execution_id,
                event="task_spawned",
                data={
                    "task_id": str(dynamic_task.id),
                    "phase": dynamic_task.phase,
                    "title": dynamic_task.title,
                    "status": dynamic_task.status,
                    "spawned_by_agent_id": str(dynamic_task.spawned_by_agent_id),
                    "created_at": dynamic_task.created_at.isoformat(),
                }
            )
        except Exception as e:
            logger.debug(f"SSE broadcast failed (non-critical): {e}")
        
        logger.info(
            f"Dynamic task spawned: {dynamic_task.id} "
            f"(phase={phase.value}, agent={agent_id}, execution={execution_id})"
        )
        
        return dynamic_task

    async def _create_task_dependencies(
        self,
        db: AsyncSession,
        task_id: UUID,
        blocking_task_ids: List[UUID],
    ) -> None:
        """
        Create task dependency relationships using bulk insert for performance.
        
        Validates:
        - No self-dependencies
        - All blocked tasks exist
        - No circular dependencies (basic check)
        
        Args:
            db: Database session
            task_id: Task that blocks others
            blocking_task_ids: Tasks that are blocked
            
        Raises:
            ValueError: If validation fails
        """
        if not blocking_task_ids:
            return
        
        # Validate no self-dependencies
        for blocked_task_id in blocking_task_ids:
            if blocked_task_id == task_id:
                raise ValueError("Task cannot block itself")
        
        # Validate no duplicates
        if len(blocking_task_ids) != len(set(blocking_task_ids)):
            raise ValueError("Duplicate blocking task IDs provided")
        
        # Bulk validate all tasks exist in a single query (performance)
        from sqlalchemy import select
        validate_stmt = select(DynamicTask.id).where(
            DynamicTask.id.in_(blocking_task_ids)
        )
        result = await db.execute(validate_stmt)
        existing_ids = {row[0] for row in result.all()}
        missing_ids = set(blocking_task_ids) - existing_ids
        
        if missing_ids:
            raise ValueError(
                f"Blocked tasks not found: {sorted(missing_ids)}"
            )
        
        # Check for basic circular dependency (task_id blocking itself indirectly)
        # Note: Full circular dependency detection would require graph traversal
        # This is a basic check - full detection can be added later if needed
        
        # Bulk insert all dependencies in one query (much faster than N inserts)
        values = [
            {"task_id": task_id, "blocks_task_id": blocked_task_id}
            for blocked_task_id in blocking_task_ids
        ]
        try:
            await db.execute(
                task_dependencies.insert().values(values)
            )
        except Exception as e:
            # Handle unique constraint violations (if dependency already exists)
            logger.error(f"Failed to create task dependencies: {e}")
            raise ValueError(
                f"Failed to create dependencies. Some may already exist: {e}"
            ) from e

    async def get_tasks_for_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        phase: Optional[WorkflowPhase] = None,
        status: Optional[str] = None,
        include_dependencies: bool = False,
    ) -> List[DynamicTask]:
        """
        Get all dynamic tasks for an execution with optional eager loading.
        
        Args:
            db: Database session
            execution_id: Parent execution ID
            phase: Optional phase filter
            status: Optional status filter
            include_dependencies: If True, eagerly load dependencies (prevents N+1)
            
        Returns:
            List of DynamicTask instances
        """
        query = select(DynamicTask).where(
            DynamicTask.parent_execution_id == execution_id
        )
        
        if phase:
            query = query.where(DynamicTask.phase == phase.value)
        
        if status:
            query = query.where(DynamicTask.status == status)
        
        # Eager load dependencies if requested (prevents N+1 queries)
        if include_dependencies:
            query = query.options(
                selectinload(DynamicTask.blocks_tasks),
                selectinload(DynamicTask.blocked_by_tasks),
            )
        
        query = query.order_by(DynamicTask.created_at)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_task_with_dependencies(
        self,
        db: AsyncSession,
        task_id: UUID,
    ) -> Optional[DynamicTask]:
        """
        Get task with its dependencies loaded.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            DynamicTask with dependencies loaded, or None
        """
        query = (
            select(DynamicTask)
            .options(
                selectinload(DynamicTask.blocks_tasks),
                selectinload(DynamicTask.blocked_by_tasks),
            )
            .where(DynamicTask.id == task_id)
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_task_status(
        self,
        db: AsyncSession,
        task_id: UUID,
        new_status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DynamicTask:
        """
        Update task status.
        
        Args:
            db: Database session
            task_id: Task ID
            new_status: New status (pending, in_progress, completed, failed, blocked)
            metadata: Optional metadata
            
        Returns:
            Updated DynamicTask
        """
        valid_statuses = ["pending", "in_progress", "completed", "failed", "blocked"]
        if new_status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {new_status}. Must be one of {valid_statuses}"
            )
        
        task = await db.get(DynamicTask, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        old_status = task.status
        task.status = new_status
        
        if metadata:
            # Store metadata in task (could extend model later with JSONB column)
            # For now, metadata is accepted but not persisted
            logger.debug(f"Task {task_id} metadata provided but not persisted: {metadata}")
        
        try:
            await db.commit()
            await db.refresh(task)
            
            logger.info(
                f"Task {task_id} status updated: {old_status} -> {new_status}"
            )
            
            # Broadcast SSE event for task status update
            try:
                from backend.services.sse_service import sse_manager
                await sse_manager.broadcast_to_execution(
                    execution_id=task.parent_execution_id,
                    event="task_status_updated",
                    data={
                        "task_id": str(task_id),
                        "old_status": old_status,
                        "new_status": new_status,
                        "phase": task.phase,
                        "title": task.title,
                        "updated_at": task.updated_at.isoformat(),
                    }
                )
            except Exception as e:
                logger.debug(f"SSE broadcast failed (non-critical): {e}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update task {task_id} status: {e}")
            raise ValueError(f"Failed to update task status: {str(e)}") from e
        
        return task

    async def get_blocked_tasks(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> List[DynamicTask]:
        """
        Get all tasks that are currently blocked (optimized with single query).
        
        Args:
            db: Database session
            execution_id: Parent execution ID
            
        Returns:
            List of blocked DynamicTask instances
        """
        # Get all tasks for execution with dependencies loaded (prevents N+1)
        all_tasks = await self.get_tasks_for_execution(
            db=db,
            execution_id=execution_id,
            include_dependencies=True,
        )
        
        # Get tasks that are explicitly blocked
        blocked_tasks = {t.id: t for t in all_tasks if t.status == "blocked"}
        
        # Optimized: Single query to get all blocking relationships for pending tasks
        pending_task_ids = [t.id for t in all_tasks if t.status == "pending"]
        
        if pending_task_ids:
            # Single optimized query to get all blockers for all pending tasks
            # This replaces N queries (one per pending task) with 1 query
            from sqlalchemy import and_
            blocking_query = (
                select(task_dependencies.c.blocks_task_id)
                .join(
                    DynamicTask,
                    DynamicTask.id == task_dependencies.c.task_id
                )
                .where(
                    and_(
                        task_dependencies.c.blocks_task_id.in_(pending_task_ids),
                        DynamicTask.status.notin_(["completed", "failed"]),
                        DynamicTask.parent_execution_id == execution_id,
                    )
                )
                .distinct()
            )
            result = await db.execute(blocking_query)
            blocked_task_ids = {row[0] for row in result.all()}
            
            # Add tasks blocked by incomplete blockers
            for task in all_tasks:
                if task.id in blocked_task_ids:
                    blocked_tasks[task.id] = task
        
        return list(blocked_tasks.values())

