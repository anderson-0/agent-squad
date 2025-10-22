"""
NATS JetStream Message Bus Implementation

Distributed message bus using NATS JetStream for agent communication.
Provides same interface as in-memory MessageBus but with:
- Horizontal scaling across multiple servers
- Message persistence and replay
- Sub-millisecond latency
- No single point of failure
"""
from typing import Dict, List, Optional, Callable, Any
from uuid import UUID, uuid4
from datetime import datetime
import asyncio
import json
import logging

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from nats.js.api import StreamConfig, ConsumerConfig, DeliverPolicy, AckPolicy, ReplayPolicy
from nats.errors import TimeoutError as NATSTimeoutError, ConnectionClosedError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.agent_message import AgentMessageResponse
from backend.agents.communication.message_utils import (
    get_agent_details,
    get_conversation_thread_id,
)
from backend.agents.communication.nats_config import NATSConfig, default_nats_config
from backend.models.agent_message import AgentMessage

logger = logging.getLogger(__name__)


def get_sse_manager():
    """Lazy import to avoid circular dependency"""
    from backend.services.sse_service import sse_manager
    return sse_manager


class NATSMessageBus:
    """
    NATS JetStream implementation of MessageBus.

    Features:
    - Distributed messaging (multi-server)
    - Message persistence (survives restarts)
    - Message replay (event sourcing)
    - Sub-millisecond latency
    - Automatic reconnection
    - Same interface as in-memory MessageBus
    """

    def __init__(self, config: Optional[NATSConfig] = None):
        """
        Initialize NATS message bus.

        Args:
            config: NATS configuration (uses default if not provided)
        """
        self.config = config or default_nats_config
        self._nc: Optional[NATS] = None
        self._js: Optional[JetStreamContext] = None
        self._connected = False
        self._subscribers: Dict[UUID, List[Callable]] = {}
        self._consumer_tasks: List[asyncio.Task] = []
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """
        Connect to NATS server and setup JetStream.

        Raises:
            ConnectionError: If unable to connect to NATS
        """
        if self._connected:
            logger.warning("Already connected to NATS")
            return

        try:
            logger.info(f"Connecting to NATS at {self.config.url}")

            # Create NATS client
            self._nc = NATS()

            # Connect with reconnection settings
            await self._nc.connect(
                servers=[self.config.url],
                name=self.config.name,
                max_reconnect_attempts=self.config.max_reconnect_attempts,
                reconnect_time_wait=self.config.reconnect_time_wait,
                error_cb=self._error_callback,
                disconnected_cb=self._disconnected_callback,
                reconnected_cb=self._reconnected_callback,
            )

            # Get JetStream context
            self._js = self._nc.jetstream()

            # Setup stream
            await self._setup_stream()

            self._connected = True
            logger.info("Successfully connected to NATS JetStream")

        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise ConnectionError(f"Cannot connect to NATS: {e}")

    async def disconnect(self) -> None:
        """
        Gracefully disconnect from NATS.
        """
        if not self._connected:
            return

        logger.info("Disconnecting from NATS")

        # Cancel consumer tasks
        for task in self._consumer_tasks:
            if not task.done():
                task.cancel()

        if self._consumer_tasks:
            await asyncio.gather(*self._consumer_tasks, return_exceptions=True)

        # Close connection
        if self._nc:
            await self._nc.close()

        self._connected = False
        logger.info("Disconnected from NATS")

    async def _setup_stream(self) -> None:
        """
        Create or update JetStream stream.
        """
        if not self._js:
            raise RuntimeError("JetStream not initialized")

        try:
            # Try to get existing stream
            await self._js.stream_info(self.config.stream.name)
            logger.info(f"Stream '{self.config.stream.name}' already exists")
        except Exception:
            # Stream doesn't exist, create it
            logger.info(f"Creating stream '{self.config.stream.name}'")
            stream_config = StreamConfig(
                name=self.config.stream.name,
                subjects=self.config.stream.subjects,
                retention="limits",
                max_msgs=self.config.stream.max_msgs,
                max_age=self.config.stream.max_age,
                storage="file",
                max_msg_size=self.config.stream.max_msg_size,
                discard="old",
                duplicate_window=self.config.stream.duplicate_window,
            )
            await self._js.add_stream(config=stream_config)
            logger.info(f"Stream '{self.config.stream.name}' created successfully")

    def _get_subject(
        self,
        message_type: str,
        sender_id: Optional[UUID] = None,
        recipient_id: Optional[UUID] = None,
    ) -> str:
        """
        Generate NATS subject from message parameters.

        Format: agent.message.<message_type>
        Examples:
        - agent.message.task_assignment
        - agent.message.status_update
        - agent.message.question

        Args:
            message_type: Type of message
            sender_id: Optional sender ID (for future routing)
            recipient_id: Optional recipient ID (for future routing)

        Returns:
            NATS subject string
        """
        return f"agent.message.{message_type}"

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
        Send a message via NATS JetStream.

        Args:
            sender_id: ID of sending agent
            recipient_id: ID of receiving agent (None for broadcast)
            content: Message content
            message_type: Type of message (task_assignment, status_update, etc.)
            metadata: Optional metadata
            task_execution_id: Optional task execution context
            db: Optional database session for enriched metadata

        Returns:
            Created message

        Raises:
            RuntimeError: If not connected to NATS
            TimeoutError: If publish times out
        """
        if not self._connected or not self._js:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        async with self._lock:
            # Generate unique message ID
            message_id = uuid4()

            # Create message object
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
                    logger.error(f"Error persisting message to database: {e}")

            # Prepare message payload for NATS
            payload = {
                "id": str(message_id),
                "task_execution_id": str(task_execution_id) if task_execution_id else None,
                "sender_id": str(sender_id),
                "recipient_id": str(recipient_id) if recipient_id else None,
                "content": content,
                "message_type": message_type,
                "metadata": metadata or {},
                "created_at": message.created_at.isoformat(),
            }

            # Publish to NATS JetStream
            subject = self._get_subject(message_type, sender_id, recipient_id)

            try:
                ack = await asyncio.wait_for(
                    self._js.publish(
                        subject=subject,
                        payload=json.dumps(payload).encode('utf-8'),
                    ),
                    timeout=self.config.publish_timeout
                )
                logger.debug(
                    f"Published message {message_id} to NATS: "
                    f"seq={ack.seq}, stream={ack.stream}"
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout publishing message {message_id} to NATS")
                raise TimeoutError("NATS publish timeout")
            except Exception as e:
                logger.error(f"Error publishing to NATS: {e}")
                raise

            # Notify local subscribers (for real-time callbacks)
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
                    logger.error(f"Error broadcasting to SSE: {e}")

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
        Broadcast a message to all agents via NATS.

        Args:
            sender_id: ID of sending agent
            content: Message content
            message_type: Type of message
            metadata: Optional metadata
            task_execution_id: Optional task execution context
            db: Optional database session

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
        Get messages for an agent from database (not NATS).

        Note: NATS is for real-time delivery. For querying, we use the database.

        Args:
            agent_id: Agent ID to get messages for
            since: Only get messages after this time
            limit: Maximum number of messages
            message_type: Filter by message type

        Returns:
            List of messages
        """
        # This method queries the database, not NATS
        # NATS is for delivery, database is for querying
        # Implementation would use SQLAlchemy query
        logger.warning(
            "get_messages() should query database, not NATS. "
            "Use history_manager.get_agent_messages() instead."
        )
        return []

    async def get_conversation(
        self,
        task_execution_id: UUID,
        limit: Optional[int] = None,
    ) -> List[AgentMessageResponse]:
        """
        Get all messages for a specific task execution from database.

        Note: NATS is for real-time delivery. For querying, we use the database.

        Args:
            task_execution_id: Task execution ID
            limit: Maximum number of messages

        Returns:
            List of messages in chronological order
        """
        # This method queries the database, not NATS
        logger.warning(
            "get_conversation() should query database, not NATS. "
            "Use history_manager.get_conversation_history() instead."
        )
        return []

    async def subscribe(
        self,
        agent_id: UUID,
        callback: Callable[[AgentMessageResponse], None]
    ) -> str:
        """
        Subscribe to real-time messages for an agent.

        This is for in-process callbacks, not distributed subscriptions.
        For distributed consumption, use NATS pull subscribers.

        Args:
            agent_id: Agent ID to subscribe for
            callback: Async function to call when message arrives

        Returns:
            Subscription ID
        """
        async with self._lock:
            if agent_id not in self._subscribers:
                self._subscribers[agent_id] = []
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

        Same implementation as in-memory bus.

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
                logger.error(f"Error enriching message metadata: {e}")

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
        Notify local subscribers of new message.

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
                        logger.error(f"Error notifying subscriber: {e}")
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
                        logger.error(f"Error notifying subscriber: {e}")

    async def clear_agent_messages(self, agent_id: UUID):
        """
        Clear messages for an agent.

        Note: In NATS mode, this doesn't make sense (messages are in stream).
        This is here for interface compatibility only.
        """
        logger.warning(
            "clear_agent_messages() not supported in NATS mode. "
            "Messages are stored in JetStream stream."
        )

    async def clear_all_messages(self):
        """
        Clear all messages.

        Note: In NATS mode, this would require deleting/recreating the stream.
        This is here for interface compatibility only.
        """
        logger.warning(
            "clear_all_messages() not supported in NATS mode. "
            "To clear messages, delete and recreate the JetStream stream."
        )

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics from NATS.

        Returns:
            Dictionary with stats
        """
        if not self._connected or not self._js:
            return {
                "connected": False,
                "error": "Not connected to NATS"
            }

        try:
            # Get stream info
            stream_info = await self._js.stream_info(self.config.stream.name)

            return {
                "connected": True,
                "stream_name": stream_info.config.name,
                "total_messages": stream_info.state.messages,
                "total_bytes": stream_info.state.bytes,
                "first_seq": stream_info.state.first_seq,
                "last_seq": stream_info.state.last_seq,
                "consumer_count": stream_info.state.consumer_count,
                "local_subscribers": sum(len(subs) for subs in self._subscribers.values()),
            }
        except Exception as e:
            logger.error(f"Error getting NATS stats: {e}")
            return {
                "connected": True,
                "error": str(e)
            }

    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"<NATSMessageBus status={status} url={self.config.url}>"

    # Callback handlers for NATS events

    async def _error_callback(self, error):
        """Called when NATS encounters an error"""
        logger.error(f"NATS error: {error}")

    async def _disconnected_callback(self):
        """Called when disconnected from NATS"""
        logger.warning("Disconnected from NATS server")

    async def _reconnected_callback(self):
        """Called when reconnected to NATS"""
        logger.info("Reconnected to NATS server")


# Global NATS message bus instance
_nats_message_bus: Optional[NATSMessageBus] = None


async def get_nats_message_bus(config: Optional[NATSConfig] = None) -> NATSMessageBus:
    """
    Get or create the global NATS message bus instance.

    Args:
        config: Optional NATS configuration

    Returns:
        NATSMessageBus instance
    """
    global _nats_message_bus
    if _nats_message_bus is None:
        _nats_message_bus = NATSMessageBus(config)
        await _nats_message_bus.connect()
    return _nats_message_bus


async def reset_nats_message_bus():
    """Reset the global NATS message bus (useful for testing)"""
    global _nats_message_bus
    if _nats_message_bus is not None:
        await _nats_message_bus.disconnect()
    _nats_message_bus = None
