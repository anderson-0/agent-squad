"""
Server-Sent Events (SSE) API Endpoints

Real-time streaming endpoints for agent messages and execution updates.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.services.sse_service import sse_manager
from backend.services.squad_service import SquadService
from backend.services.task_execution_service import TaskExecutionService


router = APIRouter(prefix="/sse", tags=["sse"])


@router.get(
    "/execution/{execution_id}",
    summary="Stream execution updates",
    description="Subscribe to real-time updates for a task execution via Server-Sent Events"
)
async def stream_execution_updates(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream real-time updates for a task execution.

    This endpoint uses Server-Sent Events (SSE) to push updates to the client.

    **Events streamed:**
    - `connected` - Initial connection established
    - `message` - New agent message
    - `status_update` - Execution status changed
    - `log` - New log entry
    - `progress` - Progress update
    - `error` - Error occurred
    - `completed` - Execution completed
    - `heartbeat` - Keep-alive heartbeat (every 15 seconds)

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v1/sse/execution/{id}', {
        headers: { 'Authorization': 'Bearer <token>' }
    });

    eventSource.addEventListener('message', (e) => {
        const data = JSON.parse(e.data);
        console.log('New message:', data);
    });

    eventSource.addEventListener('status_update', (e) => {
        const data = JSON.parse(e.data);
        console.log('Status changed:', data);
    });
    ```

    Args:
        execution_id: Task execution ID to stream
        current_user: Current authenticated user
        db: Database session

    Returns:
        StreamingResponse with SSE events
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

    # Stream updates
    return StreamingResponse(
        sse_manager.subscribe_to_execution(
            execution_id=execution_id,
            user_id=current_user.id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get(
    "/squad/{squad_id}",
    summary="Stream squad updates",
    description="Subscribe to real-time updates for all executions in a squad via Server-Sent Events"
)
async def stream_squad_updates(
    squad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream real-time updates for all executions in a squad.

    This endpoint uses Server-Sent Events (SSE) to push updates to the client.

    **Events streamed:**
    - `connected` - Initial connection established
    - `execution_started` - New execution started
    - `execution_completed` - Execution completed
    - `message` - New agent message (across all executions)
    - `status_update` - Execution status changed
    - `heartbeat` - Keep-alive heartbeat (every 15 seconds)

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v1/sse/squad/{id}', {
        headers: { 'Authorization': 'Bearer <token>' }
    });

    eventSource.addEventListener('execution_started', (e) => {
        const data = JSON.parse(e.data);
        console.log('New execution:', data);
    });
    ```

    Args:
        squad_id: Squad ID to stream
        current_user: Current authenticated user
        db: Database session

    Returns:
        StreamingResponse with SSE events
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Stream updates
    return StreamingResponse(
        sse_manager.subscribe_to_squad(
            squad_id=squad_id,
            user_id=current_user.id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get(
    "/stats",
    summary="Get SSE connection stats",
    description="Get statistics about active SSE connections"
)
async def get_sse_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get SSE connection statistics.

    Returns information about active streaming connections.

    Args:
        current_user: Current authenticated user

    Returns:
        Connection statistics
    """
    stats = sse_manager.get_stats()
    return stats
