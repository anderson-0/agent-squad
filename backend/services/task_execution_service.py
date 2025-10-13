"""
Task Execution Service

Business logic for task execution operations.
Handles task execution lifecycle, status updates, logging, and error handling.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.project import Task, TaskExecution
from backend.models.squad import Squad
from backend.models.message import AgentMessage


def get_sse_manager():
    """Lazy import to avoid circular dependency"""
    from backend.services.sse_service import sse_manager
    return sse_manager


async def broadcast_sse_event(
    execution_id: UUID,
    squad_id: UUID,
    event: str,
    data: Dict[str, Any]
):
    """
    Broadcast event to SSE connections.

    Args:
        execution_id: Task execution ID
        squad_id: Squad ID
        event: Event type
        data: Event data
    """
    try:
        sse_manager = get_sse_manager()
        # Broadcast to execution subscribers
        await sse_manager.broadcast_to_execution(execution_id, event, data)
        # Also broadcast to squad subscribers
        await sse_manager.broadcast_to_squad(squad_id, event, data)
    except Exception as e:
        # Don't fail operations if SSE broadcast fails
        print(f"Error broadcasting SSE event: {e}")


class TaskExecutionService:
    """Service for handling task execution operations"""

    @staticmethod
    async def start_task_execution(
        db: AsyncSession,
        task_id: UUID,
        squad_id: UUID,
        execution_metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskExecution:
        """
        Start a new task execution.

        Args:
            db: Database session
            task_id: Task UUID
            squad_id: Squad UUID
            execution_metadata: Optional metadata

        Returns:
            Created task execution

        Raises:
            HTTPException: If task or squad not found
        """
        # Validate task exists
        result = await db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        # Validate squad exists
        result = await db.execute(
            select(Squad).where(Squad.id == squad_id)
        )
        squad = result.scalar_one_or_none()

        if not squad:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Squad {squad_id} not found"
            )

        if squad.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Squad {squad_id} is not active (status: {squad.status})"
            )

        # Create task execution
        task_execution = TaskExecution(
            task_id=task_id,
            squad_id=squad_id,
            status="pending",
            started_at=datetime.utcnow(),
            logs=[],
            execution_metadata=execution_metadata or {},
        )

        db.add(task_execution)

        # Update task status
        task.status = "in_progress"

        await db.commit()
        await db.refresh(task_execution)

        # Add initial log
        await TaskExecutionService.add_log(
            db,
            task_execution.id,
            "info",
            "Task execution started",
        )

        # Broadcast SSE event
        await broadcast_sse_event(
            execution_id=task_execution.id,
            squad_id=squad_id,
            event="execution_started",
            data={
                "task_id": str(task_id),
                "status": "pending",
            }
        )

        return task_execution

    @staticmethod
    async def get_task_execution(
        db: AsyncSession,
        execution_id: UUID,
        load_messages: bool = False,
    ) -> Optional[TaskExecution]:
        """
        Get task execution by ID.

        Args:
            db: Database session
            execution_id: Task execution UUID
            load_messages: Load associated messages

        Returns:
            Task execution if found, None otherwise
        """
        query = select(TaskExecution).where(TaskExecution.id == execution_id)

        if load_messages:
            query = query.options(selectinload(TaskExecution.messages))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_squad_executions(
        db: AsyncSession,
        squad_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[TaskExecution]:
        """
        Get task executions for a squad.

        Args:
            db: Database session
            squad_id: Squad UUID
            status: Optional status filter
            limit: Max results

        Returns:
            List of task executions
        """
        query = select(TaskExecution).where(TaskExecution.squad_id == squad_id)

        if status:
            query = query.where(TaskExecution.status == status)

        result = await db.execute(
            query
            .order_by(TaskExecution.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_execution_status(
        db: AsyncSession,
        execution_id: UUID,
        status: str,
        log_message: Optional[str] = None,
    ) -> TaskExecution:
        """
        Update task execution status.

        Args:
            db: Database session
            execution_id: Task execution UUID
            status: New status (pending, in_progress, completed, failed, blocked)
            log_message: Optional log message

        Returns:
            Updated task execution

        Raises:
            HTTPException: If execution not found or invalid status
        """
        valid_statuses = ["pending", "in_progress", "completed", "failed", "blocked"]

        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Valid: {', '.join(valid_statuses)}"
            )

        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )

        old_status = execution.status
        execution.status = status

        # Update completed_at if completed or failed
        if status in ["completed", "failed"]:
            execution.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(execution)

        # Add log
        message = log_message or f"Status changed from {old_status} to {status}"
        await TaskExecutionService.add_log(
            db,
            execution_id,
            "info",
            message,
        )

        # Broadcast SSE event
        await broadcast_sse_event(
            execution_id=execution_id,
            squad_id=execution.squad_id,
            event="status_update",
            data={
                "old_status": old_status,
                "new_status": status,
                "message": message,
            }
        )

        return execution

    @staticmethod
    async def add_log(
        db: AsyncSession,
        execution_id: UUID,
        level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskExecution:
        """
        Add a log entry to task execution.

        Args:
            db: Database session
            execution_id: Task execution UUID
            level: Log level (info, warning, error)
            message: Log message
            metadata: Optional metadata

        Returns:
            Updated task execution

        Raises:
            HTTPException: If execution not found
        """
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "metadata": metadata or {},
        }

        # Append to logs array
        current_logs = execution.logs or []
        current_logs.append(log_entry)
        execution.logs = current_logs

        await db.commit()
        await db.refresh(execution)

        # Broadcast SSE event for log
        await broadcast_sse_event(
            execution_id=execution_id,
            squad_id=execution.squad_id,
            event="log",
            data=log_entry
        )

        return execution

    @staticmethod
    async def complete_execution(
        db: AsyncSession,
        execution_id: UUID,
        result: Dict[str, Any],
    ) -> TaskExecution:
        """
        Mark task execution as completed.

        Args:
            db: Database session
            execution_id: Task execution UUID
            result: Execution result

        Returns:
            Updated task execution

        Raises:
            HTTPException: If execution not found
        """
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )

        execution.status = "completed"
        execution.completed_at = datetime.utcnow()

        # Store result in metadata
        current_metadata = execution.execution_metadata or {}
        current_metadata["result"] = result
        execution.execution_metadata = current_metadata

        # Update task status
        result_obj = await db.execute(
            select(Task).where(Task.id == execution.task_id)
        )
        task = result_obj.scalar_one_or_none()

        if task:
            task.status = "completed"

        await db.commit()
        await db.refresh(execution)

        # Add log
        await TaskExecutionService.add_log(
            db,
            execution_id,
            "info",
            "Task execution completed successfully",
        )

        # Broadcast SSE event
        await broadcast_sse_event(
            execution_id=execution_id,
            squad_id=execution.squad_id,
            event="completed",
            data={
                "result": result,
                "duration_seconds": (execution.completed_at - execution.started_at).total_seconds() if execution.completed_at and execution.started_at else None,
            }
        )

        return execution

    @staticmethod
    async def handle_execution_error(
        db: AsyncSession,
        execution_id: UUID,
        error: str,
        error_metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskExecution:
        """
        Handle task execution error.

        Args:
            db: Database session
            execution_id: Task execution UUID
            error: Error message
            error_metadata: Optional error metadata

        Returns:
            Updated task execution

        Raises:
            HTTPException: If execution not found
        """
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )

        execution.status = "failed"
        execution.completed_at = datetime.utcnow()
        execution.error_message = error

        # Store error details in metadata
        current_metadata = execution.execution_metadata or {}
        current_metadata["error_details"] = error_metadata or {}
        execution.execution_metadata = current_metadata

        # Update task status
        result = await db.execute(
            select(Task).where(Task.id == execution.task_id)
        )
        task = result.scalar_one_or_none()

        if task:
            task.status = "failed"

        await db.commit()
        await db.refresh(execution)

        # Add log
        await TaskExecutionService.add_log(
            db,
            execution_id,
            "error",
            f"Task execution failed: {error}",
            metadata=error_metadata,
        )

        # Broadcast SSE event
        await broadcast_sse_event(
            execution_id=execution_id,
            squad_id=execution.squad_id,
            event="error",
            data={
                "error": error,
                "error_metadata": error_metadata or {},
            }
        )

        return execution

    @staticmethod
    async def get_execution_messages(
        db: AsyncSession,
        execution_id: UUID,
        limit: Optional[int] = 100,
    ) -> List[AgentMessage]:
        """
        Get all messages for a task execution.

        Args:
            db: Database session
            execution_id: Task execution UUID
            limit: Max messages to return

        Returns:
            List of agent messages

        Raises:
            HTTPException: If execution not found
        """
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )

        query = (
            select(AgentMessage)
            .where(AgentMessage.task_execution_id == execution_id)
            .order_by(AgentMessage.created_at)
        )

        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_execution_summary(
        db: AsyncSession,
        execution_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get comprehensive execution summary.

        Args:
            db: Database session
            execution_id: Task execution UUID

        Returns:
            Dictionary with execution summary

        Raises:
            HTTPException: If execution not found
        """
        execution = await TaskExecutionService.get_task_execution(
            db, execution_id, load_messages=True
        )

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )

        # Get message count
        message_count = len(execution.messages) if execution.messages else 0

        # Calculate duration
        duration_seconds = None
        if execution.completed_at and execution.started_at:
            duration_seconds = (execution.completed_at - execution.started_at).total_seconds()

        return {
            "id": str(execution.id),
            "task_id": str(execution.task_id),
            "squad_id": str(execution.squad_id),
            "status": execution.status,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration_seconds": duration_seconds,
            "error_message": execution.error_message,
            "message_count": message_count,
            "log_count": len(execution.logs) if execution.logs else 0,
            "metadata": execution.execution_metadata,
            "created_at": execution.created_at.isoformat(),
            "updated_at": execution.updated_at.isoformat(),
        }

    @staticmethod
    async def cancel_execution(
        db: AsyncSession,
        execution_id: UUID,
        reason: Optional[str] = None,
    ) -> TaskExecution:
        """
        Cancel a running task execution.

        Args:
            db: Database session
            execution_id: Task execution UUID
            reason: Optional cancellation reason

        Returns:
            Updated task execution

        Raises:
            HTTPException: If execution not found or already completed
        """
        execution = await TaskExecutionService.get_task_execution(db, execution_id)

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )

        if execution.status in ["completed", "failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel execution with status: {execution.status}"
            )

        execution.status = "failed"
        execution.completed_at = datetime.utcnow()
        execution.error_message = f"Cancelled by user. {reason or ''}"

        await db.commit()
        await db.refresh(execution)

        # Add log
        await TaskExecutionService.add_log(
            db,
            execution_id,
            "warning",
            f"Task execution cancelled. {reason or 'No reason provided.'}",
        )

        return execution
