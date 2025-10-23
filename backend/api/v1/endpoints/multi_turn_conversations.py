"""
Multi-Turn Conversation API Endpoints

REST API for universal multi-turn conversations (user-agent, agent-agent, multi-party).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from backend.core.database import get_db
from backend.services.conversation_service import ConversationService
from backend.schemas import (
    CreateUserAgentConversationRequest,
    CreateAgentAgentConversationRequest,
    MultiTurnConversationResponse,
    ConversationWithMessagesResponse,
    ConversationListResponse,
    SendMessageRequest,
    MessageResponse,
    MessageListResponse,
    ConversationHistoryResponse,
    AddParticipantRequest,
    ParticipantResponse,
    ParticipantListResponse,
    UpdateConversationTitleRequest,
    UpdateConversationSummaryRequest,
)
from backend.core.logging import logger

router = APIRouter()


# ============================================================================
# CONVERSATION CREATION
# ============================================================================

@router.post("/user-agent", response_model=MultiTurnConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_user_agent_conversation(
    request: CreateUserAgentConversationRequest,
    user_id: UUID = Query(..., description="ID of the user creating the conversation"),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user-agent conversation.

    Creates a conversation between a user and an AI agent with message history support.
    """
    try:
        conversation = await ConversationService.create_user_agent_conversation(
            db=db,
            user_id=user_id,
            agent_id=request.agent_id,
            title=request.title,
            tags=request.tags,
            metadata=request.metadata
        )
        return conversation.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user-agent conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create conversation")


@router.post("/agent-agent", response_model=MultiTurnConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_agent_conversation(
    request: CreateAgentAgentConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new agent-agent conversation.

    Creates a conversation between two AI agents for collaborative work.
    """
    try:
        conversation = await ConversationService.create_agent_agent_conversation(
            db=db,
            initiator_agent_id=request.initiator_agent_id,
            responder_agent_id=request.responder_agent_id,
            title=request.title,
            agent_conversation_id=request.agent_conversation_id,
            tags=request.tags,
            metadata=request.metadata
        )
        return conversation.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating agent-agent conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create conversation")


# ============================================================================
# CONVERSATION RETRIEVAL
# ============================================================================

@router.get("/{conversation_id}", response_model=MultiTurnConversationResponse)
async def get_conversation(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a conversation by ID.

    Returns conversation metadata without messages. Use /messages endpoint to get messages.
    """
    conversation = await ConversationService.get_conversation(
        db=db,
        conversation_id=conversation_id,
        include_messages=False,
        include_participants=False
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return conversation.to_dict()


@router.get("/{conversation_id}/with-messages", response_model=ConversationWithMessagesResponse)
async def get_conversation_with_messages(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a conversation with all messages included.

    Returns full conversation including message history.
    """
    conversation = await ConversationService.get_conversation(
        db=db,
        conversation_id=conversation_id,
        include_messages=True,
        include_participants=True
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Build response with messages
    response = conversation.to_dict()
    response["messages"] = [msg.to_dict() for msg in conversation.messages]
    response["participant_count"] = len(conversation.participants)

    return response


@router.get("/user/{user_id}", response_model=ConversationListResponse)
async def get_user_conversations(
    user_id: UUID = Path(..., description="ID of the user"),
    status: Optional[str] = Query(None, description="Filter by status (active, archived, closed)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all conversations for a user.

    Returns paginated list of conversations for the specified user.
    """
    conversations, total_count = await ConversationService.get_user_conversations(
        db=db,
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset
    )

    return {
        "conversations": [conv.to_dict() for conv in conversations],
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/agent/{agent_id}", response_model=ConversationListResponse)
async def get_agent_conversations(
    agent_id: UUID = Path(..., description="ID of the agent"),
    conversation_type: Optional[str] = Query(None, description="Filter by type (user_agent, agent_agent, multi_party)"),
    status: Optional[str] = Query(None, description="Filter by status (active, archived, closed)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all conversations for an agent.

    Returns paginated list of conversations where the agent is a participant.
    """
    conversations, total_count = await ConversationService.get_agent_conversations(
        db=db,
        agent_id=agent_id,
        conversation_type=conversation_type,
        status=status,
        limit=limit,
        offset=offset
    )

    return {
        "conversations": [conv.to_dict() for conv in conversations],
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }


# ============================================================================
# MESSAGE OPERATIONS
# ============================================================================

@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    request: SendMessageRequest = ...,
    sender_id: UUID = Query(..., description="ID of the sender (user or agent)"),
    sender_type: str = Query(..., description="Type of sender: 'user' or 'agent'"),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message in a conversation.

    Adds a new message to the conversation from either a user or agent.
    """
    if sender_type not in ["user", "agent"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sender_type must be 'user' or 'agent'"
        )

    try:
        message = await ConversationService.send_message(
            db=db,
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=request.content,
            role=request.role.value,
            metadata=request.metadata
        )
        return message.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send message")


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of messages"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages in a conversation.

    Returns paginated list of messages ordered by creation time.
    """
    messages, total_count = await ConversationService.get_conversation_history(
        db=db,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset
    )

    return {
        "messages": [msg.to_dict() for msg in messages],
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/{conversation_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of messages"),
    max_tokens: Optional[int] = Query(None, description="Maximum total tokens to include (for context window)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation history with context window support.

    Returns messages suitable for LLM context, optionally limited by token count.
    """
    conversation = await ConversationService.get_conversation(db=db, conversation_id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages, total_count = await ConversationService.get_conversation_history(
        db=db,
        conversation_id=conversation_id,
        limit=limit,
        offset=0,
        max_tokens=max_tokens
    )

    return {
        "conversation_id": conversation_id,
        "messages": [msg.to_dict() for msg in messages],
        "total_messages": total_count,
        "total_tokens": conversation.total_tokens_used,
        "context_window_tokens": sum(msg.total_tokens or 0 for msg in messages)
    }


# ============================================================================
# CONVERSATION MANAGEMENT
# ============================================================================

@router.patch("/{conversation_id}/title", response_model=MultiTurnConversationResponse)
async def update_conversation_title(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    request: UpdateConversationTitleRequest = ...,
    db: AsyncSession = Depends(get_db)
):
    """
    Update conversation title.
    """
    try:
        conversation = await ConversationService.update_conversation_title(
            db=db,
            conversation_id=conversation_id,
            title=request.title
        )
        return conversation.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating conversation title: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update title")


@router.patch("/{conversation_id}/summary", response_model=MultiTurnConversationResponse)
async def update_conversation_summary(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    request: UpdateConversationSummaryRequest = ...,
    db: AsyncSession = Depends(get_db)
):
    """
    Update conversation summary.
    """
    try:
        conversation = await ConversationService.update_conversation_summary(
            db=db,
            conversation_id=conversation_id,
            summary=request.summary
        )
        return conversation.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating conversation summary: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update summary")


@router.post("/{conversation_id}/archive", response_model=MultiTurnConversationResponse)
async def archive_conversation(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    db: AsyncSession = Depends(get_db)
):
    """
    Archive a conversation.

    Archived conversations are preserved but removed from active lists.
    """
    try:
        conversation = await ConversationService.archive_conversation(
            db=db,
            conversation_id=conversation_id
        )
        return conversation.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error archiving conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to archive conversation")


@router.post("/{conversation_id}/close", response_model=MultiTurnConversationResponse)
async def close_conversation(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    db: AsyncSession = Depends(get_db)
):
    """
    Close a conversation.

    Closed conversations cannot receive new messages.
    """
    try:
        conversation = await ConversationService.close_conversation(
            db=db,
            conversation_id=conversation_id
        )
        return conversation.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error closing conversation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to close conversation")


# ============================================================================
# PARTICIPANT MANAGEMENT
# ============================================================================

@router.post("/{conversation_id}/participants", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
async def add_participant(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    request: AddParticipantRequest = ...,
    db: AsyncSession = Depends(get_db)
):
    """
    Add a participant to a conversation.

    Converts conversation to multi-party if needed.
    """
    try:
        participant = await ConversationService.add_participant(
            db=db,
            conversation_id=conversation_id,
            participant_id=request.participant_id,
            participant_type=request.participant_type.value,
            role=request.role.value,
            metadata=request.metadata
        )
        return participant.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding participant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add participant")


@router.delete("/{conversation_id}/participants/{participant_id}/{participant_type}", response_model=ParticipantResponse)
async def remove_participant(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    participant_id: UUID = Path(..., description="ID of the participant"),
    participant_type: str = Path(..., description="Type of participant: 'user' or 'agent'"),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove (deactivate) a participant from a conversation.
    """
    if participant_type not in ["user", "agent"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="participant_type must be 'user' or 'agent'"
        )

    try:
        participant = await ConversationService.remove_participant(
            db=db,
            conversation_id=conversation_id,
            participant_id=participant_id,
            participant_type=participant_type
        )
        return participant.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing participant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove participant")


@router.get("/{conversation_id}/participants", response_model=ParticipantListResponse)
async def get_conversation_participants(
    conversation_id: UUID = Path(..., description="ID of the conversation"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all participants in a conversation.
    """
    conversation = await ConversationService.get_conversation(
        db=db,
        conversation_id=conversation_id,
        include_participants=True
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return {
        "participants": [p.to_dict() for p in conversation.participants],
        "total_count": len(conversation.participants)
    }
