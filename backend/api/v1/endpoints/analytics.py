"""
Squad Analytics API Endpoints

Provides analytics and statistics for squads and squad members.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.squad_analytics_service import SquadAnalyticsService


router = APIRouter()


@router.get("/squads/{squad_id}/stats")
async def get_squad_statistics(
    squad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated statistics for entire squad.

    Returns:
    - Total tokens consumed by all members
    - Total messages sent
    - Per-member breakdown
    """
    try:
        stats = await SquadAnalyticsService.get_squad_stats(db, squad_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving squad stats: {str(e)}")


@router.get("/squad-members/{member_id}/stats")
async def get_member_statistics(
    member_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive statistics for a specific squad member.

    Returns:
    - Token usage (input/output/total)
    - Message counts (sent/received)
    - Last activity timestamps
    """
    try:
        stats = await SquadAnalyticsService.get_member_stats(db, member_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving member stats: {str(e)}")


@router.get("/squads/{squad_id}/communication-matrix")
async def get_communication_matrix(
    squad_id: UUID,
    since_days: Optional[int] = Query(None, description="Filter messages from last N days"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get communication matrix showing who talks to whom in the squad.

    Returns pairwise message counts between all squad members.

    Query Parameters:
    - since_days: Optional filter to show communication from last N days

    Example response:
    {
        "squad_id": "...",
        "members": [...],
        "communication_matrix": {
            "member_a_id": {
                "member_b_id": 15,  # 15 messages from A to B
                "member_c_id": 3
            },
            ...
        }
    }
    """
    try:
        since = None
        if since_days is not None:
            since = datetime.utcnow() - timedelta(days=since_days)

        matrix = await SquadAnalyticsService.get_communication_matrix(db, squad_id, since)
        return matrix
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving communication matrix: {str(e)}")


@router.get("/conversations/between")
async def get_conversations_between_members(
    member_a_id: UUID = Query(..., description="First member ID"),
    member_b_id: UUID = Query(..., description="Second member ID"),
    limit: int = Query(100, ge=1, le=500, description="Max messages to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    since_days: Optional[int] = Query(None, description="Filter messages from last N days"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all messages exchanged between two specific squad members.

    Returns bidirectional conversation (A→B and B→A messages).

    Query Parameters:
    - member_a_id: First member UUID
    - member_b_id: Second member UUID
    - limit: Max messages to return (default: 100, max: 500)
    - offset: Offset for pagination (default: 0)
    - since_days: Optional filter for recent messages

    Example response:
    {
        "member_a_id": "...",
        "member_b_id": "...",
        "total_messages": 42,
        "returned_messages": 42,
        "messages": [
            {
                "id": "...",
                "sender_id": "...",
                "recipient_id": "...",
                "content": "...",
                "message_type": "question",
                "created_at": "2025-10-23T..."
            },
            ...
        ]
    }
    """
    try:
        since = None
        until = None

        if since_days is not None:
            since = datetime.utcnow() - timedelta(days=since_days)

        conversations = await SquadAnalyticsService.get_conversations_between_members(
            db=db,
            member_a_id=member_a_id,
            member_b_id=member_b_id,
            limit=limit,
            offset=offset,
            since=since,
            until=until
        )
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversations: {str(e)}")


@router.post("/squad-members/{member_id}/stats/tokens")
async def update_member_token_usage(
    member_id: UUID,
    input_tokens: int = Query(..., ge=0, description="Input tokens consumed"),
    output_tokens: int = Query(..., ge=0, description="Output tokens consumed"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update token usage for a squad member.

    Call this endpoint after each LLM call to track token consumption.

    Body Parameters:
    - input_tokens: Number of input tokens consumed
    - output_tokens: Number of output tokens consumed

    Returns updated stats.
    """
    try:
        stats = await SquadAnalyticsService.update_token_usage(
            db=db,
            squad_member_id=member_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        return {
            "squad_member_id": str(member_id),
            "total_input_tokens": stats.total_input_tokens,
            "total_output_tokens": stats.total_output_tokens,
            "total_tokens": stats.total_tokens,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating token usage: {str(e)}")


@router.post("/squad-members/{member_id}/stats/message-sent")
async def record_message_sent(
    member_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Record that a squad member sent a message.

    Call this endpoint when a member sends a message.

    Returns updated stats.
    """
    try:
        stats = await SquadAnalyticsService.update_message_sent(
            db=db,
            squad_member_id=member_id
        )
        return {
            "squad_member_id": str(member_id),
            "total_messages_sent": stats.total_messages_sent,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording message sent: {str(e)}")


@router.post("/squad-members/{member_id}/stats/message-received")
async def record_message_received(
    member_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Record that a squad member received a message.

    Call this endpoint when a member receives a message.

    Returns updated stats.
    """
    try:
        stats = await SquadAnalyticsService.update_message_received(
            db=db,
            squad_member_id=member_id
        )
        return {
            "squad_member_id": str(member_id),
            "total_messages_received": stats.total_messages_received,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording message received: {str(e)}")
