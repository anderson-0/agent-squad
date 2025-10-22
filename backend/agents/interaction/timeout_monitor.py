"""
Timeout Monitor

Celery task for monitoring conversation timeouts and triggering:
- Follow-up messages after initial timeout
- Escalation after retry limit exceeded
- State transitions for timed-out conversations
"""
from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_async_session_context
from backend.models import Conversation, ConversationState, ConversationEvent, SquadMember
from backend.agents.configuration.interaction_config import get_interaction_config
from backend.agents.communication.message_bus import get_message_bus
from backend.agents.interaction.escalation_service import EscalationService


class TimeoutMonitor:
    """
    Monitor for conversation timeouts

    This class is responsible for:
    1. Finding conversations that have exceeded their timeout
    2. Sending follow-up messages for initial timeouts
    3. Triggering escalation after retry limit exceeded
    4. Tracking timeout events in conversation history
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize timeout monitor

        Args:
            db: Database session
        """
        self.db = db
        self.config = get_interaction_config()
        self.message_bus = get_message_bus()
        self.escalation_service = EscalationService(db)

    async def check_timeouts(self) -> dict:
        """
        Check all conversations for timeouts and handle appropriately

        Returns:
            Dictionary with statistics about timeouts processed
        """
        now = datetime.utcnow()

        # Find conversations that have timed out
        timed_out_conversations = await self._find_timed_out_conversations(now)

        stats = {
            "checked_at": now.isoformat(),
            "total_timed_out": len(timed_out_conversations),
            "follow_ups_sent": 0,
            "escalations_triggered": 0,
            "errors": []
        }

        for conversation in timed_out_conversations:
            try:
                await self._handle_timeout(conversation, stats)
            except Exception as e:
                stats["errors"].append({
                    "conversation_id": str(conversation.id),
                    "error": str(e)
                })

        return stats

    async def _find_timed_out_conversations(self, now: datetime) -> List[Conversation]:
        """
        Find conversations that have timed out

        Args:
            now: Current timestamp

        Returns:
            List of timed out conversations
        """
        # Query for conversations with timeout_at < now and in active states
        stmt = select(Conversation).where(
            and_(
                Conversation.timeout_at.is_not(None),
                Conversation.timeout_at <= now,
                Conversation.current_state.in_([
                    ConversationState.INITIATED.value,
                    ConversationState.WAITING.value,
                    ConversationState.FOLLOW_UP.value
                ])
            )
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _handle_timeout(self, conversation: Conversation, stats: dict) -> None:
        """
        Handle a timed out conversation

        Decides whether to:
        - Send follow-up message (first timeout)
        - Escalate to next level (retry limit exceeded)

        Args:
            conversation: Timed out conversation
            stats: Statistics dictionary to update
        """
        # Count how many timeout events have already occurred
        stmt = select(ConversationEvent).where(
            and_(
                ConversationEvent.conversation_id == conversation.id,
                ConversationEvent.event_type == "timeout"
            )
        )
        result = await self.db.execute(stmt)
        timeout_events = result.scalars().all()
        timeout_count = len(timeout_events)

        if timeout_count < self.config.timeouts.max_retries:
            # Send follow-up message
            await self._send_follow_up(conversation)
            stats["follow_ups_sent"] += 1
        else:
            # Exceeded retry limit - escalate
            success = await self.escalation_service.escalate_conversation(
                conversation_id=conversation.id,
                reason="timeout",
                triggered_by_agent_id=None  # System triggered
            )

            if success:
                stats["escalations_triggered"] += 1
            else:
                # No next level available - conversation already marked as unresolvable
                stats["escalations_triggered"] += 1  # Count unresolvable as escalation attempt

    async def _send_follow_up(self, conversation: Conversation) -> None:
        """
        Send a follow-up message for a timed out conversation

        Updates conversation state to FOLLOW_UP and sends reminder message

        Args:
            conversation: Timed out conversation
        """
        from datetime import timedelta
        from uuid import uuid4

        # Update conversation state
        old_state = conversation.current_state
        conversation.current_state = ConversationState.FOLLOW_UP.value

        # Set new timeout for retry
        conversation.timeout_at = datetime.utcnow() + timedelta(
            seconds=self.config.timeouts.retry_timeout_seconds
        )

        # Get responder for follow-up message recipient
        stmt = select(SquadMember).where(
            SquadMember.id == conversation.current_responder_id
        )
        result = await self.db.execute(stmt)
        responder = result.scalar_one_or_none()

        # Send follow-up message via message bus
        follow_up_msg = self.config.get_message_template("follow_up")

        message = await self.message_bus.send_message(
            sender_id=conversation.asker_id,
            recipient_id=conversation.current_responder_id,
            content=follow_up_msg,
            message_type="follow_up",
            task_execution_id=conversation.task_execution_id,
            db=self.db
        )

        # Create timeout event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type="timeout",
            from_state=old_state,
            to_state=ConversationState.FOLLOW_UP.value,
            message_id=message.id,
            triggered_by_agent_id=None,  # System triggered
            event_data={
                "timeout_type": "initial",
                "responder_id": str(conversation.current_responder_id),
                "responder_role": responder.role if responder else None
            }
        )

        self.db.add(event)
        await self.db.commit()


# Celery task wrapper
async def check_conversation_timeouts() -> dict:
    """
    Celery task: Check all conversations for timeouts

    This task should be run periodically (e.g., every 60 seconds)
    via Celery Beat.

    Returns:
        Dictionary with timeout processing statistics
    """
    async with get_async_session_context() as db:
        monitor = TimeoutMonitor(db)
        return await monitor.check_timeouts()


# Additional helper for manual timeout checks (useful for testing)
async def check_specific_conversation_timeout(conversation_id: UUID) -> dict:
    """
    Check timeout for a specific conversation

    Useful for:
    - Testing timeout behavior
    - Manual timeout triggers
    - Debugging timeout issues

    Args:
        conversation_id: ID of conversation to check

    Returns:
        Dictionary with result of timeout check
    """
    async with get_async_session_context() as db:
        monitor = TimeoutMonitor(db)
        now = datetime.utcnow()

        # Get specific conversation
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation is None:
            return {"error": f"Conversation not found: {conversation_id}"}

        if conversation.timeout_at is None:
            return {"message": "Conversation has no timeout set"}

        if conversation.timeout_at > now:
            return {
                "message": "Conversation has not timed out yet",
                "timeout_at": conversation.timeout_at.isoformat(),
                "time_remaining_seconds": (conversation.timeout_at - now).total_seconds()
            }

        # Handle timeout
        stats = {
            "checked_at": now.isoformat(),
            "total_timed_out": 1,
            "follow_ups_sent": 0,
            "escalations_triggered": 0,
            "errors": []
        }

        try:
            await monitor._handle_timeout(conversation, stats)
        except Exception as e:
            stats["errors"].append({
                "conversation_id": str(conversation_id),
                "error": str(e)
            })

        return stats
