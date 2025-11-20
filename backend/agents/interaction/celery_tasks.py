"""
Celery Tasks for Agent Interactions

This module contains Celery tasks for:
- Periodic timeout monitoring
- Conversation cleanup
- Analytics and reporting
"""
import asyncio
from typing import Optional
from uuid import UUID

from backend.agents.interaction.celery_config import celery_app, run_async_task
from backend.agents.interaction.timeout_monitor import (
    check_conversation_timeouts,
    check_specific_conversation_timeout
)
from backend.agents.configuration.interaction_config import get_interaction_config


# Get configuration
config = get_interaction_config()


@celery_app.task(
    name='backend.agents.interaction.celery_tasks.check_timeouts_task',
    bind=True,
    max_retries=config.celery.task_max_retries,
    default_retry_delay=config.celery.task_retry_delay
)
def check_timeouts_task(self):
    """
    Celery task: Check all conversations for timeouts

    This is the main periodic task that runs every 60 seconds (configurable)
    to check for conversation timeouts and trigger follow-ups or escalations.

    The task:
    1. Finds all conversations with timeout_at <= now()
    2. Determines if follow-up or escalation is needed
    3. Sends messages and updates conversation state
    4. Logs all timeout events

    Returns:
        Dictionary with processing statistics
    """
    try:
        # Run the async timeout check
        result = run_async_task(check_conversation_timeouts())
        return result
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc)


@celery_app.task(
    name='backend.agents.interaction.celery_tasks.check_specific_timeout_task',
    bind=True,
    max_retries=config.celery.task_max_retries,
    default_retry_delay=config.celery.task_retry_delay
)
def check_specific_timeout_task(self, conversation_id: str):
    """
    Celery task: Check timeout for a specific conversation

    Useful for:
    - Manual timeout triggers
    - Testing timeout behavior
    - Debugging specific conversations

    Args:
        conversation_id: UUID of conversation as string

    Returns:
        Dictionary with timeout check result
    """
    try:
        conv_id = UUID(conversation_id)
        result = run_async_task(check_specific_conversation_timeout(conv_id))
        return result
    except ValueError as e:
        return {"error": f"Invalid conversation ID: {conversation_id}"}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name='backend.agents.interaction.celery_tasks.cleanup_old_conversations_task'
)
def cleanup_old_conversations_task(days_old: int = 30):
    """
    Celery task: Clean up old resolved conversations

    Removes conversation data older than specified days to prevent
    database bloat. Only removes conversations in terminal states:
    - ANSWERED
    - CANCELLED
    - unresolvable

    Args:
        days_old: Number of days after which to clean up (default: 30)

    Returns:
        Dictionary with cleanup statistics
    """
    try:
        result = run_async_task(_cleanup_old_conversations(days_old))
        return result
    except Exception as exc:
        return {"error": str(exc)}


async def _cleanup_old_conversations(days_old: int) -> dict:
    """
    Internal async function to clean up old conversations

    Args:
        days_old: Number of days threshold

    Returns:
        Dictionary with cleanup statistics
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select, delete, and_
    from backend.core.database import get_async_session_context
    from backend.models import Conversation, ConversationEvent

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        async with get_db_context() as db:
        # Find old conversations in terminal states
        stmt = select(Conversation).where(
            and_(
                Conversation.resolved_at.is_not(None),
                Conversation.resolved_at <= cutoff_date,
                Conversation.current_state.in_(['answered', 'cancelled', 'unresolvable'])
            )
        )
        result = await db.execute(stmt)
        conversations_to_delete = result.scalars().all()

        conversation_ids = [c.id for c in conversations_to_delete]

        if not conversation_ids:
            return {
                "conversations_deleted": 0,
                "events_deleted": 0,
                "cutoff_date": cutoff_date.isoformat()
            }

        # Delete associated events first (foreign key constraint)
        stmt = delete(ConversationEvent).where(
            ConversationEvent.conversation_id.in_(conversation_ids)
        )
        events_result = await db.execute(stmt)
        events_deleted = events_result.rowcount

        # Delete conversations
        stmt = delete(Conversation).where(
            Conversation.id.in_(conversation_ids)
        )
        conv_result = await db.execute(stmt)
        conversations_deleted = conv_result.rowcount

        await db.commit()

        return {
            "conversations_deleted": conversations_deleted,
            "events_deleted": events_deleted,
            "cutoff_date": cutoff_date.isoformat(),
            "conversation_ids": [str(cid) for cid in conversation_ids]
        }


@celery_app.task(
    name='backend.agents.interaction.celery_tasks.generate_timeout_report_task'
)
def generate_timeout_report_task(days: int = 7):
    """
    Celery task: Generate timeout analytics report

    Generates a report showing:
    - Number of timeouts per day
    - Average time to timeout
    - Most common timeout reasons
    - Escalation success rate
    - Most problematic agent roles

    Args:
        days: Number of days to analyze (default: 7)

    Returns:
        Dictionary with analytics
    """
    try:
        result = run_async_task(_generate_timeout_report(days))
        return result
    except Exception as exc:
        return {"error": str(exc)}


async def _generate_timeout_report(days: int) -> dict:
    """
    Internal async function to generate timeout analytics

    Args:
        days: Number of days to analyze

    Returns:
        Dictionary with analytics data
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select, func, and_
    from backend.core.database import get_async_session_context
    from backend.models import ConversationEvent, Conversation

    start_date = datetime.utcnow() - timedelta(days=days)

        async with get_db_context() as db:
        # Count timeout events
        stmt = select(func.count(ConversationEvent.id)).where(
            and_(
                ConversationEvent.event_type == "timeout",
                ConversationEvent.created_at >= start_date
            )
        )
        result = await db.execute(stmt)
        total_timeouts = result.scalar()

        # Count escalation events
        stmt = select(func.count(ConversationEvent.id)).where(
            and_(
                ConversationEvent.event_type == "escalated",
                ConversationEvent.created_at >= start_date
            )
        )
        result = await db.execute(stmt)
        total_escalations = result.scalar()

        # Count unresolvable events
        stmt = select(func.count(ConversationEvent.id)).where(
            and_(
                ConversationEvent.event_type == "unresolvable",
                ConversationEvent.created_at >= start_date
            )
        )
        result = await db.execute(stmt)
        total_unresolvable = result.scalar()

        # Get average escalation level for resolved conversations
        stmt = select(func.avg(Conversation.escalation_level)).where(
            and_(
                Conversation.resolved_at >= start_date,
                Conversation.current_state == "answered"
            )
        )
        result = await db.execute(stmt)
        avg_escalation_level = result.scalar() or 0

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "total_timeouts": total_timeouts,
            "total_escalations": total_escalations,
            "total_unresolvable": total_unresolvable,
            "average_escalation_level": float(avg_escalation_level),
            "escalation_success_rate": (
                (total_escalations - total_unresolvable) / total_escalations * 100
                if total_escalations > 0 else 0
            )
        }
