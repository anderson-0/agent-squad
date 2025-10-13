"""
Workflow Engine

Manages task execution workflow states and transitions.
Implements a state machine for task execution lifecycle.
"""
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.task_execution_service import TaskExecutionService


class WorkflowState(str, Enum):
    """Task execution workflow states"""
    PENDING = "pending"                    # Task received, not yet analyzed
    ANALYZING = "analyzing"                # PM analyzing task
    PLANNING = "planning"                  # Creating implementation plan
    DELEGATED = "delegated"                # Task delegated to agents
    IN_PROGRESS = "in_progress"            # Agents working on task
    REVIEWING = "reviewing"                # Code review in progress
    TESTING = "testing"                    # QA testing in progress
    BLOCKED = "blocked"                    # Blocked by dependency or issue
    COMPLETED = "completed"                # Task completed successfully
    FAILED = "failed"                      # Task failed


class WorkflowEngine:
    """
    Workflow State Machine for Task Execution

    Manages state transitions and executes state-specific actions.
    Ensures valid state transitions and tracks execution progress.
    """

    # Valid state transitions
    VALID_TRANSITIONS: Dict[WorkflowState, List[WorkflowState]] = {
        WorkflowState.PENDING: [
            WorkflowState.ANALYZING,
            WorkflowState.FAILED,
        ],
        WorkflowState.ANALYZING: [
            WorkflowState.PLANNING,
            WorkflowState.BLOCKED,
            WorkflowState.FAILED,
        ],
        WorkflowState.PLANNING: [
            WorkflowState.DELEGATED,
            WorkflowState.BLOCKED,
            WorkflowState.FAILED,
        ],
        WorkflowState.DELEGATED: [
            WorkflowState.IN_PROGRESS,
            WorkflowState.BLOCKED,
            WorkflowState.FAILED,
        ],
        WorkflowState.IN_PROGRESS: [
            WorkflowState.REVIEWING,
            WorkflowState.TESTING,
            WorkflowState.BLOCKED,
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
        ],
        WorkflowState.REVIEWING: [
            WorkflowState.IN_PROGRESS,  # Changes requested
            WorkflowState.TESTING,      # Approved, move to QA
            WorkflowState.BLOCKED,
            WorkflowState.FAILED,
        ],
        WorkflowState.TESTING: [
            WorkflowState.IN_PROGRESS,  # Bugs found, back to dev
            WorkflowState.REVIEWING,    # Need re-review
            WorkflowState.COMPLETED,    # QA passed
            WorkflowState.BLOCKED,
            WorkflowState.FAILED,
        ],
        WorkflowState.BLOCKED: [
            WorkflowState.ANALYZING,    # Unblocked, restart
            WorkflowState.PLANNING,     # Unblocked at planning
            WorkflowState.IN_PROGRESS,  # Unblocked during dev
            WorkflowState.FAILED,       # Can't resolve blocker
        ],
        WorkflowState.COMPLETED: [],    # Terminal state
        WorkflowState.FAILED: [],       # Terminal state
    }

    def __init__(self):
        """Initialize workflow engine"""
        self._state_actions: Dict[WorkflowState, Callable] = {}

    def register_state_action(
        self,
        state: WorkflowState,
        action: Callable,
    ) -> None:
        """
        Register an action to execute when entering a state.

        Args:
            state: Workflow state
            action: Async function to execute
        """
        self._state_actions[state] = action

    def is_valid_transition(
        self,
        from_state: WorkflowState,
        to_state: WorkflowState,
    ) -> bool:
        """
        Check if a state transition is valid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid
        """
        valid_next_states = self.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_next_states

    def get_valid_transitions(
        self,
        current_state: WorkflowState,
    ) -> List[WorkflowState]:
        """
        Get list of valid next states.

        Args:
            current_state: Current workflow state

        Returns:
            List of valid next states
        """
        return self.VALID_TRANSITIONS.get(current_state, [])

    async def transition_state(
        self,
        db: AsyncSession,
        execution_id: UUID,
        from_state: WorkflowState,
        to_state: WorkflowState,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Transition to a new state.

        Args:
            db: Database session
            execution_id: Task execution ID
            from_state: Current state
            to_state: Target state
            reason: Optional transition reason
            metadata: Optional metadata

        Returns:
            True if transition succeeded

        Raises:
            ValueError: If transition is invalid
        """
        # Validate transition
        if not self.is_valid_transition(from_state, to_state):
            raise ValueError(
                f"Invalid transition from {from_state.value} to {to_state.value}. "
                f"Valid transitions: {[s.value for s in self.get_valid_transitions(from_state)]}"
            )

        # Update execution status
        log_message = reason or f"State transitioned from {from_state.value} to {to_state.value}"

        await TaskExecutionService.update_execution_status(
            db=db,
            execution_id=execution_id,
            status=to_state.value,
            log_message=log_message,
        )

        # Store transition metadata
        if metadata:
            await TaskExecutionService.add_log(
                db=db,
                execution_id=execution_id,
                level="info",
                message=f"State transition metadata",
                metadata={
                    "from_state": from_state.value,
                    "to_state": to_state.value,
                    **metadata,
                },
            )

        # Execute state action if registered
        if to_state in self._state_actions:
            action = self._state_actions[to_state]
            await action(db, execution_id, metadata)

        return True

    async def execute_state_actions(
        self,
        db: AsyncSession,
        execution_id: UUID,
        state: WorkflowState,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute actions for a specific state.

        Args:
            db: Database session
            execution_id: Task execution ID
            state: Current workflow state
            context: Optional context data

        Returns:
            Action result if action exists, None otherwise
        """
        if state in self._state_actions:
            action = self._state_actions[state]
            return await action(db, execution_id, context)

        return None

    def get_workflow_progress(
        self,
        current_state: WorkflowState,
    ) -> Dict[str, Any]:
        """
        Get workflow progress information.

        Args:
            current_state: Current workflow state

        Returns:
            Dictionary with progress details
        """
        # Define state order for progress calculation
        state_order = [
            WorkflowState.PENDING,
            WorkflowState.ANALYZING,
            WorkflowState.PLANNING,
            WorkflowState.DELEGATED,
            WorkflowState.IN_PROGRESS,
            WorkflowState.REVIEWING,
            WorkflowState.TESTING,
            WorkflowState.COMPLETED,
        ]

        # Terminal states
        if current_state == WorkflowState.COMPLETED:
            return {
                "state": current_state.value,
                "progress_percentage": 100,
                "is_terminal": True,
                "is_blocked": False,
            }

        if current_state == WorkflowState.FAILED:
            return {
                "state": current_state.value,
                "progress_percentage": 0,
                "is_terminal": True,
                "is_blocked": False,
            }

        if current_state == WorkflowState.BLOCKED:
            return {
                "state": current_state.value,
                "progress_percentage": 50,  # Estimated mid-way
                "is_terminal": False,
                "is_blocked": True,
            }

        # Calculate progress based on state position
        try:
            state_index = state_order.index(current_state)
            progress = int((state_index / len(state_order)) * 100)
        except ValueError:
            progress = 0

        return {
            "state": current_state.value,
            "progress_percentage": progress,
            "is_terminal": False,
            "is_blocked": False,
        }

    def get_state_description(
        self,
        state: WorkflowState,
    ) -> str:
        """
        Get human-readable description of a state.

        Args:
            state: Workflow state

        Returns:
            State description
        """
        descriptions = {
            WorkflowState.PENDING: "Task received and queued for processing",
            WorkflowState.ANALYZING: "Project Manager analyzing task requirements",
            WorkflowState.PLANNING: "Creating implementation plan and breaking down work",
            WorkflowState.DELEGATED: "Task delegated to team members",
            WorkflowState.IN_PROGRESS: "Agents actively working on implementation",
            WorkflowState.REVIEWING: "Tech Lead reviewing code changes",
            WorkflowState.TESTING: "QA Tester verifying acceptance criteria",
            WorkflowState.BLOCKED: "Blocked by dependency or unresolved issue",
            WorkflowState.COMPLETED: "Task completed successfully",
            WorkflowState.FAILED: "Task failed with errors",
        }

        return descriptions.get(state, state.value)

    def get_workflow_metrics(
        self,
        state_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate workflow metrics from state history.

        Args:
            state_history: List of state transitions with timestamps

        Returns:
            Dictionary with workflow metrics
        """
        if not state_history:
            return {
                "total_transitions": 0,
                "time_in_each_state": {},
                "total_duration_seconds": 0,
            }

        time_in_states: Dict[str, float] = {}
        total_transitions = len(state_history)

        # Calculate time spent in each state
        for i in range(len(state_history) - 1):
            current = state_history[i]
            next_state = state_history[i + 1]

            state_name = current.get("state")
            start_time = datetime.fromisoformat(current.get("timestamp"))
            end_time = datetime.fromisoformat(next_state.get("timestamp"))

            duration = (end_time - start_time).total_seconds()

            if state_name in time_in_states:
                time_in_states[state_name] += duration
            else:
                time_in_states[state_name] = duration

        # Total duration
        first_timestamp = datetime.fromisoformat(state_history[0].get("timestamp"))
        last_timestamp = datetime.fromisoformat(state_history[-1].get("timestamp"))
        total_duration = (last_timestamp - first_timestamp).total_seconds()

        return {
            "total_transitions": total_transitions,
            "time_in_each_state_seconds": time_in_states,
            "total_duration_seconds": total_duration,
            "average_time_per_state_seconds": total_duration / max(total_transitions, 1),
        }
