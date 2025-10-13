"""
Message Bus for Agent-to-Agent Communication

Central hub for routing messages between agents.
Supports point-to-point and broadcast messaging.
"""
from typing import Dict, List, Optional, Callable, Any
from uuid import UUID
from datetime import datetime
from collections import defaultdict, deque
import asyncio
import json

from pydantic import BaseModel

from backend.schemas.agent_message import AgentMessageCreate, AgentMessageResponse


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

        Returns:
            Created message
        """
        async with self._lock:
            # Create message
            message = AgentMessageResponse(
                id=UUID(int=len(self._all_messages)),  # Simple ID generation
                task_execution_id=task_execution_id or UUID(int=0),
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                message_type=message_type,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )

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

            return message

    async def broadcast_message(
        self,
        sender_id: UUID,
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        task_execution_id: Optional[UUID] = None,
    ) -> AgentMessageResponse:
        """
        Broadcast a message to all agents.

        Args:
            sender_id: ID of sending agent
            content: Message content
            message_type: Type of message
            metadata: Optional metadata
            task_execution_id: Optional task execution context

        Returns:
            Created message
        """
        return await self.send_message(
            sender_id=sender_id,
            recipient_id=None,  # None means broadcast
            content=content,
            message_type=message_type,
            metadata=metadata,
            task_execution_id=task_execution_id
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


def get_message_bus() -> MessageBus:
    """
    Get or create the global message bus instance.

    Returns:
        MessageBus instance
    """
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus


def reset_message_bus():
    """Reset the global message bus (useful for testing)"""
    global _message_bus
    _message_bus = None
