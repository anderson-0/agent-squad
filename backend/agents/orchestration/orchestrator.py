"""
Task Orchestrator

Main orchestration logic that coordinates agent collaboration,
manages workflows, and handles task execution from start to finish.
"""
from typing import Dict, List, Optional, Any
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.orchestration.workflow_engine import WorkflowEngine, WorkflowState
from backend.agents.orchestration.delegation_engine import DelegationEngine
from backend.agents.communication.message_bus import MessageBus
from backend.agents.context.context_manager import ContextManager
from backend.services.task_execution_service import TaskExecutionService
from backend.models.project import Task


class TaskOrchestrator:
    """
    Task Orchestrator - Coordinates Agent Collaboration

    Responsibilities:
    - Manage task execution workflow
    - Coordinate agent communication
    - Handle task delegation
    - Monitor progress and handle blockers
    - Escalate issues when needed
    """

    def __init__(
        self,
        message_bus: MessageBus,
        context_manager: ContextManager,
    ):
        """
        Initialize task orchestrator

        Args:
            message_bus: Message bus for agent communication
            context_manager: Context manager for RAG/memory
        """
        self.message_bus = message_bus
        self.context_manager = context_manager
        self.workflow_engine = WorkflowEngine()
        self.delegation_engine = DelegationEngine()

        # Register state actions
        self._register_state_actions()

    def _register_state_actions(self) -> None:
        """Register actions for workflow states"""
        self.workflow_engine.register_state_action(
            WorkflowState.ANALYZING,
            self._on_analyzing_state
        )
        self.workflow_engine.register_state_action(
            WorkflowState.PLANNING,
            self._on_planning_state
        )
        self.workflow_engine.register_state_action(
            WorkflowState.DELEGATED,
            self._on_delegated_state
        )

    async def execute_task(
        self,
        db: AsyncSession,
        task: Task,
        squad_id: UUID,
    ) -> UUID:
        """
        Execute a task with the squad.

        This is the main entry point for task execution.

        Args:
            db: Database session
            task: Task to execute
            squad_id: Squad UUID

        Returns:
            Task execution ID
        """
        # Start task execution
        execution = await TaskExecutionService.start_task_execution(
            db=db,
            task_id=task.id,
            squad_id=squad_id,
        )

        # Transition to analyzing state
        await self.workflow_engine.transition_state(
            db=db,
            execution_id=execution.id,
            from_state=WorkflowState.PENDING,
            to_state=WorkflowState.ANALYZING,
            reason="Starting task analysis with Project Manager",
        )

        # Return execution ID for tracking
        return execution.id

    async def monitor_progress(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> Dict[str, Any]:
        """
        Monitor task execution progress.

        Args:
            db: Database session
            execution_id: Task execution ID

        Returns:
            Progress information
        """
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")

        # Get workflow state
        current_state = WorkflowState(execution.status)

        # Get progress
        progress = self.workflow_engine.get_workflow_progress(current_state)

        # Get messages count
        messages = await TaskExecutionService.get_execution_messages(db, execution_id)

        return {
            "execution_id": str(execution_id),
            "current_state": current_state.value,
            "state_description": self.workflow_engine.get_state_description(current_state),
            "progress_percentage": progress["progress_percentage"],
            "is_blocked": progress["is_blocked"],
            "is_terminal": progress["is_terminal"],
            "message_count": len(messages),
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "error_message": execution.error_message,
        }

    async def handle_blocker(
        self,
        db: AsyncSession,
        execution_id: UUID,
        blocker_description: str,
        blocker_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle a blocker during task execution.

        Args:
            db: Database session
            execution_id: Task execution ID
            blocker_description: Description of blocker
            blocker_metadata: Optional metadata
        """
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")

        current_state = WorkflowState(execution.status)

        # Transition to blocked state
        await self.workflow_engine.transition_state(
            db=db,
            execution_id=execution_id,
            from_state=current_state,
            to_state=WorkflowState.BLOCKED,
            reason=f"Blocked: {blocker_description}",
            metadata=blocker_metadata,
        )

        # Add log
        await TaskExecutionService.add_log(
            db=db,
            execution_id=execution_id,
            level="warning",
            message=f"Blocker encountered: {blocker_description}",
            metadata=blocker_metadata,
        )

    async def resolve_blocker(
        self,
        db: AsyncSession,
        execution_id: UUID,
        resolution: str,
        next_state: WorkflowState,
    ) -> None:
        """
        Resolve a blocker and resume task execution.

        Args:
            db: Database session
            execution_id: Task execution ID
            resolution: How the blocker was resolved
            next_state: State to transition to after unblocking
        """
        # Transition from blocked to next state
        await self.workflow_engine.transition_state(
            db=db,
            execution_id=execution_id,
            from_state=WorkflowState.BLOCKED,
            to_state=next_state,
            reason=f"Blocker resolved: {resolution}",
        )

        # Add log
        await TaskExecutionService.add_log(
            db=db,
            execution_id=execution_id,
            level="info",
            message=f"Blocker resolved: {resolution}",
        )

    async def escalate_to_human(
        self,
        db: AsyncSession,
        execution_id: UUID,
        reason: str,
        details: str,
        attempted_solutions: List[str],
    ) -> Dict[str, Any]:
        """
        Escalate task to human for intervention.

        Args:
            db: Database session
            execution_id: Task execution ID
            reason: Reason for escalation
            details: Detailed explanation
            attempted_solutions: What was tried

        Returns:
            Escalation details
        """
        # Add log
        await TaskExecutionService.add_log(
            db=db,
            execution_id=execution_id,
            level="warning",
            message=f"Escalated to human: {reason}",
            metadata={
                "details": details,
                "attempted_solutions": attempted_solutions,
            },
        )

        # In Phase 4, this would send a notification to the user
        # For Phase 3, we just log it

        return {
            "execution_id": str(execution_id),
            "reason": reason,
            "details": details,
            "attempted_solutions": attempted_solutions,
            "escalated_at": None,  # Would be set by notification system
        }

    async def get_execution_summary(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get comprehensive execution summary.

        Args:
            db: Database session
            execution_id: Task execution ID

        Returns:
            Comprehensive summary
        """
        # Get basic summary
        summary = await TaskExecutionService.get_execution_summary(db, execution_id)

        # Get progress
        progress = await self.monitor_progress(db, execution_id)

        # Combine
        return {
            **summary,
            "progress": progress,
        }

    # State action handlers

    async def _on_analyzing_state(
        self,
        db: AsyncSession,
        execution_id: UUID,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle ANALYZING state - PM analyzes the task.

        Args:
            db: Database session
            execution_id: Task execution ID
            context: Optional context
        """
        await TaskExecutionService.add_log(
            db=db,
            execution_id=execution_id,
            level="info",
            message="Project Manager analyzing task requirements",
        )

        # In Phase 4, this would:
        # 1. Get PM agent
        # 2. Load task context from RAG
        # 3. PM analyzes task via LLM
        # 4. PM creates initial plan
        # 5. Transition to PLANNING state

        # For Phase 3, we just log and move to planning
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if execution:
            # Auto-transition to planning after analysis
            await self.workflow_engine.transition_state(
                db=db,
                execution_id=execution_id,
                from_state=WorkflowState.ANALYZING,
                to_state=WorkflowState.PLANNING,
                reason="Analysis complete, creating implementation plan",
            )

    async def _on_planning_state(
        self,
        db: AsyncSession,
        execution_id: UUID,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle PLANNING state - create implementation plan.

        Args:
            db: Database session
            execution_id: Task execution ID
            context: Optional context
        """
        await TaskExecutionService.add_log(
            db=db,
            execution_id=execution_id,
            level="info",
            message="Creating implementation plan and breaking down work",
        )

        # In Phase 4, this would:
        # 1. PM breaks down task into subtasks
        # 2. Delegation engine identifies best agents
        # 3. Create task assignments
        # 4. Transition to DELEGATED state

        # For Phase 3, we just log
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if execution:
            # Auto-transition to delegated
            await self.workflow_engine.transition_state(
                db=db,
                execution_id=execution_id,
                from_state=WorkflowState.PLANNING,
                to_state=WorkflowState.DELEGATED,
                reason="Implementation plan created, delegating to team",
            )

    async def _on_delegated_state(
        self,
        db: AsyncSession,
        execution_id: UUID,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle DELEGATED state - work assigned to agents.

        Args:
            db: Database session
            execution_id: Task execution ID
            context: Optional context
        """
        await TaskExecutionService.add_log(
            db=db,
            execution_id=execution_id,
            level="info",
            message="Tasks delegated to team members, work beginning",
        )

        # In Phase 4, this would:
        # 1. Send TaskAssignment messages to agents
        # 2. Agents acknowledge and start work
        # 3. Transition to IN_PROGRESS state

        # For Phase 3, we just log
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if execution:
            # Auto-transition to in_progress
            await self.workflow_engine.transition_state(
                db=db,
                execution_id=execution_id,
                from_state=WorkflowState.DELEGATED,
                to_state=WorkflowState.IN_PROGRESS,
                reason="Team members have begun implementation",
            )

    async def transition_to_review(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> None:
        """
        Transition task to code review state.

        Args:
            db: Database session
            execution_id: Task execution ID
        """
        await self.workflow_engine.transition_state(
            db=db,
            execution_id=execution_id,
            from_state=WorkflowState.IN_PROGRESS,
            to_state=WorkflowState.REVIEWING,
            reason="Implementation complete, requesting code review",
        )

    async def transition_to_testing(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> None:
        """
        Transition task to testing state.

        Args:
            db: Database session
            execution_id: Task execution ID
        """
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")

        current_state = WorkflowState(execution.status)

        await self.workflow_engine.transition_state(
            db=db,
            execution_id=execution_id,
            from_state=current_state,
            to_state=WorkflowState.TESTING,
            reason="Code approved, moving to QA testing",
        )

    async def complete_task(
        self,
        db: AsyncSession,
        execution_id: UUID,
        result: Dict[str, Any],
    ) -> None:
        """
        Mark task as completed.

        Args:
            db: Database session
            execution_id: Task execution ID
            result: Task completion result
        """
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")

        current_state = WorkflowState(execution.status)

        # Transition to completed
        await self.workflow_engine.transition_state(
            db=db,
            execution_id=execution_id,
            from_state=current_state,
            to_state=WorkflowState.COMPLETED,
            reason="All acceptance criteria met, task completed",
        )

        # Complete execution
        await TaskExecutionService.complete_execution(
            db=db,
            execution_id=execution_id,
            result=result,
        )

    async def fail_task(
        self,
        db: AsyncSession,
        execution_id: UUID,
        error: str,
        error_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Mark task as failed.

        Args:
            db: Database session
            execution_id: Task execution ID
            error: Error message
            error_metadata: Optional error metadata
        """
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise ValueError(f"Task execution {execution_id} not found")

        current_state = WorkflowState(execution.status)

        # Transition to failed
        await self.workflow_engine.transition_state(
            db=db,
            execution_id=execution_id,
            from_state=current_state,
            to_state=WorkflowState.FAILED,
            reason=f"Task failed: {error}",
            metadata=error_metadata,
        )

        # Handle error
        await TaskExecutionService.handle_execution_error(
            db=db,
            execution_id=execution_id,
            error=error,
            error_metadata=error_metadata,
        )
