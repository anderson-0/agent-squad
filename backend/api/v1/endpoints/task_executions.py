"""
Task Execution API Endpoints

Endpoints for managing and monitoring AI agent task executions.
"""
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.task_execution import TaskExecution
from backend.services.task_execution_service import TaskExecutionService
from backend.services.squad_service import SquadService
from backend.schemas.task_execution import (
    TaskExecutionCreate,
    TaskExecutionResponse,
    TaskExecutionWithMessages,
    TaskExecutionSummary,
    TaskExecutionCancel,
    HumanIntervention,
)


router = APIRouter(prefix="/task-executions", tags=["task-executions"])


@router.post(
    "",
    response_model=TaskExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start task execution",
    description="Start a new AI agent task execution"
)
async def start_task_execution(
    execution_data: TaskExecutionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskExecution:
    """
    Start a new task execution.

    - **task_id**: ID of the task to execute
    - **squad_id**: ID of the squad to execute the task
    - **execution_metadata**: Optional metadata for the execution

    Returns the created task execution.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution_data.squad_id, current_user.id)

    # Start execution
    execution = await TaskExecutionService.start_task_execution(
        db=db,
        task_id=execution_data.task_id,
        squad_id=execution_data.squad_id,
        execution_metadata=execution_data.execution_metadata or {},
    )

    return execution


@router.get(
    "",
    response_model=List[TaskExecutionResponse],
    summary="List task executions",
    description="Get all task executions for a squad"
)
async def list_task_executions(
    squad_id: UUID = Query(..., description="Squad ID to get executions for"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of executions to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of executions to return"),
) -> List[TaskExecution]:
    """
    List task executions for a squad.

    - **squad_id**: Squad ID (required)
    - **status**: Filter by status (optional)

    Supports pagination with skip and limit.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Get executions
    executions = await TaskExecutionService.get_squad_executions(
        db=db,
        squad_id=squad_id,
        status=status_filter,
    )

    # Apply pagination
    return executions[skip: skip + limit]


@router.get(
    "/{execution_id}",
    response_model=TaskExecutionResponse,
    summary="Get task execution",
    description="Get details of a specific task execution"
)
async def get_task_execution(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskExecution:
    """
    Get task execution by ID.

    - **execution_id**: UUID of the task execution

    Returns execution details if user has access.
    """
    # Get execution
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    return execution


@router.get(
    "/{execution_id}/summary",
    response_model=TaskExecutionSummary,
    summary="Get execution summary",
    description="Get comprehensive summary of a task execution"
)
async def get_execution_summary(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive execution summary.

    - **execution_id**: UUID of the task execution

    Returns detailed summary with duration, message count, agent activity.
    """
    # Get execution
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Get summary
    summary = await TaskExecutionService.get_execution_summary(db, execution_id)

    return summary


@router.get(
    "/{execution_id}/messages",
    response_model=TaskExecutionWithMessages,
    summary="Get execution messages",
    description="Get all agent messages for a task execution"
)
async def get_execution_messages(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    message_type: str | None = Query(None, description="Filter by message type"),
    skip: int = Query(0, ge=0, description="Number of messages to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of messages to return"),
) -> Dict[str, Any]:
    """
    Get all messages for a task execution.

    - **execution_id**: UUID of the task execution
    - **message_type**: Filter by message type (optional)

    Returns execution with messages.
    """
    # Get execution
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Get messages
    messages = await TaskExecutionService.get_execution_messages(
        db=db,
        execution_id=execution_id,
    )

    # Filter by message type if specified
    if message_type:
        messages = [m for m in messages if m.message_type == message_type]

    # Apply pagination
    paginated_messages = messages[skip: skip + limit]

    return {
        "execution": execution,
        "messages": paginated_messages,
        "total_messages": len(messages),
        "filtered_count": len(paginated_messages),
    }


@router.get(
    "/{execution_id}/logs",
    response_model=Dict[str, Any],
    summary="Get execution logs",
    description="Get logs for a task execution"
)
async def get_execution_logs(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    level: str | None = Query(None, description="Filter by log level (info/warning/error)"),
) -> Dict[str, Any]:
    """
    Get logs for a task execution.

    - **execution_id**: UUID of the task execution
    - **level**: Filter by log level (optional)

    Returns execution logs.
    """
    # Get execution
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Get logs from execution
    logs = execution.logs or []

    # Filter by level if specified
    if level:
        logs = [log for log in logs if log.get("level") == level]

    return {
        "execution_id": str(execution_id),
        "logs": logs,
        "total_logs": len(execution.logs or []),
        "filtered_count": len(logs),
    }


@router.patch(
    "/{execution_id}/status",
    response_model=TaskExecutionResponse,
    summary="Update execution status",
    description="Update the status of a task execution"
)
async def update_execution_status(
    execution_id: UUID,
    new_status: str = Query(..., description="New status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskExecution:
    """
    Update execution status.

    - **execution_id**: UUID of the task execution
    - **new_status**: New status

    Returns updated execution.
    """
    # Get execution
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Update status
    updated_execution = await TaskExecutionService.update_execution_status(
        db=db,
        execution_id=execution_id,
        status=new_status,
    )

    return updated_execution


@router.post(
    "/{execution_id}/complete",
    response_model=TaskExecutionResponse,
    summary="Complete execution",
    description="Mark a task execution as completed"
)
async def complete_execution(
    execution_id: UUID,
    result: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskExecution:
    """
    Complete task execution.

    - **execution_id**: UUID of the task execution
    - **result**: Execution result (optional)

    Returns completed execution.
    """
    # Get execution
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Complete execution
    completed_execution = await TaskExecutionService.complete_execution(
        db=db,
        execution_id=execution_id,
        result=result,
    )

    return completed_execution


@router.post(
    "/{execution_id}/error",
    response_model=TaskExecutionResponse,
    summary="Report execution error",
    description="Report an error for a task execution"
)
async def report_execution_error(
    execution_id: UUID,
    error_message: str,
    error_details: Dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskExecution:
    """
    Report execution error.

    - **execution_id**: UUID of the task execution
    - **error_message**: Error message
    - **error_details**: Additional error details (optional)

    Returns failed execution.
    """
    # Get execution
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Handle error
    failed_execution = await TaskExecutionService.handle_execution_error(
        db=db,
        execution_id=execution_id,
        error_message=error_message,
        error_details=error_details or {},
    )

    return failed_execution


@router.post(
    "/{execution_id}/intervention",
    response_model=TaskExecutionResponse,
    summary="Human intervention",
    description="Provide human intervention for a blocked task execution"
)
async def human_intervention(
    execution_id: UUID,
    intervention_data: HumanIntervention,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskExecution:
    """
    Provide human intervention for blocked execution.

    - **execution_id**: UUID of the task execution
    - **action**: Intervention action (continue/cancel/retry)
    - **instructions**: Instructions for agents (optional)
    - **metadata**: Additional metadata (optional)

    Returns updated execution.
    """
    # Get execution
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Log intervention
    await TaskExecutionService.add_log(
        db=db,
        execution_id=execution_id,
        level="info",
        message=f"Human intervention: {intervention_data.action}",
        metadata={
            "user_id": str(current_user.id),
            "action": intervention_data.action,
            "instructions": intervention_data.instructions,
            "metadata": intervention_data.metadata,
        },
    )

    # Handle different intervention actions
    if intervention_data.action == "cancel":
        execution = await TaskExecutionService.cancel_execution(db, execution_id)
    elif intervention_data.action == "continue":
        # Update status to in_progress if blocked
        if execution.status == "blocked":
            execution = await TaskExecutionService.update_execution_status(
                db=db,
                execution_id=execution_id,
                status="in_progress",
            )

    return execution


@router.post(
    "/{execution_id}/cancel",
    response_model=TaskExecutionResponse,
    summary="Cancel execution",
    description="Cancel a running task execution"
)
async def cancel_execution(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskExecution:
    """
    Cancel task execution.

    - **execution_id**: UUID of the task execution

    Returns cancelled execution.
    """
    # Get execution
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Cancel execution
    cancelled_execution = await TaskExecutionService.cancel_execution(db, execution_id)

    if not cancelled_execution:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Execution cannot be cancelled (already completed or failed)"
        )

    return cancelled_execution


@router.post(
    "/{execution_id}/logs",
    response_model=TaskExecutionResponse,
    summary="Add log entry",
    description="Add a log entry to a task execution"
)
async def add_log_entry(
    execution_id: UUID,
    level: str = Query(..., regex="^(info|warning|error)$", description="Log level"),
    message: str = Query(..., description="Log message"),
    metadata: Dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskExecution:
    """
    Add log entry to execution.

    - **execution_id**: UUID of the task execution
    - **level**: Log level (info/warning/error)
    - **message**: Log message
    - **metadata**: Additional metadata (optional)

    Returns updated execution.
    """
    # Get execution
    execution = await TaskExecutionService.get_task_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Add log
    updated_execution = await TaskExecutionService.add_log(
        db=db,
        execution_id=execution_id,
        level=level,
        message=message,
        metadata=metadata or {},
    )

    return updated_execution
