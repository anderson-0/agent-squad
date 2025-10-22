"""
Conversations API Endpoints

Endpoints for managing agent-to-agent conversations including:
- Initiating questions
- Acknowledging conversations
- Answering questions
- Escalating conversations
- Viewing conversation timelines
"""
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models import Conversation, ConversationEvent, SquadMember
from backend.agents.interaction.conversation_manager import ConversationManager
from backend.agents.interaction.escalation_service import EscalationService
from backend.services.squad_service import SquadService


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post(
    "/initiate",
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a question",
    description="Start a new agent-to-agent conversation"
)
async def initiate_question(
    asker_id: UUID,
    question_content: str,
    question_type: str = "default",
    task_execution_id: UUID | None = None,
    metadata: Dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Initiate a new question from one agent to another.

    - **asker_id**: UUID of the agent asking the question
    - **question_content**: Content of the question
    - **question_type**: Type of question (implementation, architecture, etc.)
    - **task_execution_id**: Optional task execution context
    - **metadata**: Optional additional metadata

    Returns the created conversation with initial routing.
    """
    # Get asker to verify squad ownership
    stmt = select(SquadMember).where(SquadMember.id == asker_id)
    result = await db.execute(stmt)
    asker = result.scalar_one_or_none()

    if not asker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {asker_id} not found"
        )

    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, asker.squad_id, current_user.id)

    # Initiate conversation
    manager = ConversationManager(db)
    conversation = await manager.initiate_question(
        asker_id=asker_id,
        question_content=question_content,
        question_type=question_type,
        task_execution_id=task_execution_id,
        metadata=metadata
    )

    return {
        "id": str(conversation.id),
        "initial_message_id": str(conversation.initial_message_id),
        "current_state": conversation.current_state,
        "asker_id": str(conversation.asker_id),
        "current_responder_id": str(conversation.current_responder_id),
        "escalation_level": conversation.escalation_level,
        "question_type": conversation.question_type,
        "timeout_at": conversation.timeout_at.isoformat() if conversation.timeout_at else None,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None
    }


@router.post(
    "/{conversation_id}/acknowledge",
    summary="Acknowledge conversation",
    description="Responder acknowledges receipt of question"
)
async def acknowledge_conversation(
    conversation_id: UUID,
    responder_id: UUID,
    custom_message: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Acknowledge a conversation (responder confirms receipt).

    - **conversation_id**: UUID of the conversation
    - **responder_id**: UUID of the responder acknowledging
    - **custom_message**: Optional custom acknowledgment message

    Updates conversation state to WAITING.
    """
    # Get conversation to verify squad ownership
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    # Get asker to verify squad
    stmt = select(SquadMember).where(SquadMember.id == conversation.asker_id)
    result = await db.execute(stmt)
    asker = result.scalar_one_or_none()

    if asker:
        await SquadService.verify_squad_ownership(db, asker.squad_id, current_user.id)

    # Acknowledge conversation
    manager = ConversationManager(db)
    await manager.acknowledge_conversation(
        conversation_id=conversation_id,
        responder_id=responder_id,
        custom_message=custom_message
    )

    return {
        "conversation_id": str(conversation_id),
        "status": "acknowledged",
        "message": "Conversation acknowledged successfully"
    }


@router.post(
    "/{conversation_id}/answer",
    summary="Answer conversation",
    description="Provide answer to a question"
)
async def answer_conversation(
    conversation_id: UUID,
    responder_id: UUID,
    answer_content: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Answer a conversation (provide final answer).

    - **conversation_id**: UUID of the conversation
    - **responder_id**: UUID of the responder providing answer
    - **answer_content**: Content of the answer

    Updates conversation state to ANSWERED and clears timeout.
    """
    # Get conversation to verify squad ownership
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    # Get asker to verify squad
    stmt = select(SquadMember).where(SquadMember.id == conversation.asker_id)
    result = await db.execute(stmt)
    asker = result.scalar_one_or_none()

    if asker:
        await SquadService.verify_squad_ownership(db, asker.squad_id, current_user.id)

    # Answer conversation
    manager = ConversationManager(db)
    await manager.answer_conversation(
        conversation_id=conversation_id,
        responder_id=responder_id,
        answer_content=answer_content
    )

    return {
        "conversation_id": str(conversation_id),
        "status": "answered",
        "message": "Conversation answered successfully"
    }


@router.post(
    "/{conversation_id}/escalate",
    summary="Escalate conversation",
    description="Escalate to next level in hierarchy"
)
async def escalate_conversation(
    conversation_id: UUID,
    reason: str = "manual",
    triggered_by_agent_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually escalate a conversation to the next level.

    - **conversation_id**: UUID of the conversation
    - **reason**: Reason for escalation (manual, timeout, cant_help)
    - **triggered_by_agent_id**: Optional agent ID triggering escalation

    Returns escalation result.
    """
    # Get conversation to verify squad ownership
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    # Get asker to verify squad
    stmt = select(SquadMember).where(SquadMember.id == conversation.asker_id)
    result = await db.execute(stmt)
    asker = result.scalar_one_or_none()

    if asker:
        await SquadService.verify_squad_ownership(db, asker.squad_id, current_user.id)

    # Escalate conversation
    escalation_service = EscalationService(db)
    success = await escalation_service.escalate_conversation(
        conversation_id=conversation_id,
        reason=reason,
        triggered_by_agent_id=triggered_by_agent_id
    )

    if success:
        # Refresh conversation to get updated data
        await db.refresh(conversation)
        return {
            "conversation_id": str(conversation_id),
            "status": "escalated",
            "escalation_level": conversation.escalation_level,
            "current_responder_id": str(conversation.current_responder_id),
            "message": "Conversation escalated successfully"
        }
    else:
        return {
            "conversation_id": str(conversation_id),
            "status": "unresolvable",
            "message": "No next level available - conversation marked as unresolvable"
        }


@router.post(
    "/{conversation_id}/cant-help",
    summary="Request routing (can't help)",
    description="Current responder says they can't help"
)
async def handle_cant_help(
    conversation_id: UUID,
    current_responder_id: UUID,
    target_role: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Handle "can't help" request from current responder.

    - **conversation_id**: UUID of the conversation
    - **current_responder_id**: UUID of responder who can't help
    - **target_role**: Optional specific role to route to

    Routes to specific role if provided, otherwise escalates.
    """
    # Get conversation to verify squad ownership
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    # Get asker to verify squad
    stmt = select(SquadMember).where(SquadMember.id == conversation.asker_id)
    result = await db.execute(stmt)
    asker = result.scalar_one_or_none()

    if asker:
        await SquadService.verify_squad_ownership(db, asker.squad_id, current_user.id)

    # Handle can't help
    escalation_service = EscalationService(db)
    success = await escalation_service.handle_cant_help(
        conversation_id=conversation_id,
        current_responder_id=current_responder_id,
        target_role=target_role
    )

    if success:
        await db.refresh(conversation)
        return {
            "conversation_id": str(conversation_id),
            "status": "routed" if target_role else "escalated",
            "current_responder_id": str(conversation.current_responder_id),
            "message": f"Successfully routed to {target_role}" if target_role else "Escalated to next level"
        }
    else:
        return {
            "conversation_id": str(conversation_id),
            "status": "failed",
            "message": "Could not route to target role or escalate"
        }


@router.post(
    "/{conversation_id}/cancel",
    summary="Cancel conversation",
    description="Cancel an ongoing conversation"
)
async def cancel_conversation(
    conversation_id: UUID,
    cancelled_by_id: UUID,
    reason: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Cancel a conversation.

    - **conversation_id**: UUID of the conversation
    - **cancelled_by_id**: UUID of agent cancelling
    - **reason**: Optional cancellation reason
    """
    # Get conversation to verify squad ownership
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    # Get asker to verify squad
    stmt = select(SquadMember).where(SquadMember.id == conversation.asker_id)
    result = await db.execute(stmt)
    asker = result.scalar_one_or_none()

    if asker:
        await SquadService.verify_squad_ownership(db, asker.squad_id, current_user.id)

    # Cancel conversation
    manager = ConversationManager(db)
    await manager.cancel_conversation(
        conversation_id=conversation_id,
        cancelled_by_id=cancelled_by_id,
        reason=reason
    )

    return {
        "conversation_id": str(conversation_id),
        "status": "cancelled",
        "message": "Conversation cancelled successfully"
    }


@router.get(
    "/{conversation_id}",
    summary="Get conversation details",
    description="Get conversation details with current state"
)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get conversation details.

    - **conversation_id**: UUID of the conversation

    Returns conversation with current state.
    """
    # Get conversation
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    # Get asker to verify squad
    stmt = select(SquadMember).where(SquadMember.id == conversation.asker_id)
    result = await db.execute(stmt)
    asker = result.scalar_one_or_none()

    if asker:
        await SquadService.verify_squad_ownership(db, asker.squad_id, current_user.id)

    return {
        "id": str(conversation.id),
        "initial_message_id": str(conversation.initial_message_id),
        "current_state": conversation.current_state,
        "asker_id": str(conversation.asker_id),
        "current_responder_id": str(conversation.current_responder_id),
        "escalation_level": conversation.escalation_level,
        "question_type": conversation.question_type,
        "task_execution_id": str(conversation.task_execution_id) if conversation.task_execution_id else None,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "acknowledged_at": conversation.acknowledged_at.isoformat() if conversation.acknowledged_at else None,
        "resolved_at": conversation.resolved_at.isoformat() if conversation.resolved_at else None,
        "timeout_at": conversation.timeout_at.isoformat() if conversation.timeout_at else None,
        "conv_metadata": conversation.conv_metadata
    }


@router.get(
    "/{conversation_id}/timeline",
    summary="Get conversation timeline",
    description="Get complete event timeline for a conversation"
)
async def get_conversation_timeline(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get complete conversation timeline with all events.

    - **conversation_id**: UUID of the conversation

    Returns conversation details and event timeline.
    """
    # Get conversation to verify existence and ownership
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    # Get asker to verify squad
    stmt = select(SquadMember).where(SquadMember.id == conversation.asker_id)
    result = await db.execute(stmt)
    asker = result.scalar_one_or_none()

    if asker:
        await SquadService.verify_squad_ownership(db, asker.squad_id, current_user.id)

    # Get timeline
    manager = ConversationManager(db)
    timeline = await manager.get_conversation_timeline(conversation_id)

    return timeline


@router.get(
    "/squads/{squad_id}/conversations",
    summary="List squad conversations",
    description="Get all conversations for a squad"
)
async def list_squad_conversations(
    squad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    state: str | None = Query(None, description="Filter by state"),
    question_type: str | None = Query(None, description="Filter by question type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of records to return")
) -> List[Dict[str, Any]]:
    """
    List all conversations for a squad.

    Supports filtering by:
    - **state**: Filter by conversation state
    - **question_type**: Filter by question type

    Supports pagination with skip and limit.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)

    # Build query - join with SquadMember to filter by squad
    conditions = []

    stmt = select(Conversation).join(
        SquadMember,
        Conversation.asker_id == SquadMember.id
    ).where(SquadMember.squad_id == squad_id)

    if state:
        conditions.append(Conversation.current_state == state)
    if question_type:
        conditions.append(Conversation.question_type == question_type)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Conversation.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    conversations = result.scalars().all()

    return [
        {
            "id": str(conv.id),
            "current_state": conv.current_state,
            "asker_id": str(conv.asker_id),
            "current_responder_id": str(conv.current_responder_id),
            "escalation_level": conv.escalation_level,
            "question_type": conv.question_type,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "timeout_at": conv.timeout_at.isoformat() if conv.timeout_at else None
        }
        for conv in conversations
    ]
