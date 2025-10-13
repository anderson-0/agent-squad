"""
Agent Message API Endpoints

Endpoints for viewing and managing agent-to-agent messages.
"""
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.agent_message import AgentMessage
from backend.services.squad_service import SquadService
from backend.schemas.agent_message import (
    AgentMessageResponse,
    AgentMessageCreate,
    MessageStats,
)


router = APIRouter(prefix="/agent-messages", tags=["agent-messages"])


@router.get(
    "",
    response_model=List[AgentMessageResponse],
    summary="List agent messages",
    description="Get messages for a task execution or between specific agents"
)
async def list_agent_messages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    task_execution_id: UUID | None = Query(None, description="Filter by task execution"),
    sender_id: UUID | None = Query(None, description="Filter by sender"),
    recipient_id: UUID | None = Query(None, description="Filter by recipient"),
    message_type: str | None = Query(None, description="Filter by message type"),
    since: datetime | None = Query(None, description="Messages since this timestamp"),
    skip: int = Query(0, ge=0, description="Number of messages to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of messages to return"),
) -> List[AgentMessage]:
    """
    List agent messages with various filters.

    - **task_execution_id**: Filter by task execution
    - **sender_id**: Filter by sender agent
    - **recipient_id**: Filter by recipient agent
    - **message_type**: Filter by message type
    - **since**: Get messages after this timestamp

    Returns list of agent messages.
    """
    # Build query
    query = select(AgentMessage)

    # Apply filters
    filters = []
    if task_execution_id:
        filters.append(AgentMessage.task_execution_id == task_execution_id)

        # Verify access to task execution
        from backend.models.task_execution import TaskExecution
        exec_query = select(TaskExecution).where(TaskExecution.id == task_execution_id)
        result = await db.execute(exec_query)
        execution = result.scalar_one_or_none()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {task_execution_id} not found"
            )

        # Verify squad ownership
        await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    if sender_id:
        filters.append(AgentMessage.sender_id == sender_id)

    if recipient_id:
        filters.append(AgentMessage.recipient_id == recipient_id)

    if message_type:
        filters.append(AgentMessage.message_type == message_type)

    if since:
        filters.append(AgentMessage.created_at >= since)

    if filters:
        query = query.where(and_(*filters))

    # Order by created_at descending (newest first)
    query = query.order_by(AgentMessage.created_at.desc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    messages = result.scalars().all()

    return list(messages)


@router.get(
    "/{message_id}",
    response_model=AgentMessageResponse,
    summary="Get agent message",
    description="Get details of a specific agent message"
)
async def get_agent_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AgentMessage:
    """
    Get agent message by ID.

    - **message_id**: UUID of the message

    Returns message details if user has access.
    """
    # Get message
    query = select(AgentMessage).where(AgentMessage.id == message_id)
    result = await db.execute(query)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found"
        )

    # Verify access through task execution
    if message.task_execution_id:
        from backend.models.task_execution import TaskExecution
        exec_query = select(TaskExecution).where(TaskExecution.id == message.task_execution_id)
        result = await db.execute(exec_query)
        execution = result.scalar_one_or_none()

        if execution:
            await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    return message


@router.get(
    "/conversation/{agent1_id}/{agent2_id}",
    response_model=List[AgentMessageResponse],
    summary="Get conversation between agents",
    description="Get all messages between two specific agents"
)
async def get_agent_conversation(
    agent1_id: UUID,
    agent2_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    task_execution_id: UUID | None = Query(None, description="Filter by task execution"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> List[AgentMessage]:
    """
    Get conversation between two agents.

    - **agent1_id**: First agent UUID
    - **agent2_id**: Second agent UUID
    - **task_execution_id**: Optional filter by task execution

    Returns messages between the two agents (in both directions).
    """
    # Build query for messages in both directions
    query = select(AgentMessage).where(
        or_(
            and_(
                AgentMessage.sender_id == agent1_id,
                AgentMessage.recipient_id == agent2_id
            ),
            and_(
                AgentMessage.sender_id == agent2_id,
                AgentMessage.recipient_id == agent1_id
            )
        )
    )

    # Filter by task execution if specified
    if task_execution_id:
        query = query.where(AgentMessage.task_execution_id == task_execution_id)

        # Verify access
        from backend.models.task_execution import TaskExecution
        exec_query = select(TaskExecution).where(TaskExecution.id == task_execution_id)
        result = await db.execute(exec_query)
        execution = result.scalar_one_or_none()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {task_execution_id} not found"
            )

        await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Order by created_at ascending (chronological conversation)
    query = query.order_by(AgentMessage.created_at.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    messages = result.scalars().all()

    return list(messages)


@router.get(
    "/stats/execution/{execution_id}",
    response_model=MessageStats,
    summary="Get message statistics",
    description="Get statistics about messages in a task execution"
)
async def get_message_stats(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get message statistics for a task execution.

    - **execution_id**: UUID of the task execution

    Returns message statistics (count by type, sender, etc.).
    """
    # Verify access
    from backend.models.task_execution import TaskExecution
    exec_query = select(TaskExecution).where(TaskExecution.id == execution_id)
    result = await db.execute(exec_query)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found"
        )

    await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Get all messages for this execution
    query = select(AgentMessage).where(AgentMessage.task_execution_id == execution_id)
    result = await db.execute(query)
    messages = result.scalars().all()

    # Calculate statistics
    total_messages = len(messages)

    # Count by message type
    messages_by_type = {}
    for msg in messages:
        msg_type = msg.message_type
        messages_by_type[msg_type] = messages_by_type.get(msg_type, 0) + 1

    # Count by sender
    messages_by_sender = {}
    for msg in messages:
        sender = str(msg.sender_id)
        messages_by_sender[sender] = messages_by_sender.get(sender, 0) + 1

    # Count by recipient (excluding broadcasts)
    messages_by_recipient = {}
    for msg in messages:
        if msg.recipient_id:
            recipient = str(msg.recipient_id)
            messages_by_recipient[recipient] = messages_by_recipient.get(recipient, 0) + 1

    # Calculate time range
    if messages:
        first_message = min(messages, key=lambda m: m.created_at)
        last_message = max(messages, key=lambda m: m.created_at)
        time_range = {
            "first_message_at": first_message.created_at.isoformat(),
            "last_message_at": last_message.created_at.isoformat(),
            "duration_seconds": (last_message.created_at - first_message.created_at).total_seconds(),
        }
    else:
        time_range = {
            "first_message_at": None,
            "last_message_at": None,
            "duration_seconds": 0,
        }

    return {
        "execution_id": str(execution_id),
        "total_messages": total_messages,
        "messages_by_type": messages_by_type,
        "messages_by_sender": messages_by_sender,
        "messages_by_recipient": messages_by_recipient,
        "broadcast_count": sum(1 for m in messages if m.recipient_id is None),
        "time_range": time_range,
    }


@router.post(
    "",
    response_model=AgentMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send agent message (testing)",
    description="Send a test message between agents (for testing/debugging only)"
)
async def send_agent_message(
    message_data: AgentMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AgentMessage:
    """
    Send a test message between agents.

    **WARNING**: This endpoint is for testing/debugging only.
    In production, agents send messages through the MessageBus.

    - **sender_id**: Sender agent UUID
    - **recipient_id**: Recipient agent UUID (optional for broadcast)
    - **content**: Message content
    - **message_type**: Message type
    - **task_execution_id**: Task execution UUID (optional)
    - **message_metadata**: Additional metadata (optional)

    Returns the created message.
    """
    # Verify access if task_execution_id is provided
    if message_data.task_execution_id:
        from backend.models.task_execution import TaskExecution
        exec_query = select(TaskExecution).where(TaskExecution.id == message_data.task_execution_id)
        result = await db.execute(exec_query)
        execution = result.scalar_one_or_none()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {message_data.task_execution_id} not found"
            )

        await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Create message
    message = AgentMessage(
        sender_id=message_data.sender_id,
        recipient_id=message_data.recipient_id,
        content=message_data.content,
        message_type=message_data.message_type,
        task_execution_id=message_data.task_execution_id,
        message_metadata=message_data.message_metadata or {},
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message


@router.delete(
    "/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent message",
    description="Delete a specific agent message (for cleanup/testing)"
)
async def delete_agent_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete an agent message.

    - **message_id**: UUID of the message

    This action cannot be undone.
    """
    # Get message
    query = select(AgentMessage).where(AgentMessage.id == message_id)
    result = await db.execute(query)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found"
        )

    # Verify access through task execution
    if message.task_execution_id:
        from backend.models.task_execution import TaskExecution
        exec_query = select(TaskExecution).where(TaskExecution.id == message.task_execution_id)
        result = await db.execute(exec_query)
        execution = result.scalar_one_or_none()

        if execution:
            await SquadService.verify_squad_ownership(db, execution.squad_id, current_user.id)

    # Delete message
    await db.delete(message)
    await db.commit()
