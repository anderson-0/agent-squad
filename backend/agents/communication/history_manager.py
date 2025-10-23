"""
Conversation History Manager

Manages storage and retrieval of agent conversation history from the database.
Provides summarization for long conversations to fit within context windows.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.message import AgentMessage
from backend.schemas.agent_message import AgentMessageResponse
from backend.agents.agno_base import ConversationMessage


class HistoryManager:
    """
    Manages agent conversation history.

    Features:
    - Store messages in database
    - Retrieve conversation history
    - Summarize long conversations
    - Filter by time range, agent, message type
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_message(
        self,
        task_execution_id: UUID,
        sender_id: UUID,
        recipient_id: Optional[UUID],
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentMessage:
        """
        Store a message in the database.

        Args:
            task_execution_id: Task execution context
            sender_id: Sending agent ID
            recipient_id: Receiving agent ID (None for broadcast)
            content: Message content
            message_type: Type of message
            metadata: Optional metadata

        Returns:
            Stored AgentMessage
        """
        message = AgentMessage(
            task_execution_id=task_execution_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content,
            message_type=message_type,
            message_metadata=metadata or {},
        )

        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)

        return message

    async def get_conversation_history(
        self,
        task_execution_id: UUID,
        limit: Optional[int] = 50,
        offset: int = 0,
        since: Optional[datetime] = None,
    ) -> List[AgentMessage]:
        """
        Get conversation history for a task execution.

        Args:
            task_execution_id: Task execution ID
            limit: Maximum number of messages
            offset: Number of messages to skip
            since: Only get messages after this time

        Returns:
            List of messages in chronological order
        """
        query = select(AgentMessage).where(
            AgentMessage.task_execution_id == task_execution_id
        )

        # Filter by time if provided
        if since:
            query = query.where(AgentMessage.created_at > since)

        # Order by creation time
        query = query.order_by(AgentMessage.created_at)

        # Apply pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        return list(messages)

    async def get_agent_messages(
        self,
        agent_id: UUID,
        task_execution_id: Optional[UUID] = None,
        limit: int = 50,
        message_type: Optional[str] = None,
    ) -> List[AgentMessage]:
        """
        Get messages sent to or from a specific agent.

        Args:
            agent_id: Agent ID
            task_execution_id: Optional task execution filter
            limit: Maximum number of messages
            message_type: Optional message type filter

        Returns:
            List of messages
        """
        # Messages where agent is sender or recipient
        query = select(AgentMessage).where(
            and_(
                (AgentMessage.sender_id == agent_id) |
                (AgentMessage.recipient_id == agent_id) |
                (AgentMessage.recipient_id == None)  # Broadcast messages
            )
        )

        # Filter by task execution
        if task_execution_id:
            query = query.where(AgentMessage.task_execution_id == task_execution_id)

        # Filter by message type
        if message_type:
            query = query.where(AgentMessage.message_type == message_type)

        # Order by most recent
        query = query.order_by(desc(AgentMessage.created_at)).limit(limit)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        return list(messages)

    async def get_conversation_summary(
        self,
        task_execution_id: UUID,
        max_messages: int = 100,
    ) -> str:
        """
        Get a text summary of a conversation.

        Args:
            task_execution_id: Task execution ID
            max_messages: Maximum messages to include

        Returns:
            Formatted conversation summary
        """
        messages = await self.get_conversation_history(
            task_execution_id=task_execution_id,
            limit=max_messages
        )

        if not messages:
            return "No conversation history."

        # Format messages
        summary_lines = [f"Conversation History ({len(messages)} messages):\n"]

        for msg in messages:
            sender = f"Agent {str(msg.sender_id)[:8]}"
            recipient = "Broadcast" if msg.recipient_id is None else f"Agent {str(msg.recipient_id)[:8]}"
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")

            summary_lines.append(
                f"[{timestamp}] {sender} → {recipient} ({msg.message_type}):\n"
                f"{msg.content[:200]}{'...' if len(msg.content) > 200 else ''}\n"
            )

        return "\n".join(summary_lines)

    async def summarize_conversation(
        self,
        task_execution_id: UUID,
        summarize_older_than_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Summarize a long conversation using LLM.

        This is useful when conversation history is too long for context window.
        Keeps recent messages in full, summarizes older messages.

        Args:
            task_execution_id: Task execution ID
            summarize_older_than_hours: Summarize messages older than this

        Returns:
            Dictionary with 'summary' and 'recent_messages'
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=summarize_older_than_hours)

        # Get all messages
        all_messages = await self.get_conversation_history(
            task_execution_id=task_execution_id,
            limit=None  # Get all
        )

        # Split into old and recent
        old_messages = [m for m in all_messages if m.created_at < cutoff_time]
        recent_messages = [m for m in all_messages if m.created_at >= cutoff_time]

        # If no old messages, no summary needed
        if not old_messages:
            return {
                "summary": None,
                "recent_messages": recent_messages,
                "total_messages": len(all_messages)
            }

        # Create simple summary (in production, use LLM)
        summary = self._create_simple_summary(old_messages)

        return {
            "summary": summary,
            "recent_messages": recent_messages,
            "old_message_count": len(old_messages),
            "recent_message_count": len(recent_messages),
            "total_messages": len(all_messages)
        }

    def _create_simple_summary(self, messages: List[AgentMessage]) -> str:
        """
        Create a simple summary of messages.

        In production, this should use an LLM for better summarization.

        Args:
            messages: List of messages to summarize

        Returns:
            Summary text
        """
        if not messages:
            return "No messages to summarize."

        # Count message types
        type_counts: Dict[str, int] = {}
        for msg in messages:
            type_counts[msg.message_type] = type_counts.get(msg.message_type, 0) + 1

        # Get unique agents
        agent_ids = set()
        for msg in messages:
            agent_ids.add(msg.sender_id)
            if msg.recipient_id:
                agent_ids.add(msg.recipient_id)

        summary_parts = [
            f"Summary of {len(messages)} older messages:",
            f"- {len(agent_ids)} agents participated",
            f"- Message types: {', '.join(f'{t} ({c})' for t, c in type_counts.items())}",
        ]

        # Add key events
        key_messages = [
            m for m in messages
            if m.message_type in ["task_assignment", "task_completion", "human_intervention_required"]
        ]

        if key_messages:
            summary_parts.append("- Key events:")
            for msg in key_messages[:5]:  # Max 5 key events
                summary_parts.append(f"  • {msg.message_type}: {msg.content[:100]}")

        return "\n".join(summary_parts)

    async def get_message_count(
        self,
        task_execution_id: UUID,
        since: Optional[datetime] = None,
    ) -> int:
        """
        Get count of messages in a conversation.

        Args:
            task_execution_id: Task execution ID
            since: Only count messages after this time

        Returns:
            Message count
        """
        from sqlalchemy import func

        query = select(func.count(AgentMessage.id)).where(
            AgentMessage.task_execution_id == task_execution_id
        )

        if since:
            query = query.where(AgentMessage.created_at > since)

        result = await self.db.execute(query)
        count = result.scalar()

        return count or 0

    async def delete_old_messages(
        self,
        older_than_days: int = 30,
    ) -> int:
        """
        Delete messages older than specified days.

        Args:
            older_than_days: Delete messages older than this

        Returns:
            Number of messages deleted
        """
        from sqlalchemy import delete

        cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)

        query = delete(AgentMessage).where(
            AgentMessage.created_at < cutoff_time
        )

        result = await self.db.execute(query)
        await self.db.flush()

        return result.rowcount

    def to_conversation_messages(
        self,
        messages: List[AgentMessage]
    ) -> List[ConversationMessage]:
        """
        Convert database messages to ConversationMessage format.

        Args:
            messages: List of AgentMessage objects

        Returns:
            List of ConversationMessage objects
        """
        conversation_messages = []

        for msg in messages:
            # Determine role (user = other agents, assistant = this agent)
            # This is context-dependent, so we'll use 'user' for all
            conversation_messages.append(
                ConversationMessage(
                    role="user",
                    content=msg.content,
                    metadata={
                        "sender_id": str(msg.sender_id),
                        "recipient_id": str(msg.recipient_id) if msg.recipient_id else None,
                        "message_type": msg.message_type,
                        "created_at": msg.created_at.isoformat(),
                    }
                )
            )

        return conversation_messages
