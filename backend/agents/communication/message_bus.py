"""
Message Bus for Agent-to-Agent Communication

Central hub for routing messages between agents.
Supports point-to-point and broadcast messaging.
"""
from typing import Dict, List, Optional, Callable, Any
from uuid import UUID, uuid4
from datetime import datetime
from collections import defaultdict, deque
import asyncio
import json

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.agent_message import AgentMessageCreate, AgentMessageResponse
from backend.agents.communication.message_utils import (
    get_agent_details,
    get_conversation_thread_id,
)
from backend.models.agent_message import AgentMessage


def get_sse_manager():
    """Lazy import to avoid circular dependency"""
    from backend.services.sse_service import sse_manager
    return sse_manager


class MessageSubscription(BaseModel):
    """Subscription to messages for an agent"""
    agent_id: UUID
    callback: Any  # Callable - Pydantic doesn't validate callables well
    created_at: datetime


class MessageBus:
    """
    Central message bus for agent communication.

    Features:
    - Point-to-point messaging
    - Broadcast messaging
    - Message history
    - Pub/Sub pattern
    - In-memory queue (can be upgraded to Redis/RabbitMQ)
    """

    def __init__(self, max_history_per_agent: int = 1000):
        # Message queues per agent
        self._queues: Dict[UUID, deque] = defaultdict(lambda: deque(maxlen=max_history_per_agent))

        # Broadcast queue (all agents)
        self._broadcast_queue: deque = deque(maxlen=max_history_per_agent)

        # Subscribers (for real-time notifications)
        self._subscribers: Dict[UUID, List[Callable]] = defaultdict(list)

        # All messages (for persistence/history)
        self._all_messages: deque = deque(maxlen=max_history_per_agent * 10)

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def send_message(
        self,
        sender_id: UUID,
        recipient_id: Optional[UUID],
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        task_execution_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> AgentMessageResponse:
        """
        Send a message from one agent to another (or broadcast).

        Args:
            sender_id: ID of sending agent
            recipient_id: ID of receiving agent (None for broadcast)
            content: Message content
            message_type: Type of message (task_assignment, status_update, etc.)
            metadata: Optional metadata
            task_execution_id: Optional task execution context
            db: Optional database session for enriched metadata (agent names, roles)

        Returns:
            Created message
        """
        async with self._lock:
            # Generate unique message ID
            message_id = uuid4()

            # Create message
            message = AgentMessageResponse(
                id=message_id,
                task_execution_id=task_execution_id or UUID(int=0),
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                message_type=message_type,
                message_metadata=metadata or {},
                created_at=datetime.utcnow()
            )

            # Persist to database if db session provided
            if db is not None and task_execution_id is not None:
                try:
                    db_message = AgentMessage(
                        id=message_id,
                        task_execution_id=task_execution_id,
                        sender_id=sender_id,
                        recipient_id=recipient_id,
                        content=content,
                        message_type=message_type,
                        message_metadata=metadata or {}
                    )
                    db.add(db_message)
                    await db.flush()
                    # Update message with database timestamp
                    message.created_at = db_message.created_at
                except Exception as e:
                    # Log error but don't fail message sending
                    print(f"Error persisting message to database: {e}")

            # Store in all messages
            self._all_messages.append(message)

            # Route message
            if recipient_id is None:
                # Broadcast to all agents
                self._broadcast_queue.append(message)
                # Also add to all individual queues
                for agent_queue in self._queues.values():
                    agent_queue.append(message)
            else:
                # Send to specific agent
                self._queues[recipient_id].append(message)

            # Notify subscribers
            await self._notify_subscribers(recipient_id, message)

            # Broadcast to SSE connections if task_execution_id is present
            if task_execution_id:
                try:
                    await self._broadcast_to_sse(
                        execution_id=task_execution_id,
                        message=message,
                        sender_id=sender_id,
                        recipient_id=recipient_id,
                        content=content,
                        message_type=message_type,
                        metadata=metadata,
                        db=db,
                    )
                except Exception as e:
                    # Don't fail message sending if SSE broadcast fails
                    print(f"Error broadcasting to SSE: {e}")

            return message

    async def broadcast_message(
        self,
        sender_id: UUID,
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        task_execution_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> AgentMessageResponse:
        """
        Broadcast a message to all agents.

        Args:
            sender_id: ID of sending agent
            content: Message content
            message_type: Type of message
            metadata: Optional metadata
            task_execution_id: Optional task execution context
            db: Optional database session for enriched metadata

        Returns:
            Created message
        """
        return await self.send_message(
            sender_id=sender_id,
            recipient_id=None,  # None means broadcast
            content=content,
            message_type=message_type,
            metadata=metadata,
            task_execution_id=task_execution_id,
            db=db,
        )

    async def get_messages(
        self,
        agent_id: UUID,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        message_type: Optional[str] = None,
    ) -> List[AgentMessageResponse]:
        """
        Get messages for an agent.

        Args:
            agent_id: Agent ID to get messages for
            since: Only get messages after this time
            limit: Maximum number of messages
            message_type: Filter by message type

        Returns:
            List of messages
        """
        async with self._lock:
            messages = list(self._queues[agent_id])

            # Filter by time
            if since:
                messages = [m for m in messages if m.created_at > since]

            # Filter by type
            if message_type:
                messages = [m for m in messages if m.message_type == message_type]

            # Limit results
            if limit:
                messages = messages[-limit:]

            return messages

    async def get_conversation(
        self,
        task_execution_id: UUID,
        limit: Optional[int] = None,
    ) -> List[AgentMessageResponse]:
        """
        Get all messages for a specific task execution.

        Args:
            task_execution_id: Task execution ID
            limit: Maximum number of messages

        Returns:
            List of messages in chronological order
        """
        async with self._lock:
            messages = [
                m for m in self._all_messages
                if m.task_execution_id == task_execution_id
            ]

            # Sort by created_at
            messages.sort(key=lambda m: m.created_at)

            # Limit results
            if limit:
                messages = messages[-limit:]

            return messages

    async def subscribe(
        self,
        agent_id: UUID,
        callback: Callable[[AgentMessageResponse], None]
    ) -> str:
        """
        Subscribe to real-time messages for an agent.

        Args:
            agent_id: Agent ID to subscribe for
            callback: Async function to call when message arrives

        Returns:
            Subscription ID
        """
        async with self._lock:
            self._subscribers[agent_id].append(callback)
            subscription_id = f"{agent_id}_{len(self._subscribers[agent_id])}"
            return subscription_id

    async def unsubscribe(self, agent_id: UUID, callback: Callable) -> bool:
        """
        Unsubscribe from messages.

        Args:
            agent_id: Agent ID
            callback: Callback function to remove

        Returns:
            True if unsubscribed, False if not found
        """
        async with self._lock:
            if agent_id in self._subscribers and callback in self._subscribers[agent_id]:
                self._subscribers[agent_id].remove(callback)
                return True
            return False

    async def _broadcast_to_sse(
        self,
        execution_id: UUID,
        message: AgentMessageResponse,
        sender_id: UUID,
        recipient_id: Optional[UUID],
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]],
        db: Optional[AsyncSession] = None,
    ):
        """
        Broadcast message to SSE with enriched metadata.

        If db session is provided, enriches message with agent names and roles.

        Args:
            execution_id: Task execution ID
            message: Message object
            sender_id: Sender agent ID
            recipient_id: Recipient agent ID (None for broadcast)
            content: Message content
            message_type: Message type
            metadata: Message metadata
            db: Optional database session for enrichment
        """
        sse_manager = get_sse_manager()

        # Base data
        data = {
            "message_id": str(message.id),
            "sender_id": str(sender_id),
            "recipient_id": str(recipient_id) if recipient_id else None,
            "content": content,
            "message_type": message_type,
            "metadata": metadata or {},
            "timestamp": message.created_at.isoformat(),
        }

        # Enrich with agent details if db is available
        if db:
            try:
                # Get sender details
                sender_details = await get_agent_details(db, sender_id)
                if sender_details:
                    data["sender_role"] = sender_details.role
                    data["sender_name"] = sender_details.name
                    data["sender_specialization"] = sender_details.specialization

                # Get recipient details (if not broadcast)
                if recipient_id:
                    recipient_details = await get_agent_details(db, recipient_id)
                    if recipient_details:
                        data["recipient_role"] = recipient_details.role
                        data["recipient_name"] = recipient_details.name
                        data["recipient_specialization"] = recipient_details.specialization
                else:
                    # Broadcast message
                    data["recipient_role"] = "broadcast"
                    data["recipient_name"] = "All Agents"

                # Add conversation thread ID
                thread_id = get_conversation_thread_id(metadata)
                if thread_id:
                    data["conversation_thread_id"] = thread_id

            except Exception as e:
                # If enrichment fails, log but continue with base data
                print(f"Error enriching message metadata: {e}")

        # Broadcast to SSE
        await sse_manager.broadcast_to_execution(
            execution_id=execution_id,
            event="message",
            data=data
        )

    async def _notify_subscribers(
        self,
        recipient_id: Optional[UUID],
        message: AgentMessageResponse
    ):
        """
        Notify subscribers of new message.

        Args:
            recipient_id: Recipient agent ID (None for broadcast)
            message: Message to send
        """
        # If broadcast, notify all subscribers
        if recipient_id is None:
            for callbacks in self._subscribers.values():
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        print(f"Error notifying subscriber: {e}")
        else:
            # Notify specific agent's subscribers
            if recipient_id in self._subscribers:
                for callback in self._subscribers[recipient_id]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        print(f"Error notifying subscriber: {e}")

    async def clear_agent_messages(self, agent_id: UUID):
        """
        Clear all messages for an agent.

        Args:
            agent_id: Agent ID
        """
        async with self._lock:
            self._queues[agent_id].clear()

    async def clear_all_messages(self):
        """Clear all messages from the bus"""
        async with self._lock:
            self._queues.clear()
            self._broadcast_queue.clear()
            self._all_messages.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "total_messages": len(self._all_messages),
            "agents_with_messages": len(self._queues),
            "total_subscribers": sum(len(subs) for subs in self._subscribers.values()),
            "broadcast_messages": len(self._broadcast_queue),
        }

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"<MessageBus "
            f"messages={stats['total_messages']} "
            f"agents={stats['agents_with_messages']} "
            f"subscribers={stats['total_subscribers']}>"
        )


# Global message bus instance
_message_bus: Optional[MessageBus] = None
_message_bus_type: Optional[str] = None


def get_message_bus():
    """
    Get or create the global message bus instance.

    Returns either in-memory MessageBus or NATS MessageBus based on config.
    Set MESSAGE_BUS environment variable to "memory" or "nats".

    Returns:
        MessageBus or NATSMessageBus instance
    """
    global _message_bus, _message_bus_type

    # Lazy import to avoid circular dependency
    from backend.core.config import Settings
    import os

    # Re-read settings to detect environment changes (important for testing)
    bus_type = os.environ.get('MESSAGE_BUS', 'memory').lower()

    # If bus already exists and type hasn't changed, return it
    if _message_bus is not None and _message_bus_type == bus_type:
        return _message_bus

    # Type changed, need to reset
    if _message_bus is not None and _message_bus_type != bus_type:
        print(f"⚠️  Message bus type changed from {_message_bus_type} to {bus_type}, resetting...")
        _message_bus = None
        _message_bus_type = None

    # Type changed or first initialization
    if bus_type == "nats":
        # Use NATS JetStream message bus
        # Import here to avoid circular dependency
        from backend.agents.communication.nats_message_bus import NATSMessageBus
        from backend.agents.communication.nats_config import NATSConfig

        # Get NATS config from environment variables
        nats_url = os.environ.get('NATS_URL', 'nats://localhost:4222')
        nats_stream_name = os.environ.get('NATS_STREAM_NAME', 'agent-messages')
        nats_max_msgs = int(os.environ.get('NATS_MAX_MSGS', '1000000'))
        nats_max_age_days = int(os.environ.get('NATS_MAX_AGE_DAYS', '7'))
        nats_consumer_name = os.environ.get('NATS_CONSUMER_NAME', 'agent-processor')

        print(f"🚀 Initializing NATS message bus (url={nats_url})")

        # Create config from settings
        config = NATSConfig(
            url=nats_url,
            stream=NATSConfig.model_fields['stream'].default.copy(
                update={
                    "name": nats_stream_name,
                    "max_msgs": nats_max_msgs,
                    "max_age": nats_max_age_days * 24 * 60 * 60,
                }
            ),
            consumer=NATSConfig.model_fields['consumer'].default.copy(
                update={
                    "durable": nats_consumer_name,
                }
            )
        )

        _message_bus = NATSMessageBus(config)
        _message_bus_type = "nats"

        # Note: Connection happens lazily when first message is sent
        # or explicitly via await _message_bus.connect()
        print("✅ NATS message bus initialized (will connect on first use)")

    else:
        # Use in-memory message bus (default)
        print("📝 Using in-memory message bus")
        _message_bus = MessageBus()
        _message_bus_type = "memory"

    return _message_bus


async def reset_message_bus():
    """
    Reset the global message bus (useful for testing).

    If using NATS bus, this will disconnect gracefully.
    """
    global _message_bus, _message_bus_type

    if _message_bus is not None:
        # If NATS bus, disconnect
        if hasattr(_message_bus, 'disconnect'):
            await _message_bus.disconnect()

    _message_bus = None
    _message_bus_type = None
