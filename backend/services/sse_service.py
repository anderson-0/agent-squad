"""
Server-Sent Events (SSE) Service

Manages real-time streaming connections for agent messages and execution updates.
"""
import asyncio
import json
from typing import Dict, Set, Any, Optional, AsyncGenerator
from uuid import UUID
from datetime import datetime
from collections import defaultdict

from backend.core.logging import logger


class SSEConnectionManager:
    """
    SSE Connection Manager

    Manages active SSE connections and broadcasts events to subscribers.
    Supports per-execution and per-squad subscriptions.
    """

    def __init__(self):
        """Initialize connection manager"""
        # Active connections by execution ID
        self.execution_connections: Dict[UUID, Set[asyncio.Queue]] = defaultdict(set)

        # Active connections by squad ID
        self.squad_connections: Dict[UUID, Set[asyncio.Queue]] = defaultdict(set)

        # All active connections (for global broadcasts)
        self.all_connections: Set[asyncio.Queue] = set()

        # Connection metadata
        self.connection_metadata: Dict[asyncio.Queue, Dict[str, Any]] = {}

        # Heartbeat interval (seconds)
        self.heartbeat_interval = 15

    async def subscribe_to_execution(
        self,
        execution_id: UUID,
        user_id: UUID,
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to execution updates.

        Args:
            execution_id: Task execution ID to subscribe to
            user_id: User ID (for authorization)

        Yields:
            SSE formatted messages
        """
        # Create queue for this connection
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        # Register connection
        self.execution_connections[execution_id].add(queue)
        self.all_connections.add(queue)
        self.connection_metadata[queue] = {
            "execution_id": execution_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "type": "execution",
        }

        logger.info(f"SSE connection established for execution {execution_id} by user {user_id}")

        try:
            # Send initial connection message
            yield self._format_sse_message({
                "event": "connected",
                "data": {
                    "execution_id": str(execution_id),
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Connected to execution stream"
                }
            })

            # Start heartbeat task
            heartbeat_task = asyncio.create_task(self._send_heartbeat(queue))

            # Stream messages
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        queue.get(),
                        timeout=self.heartbeat_interval
                    )

                    if message is None:  # Sentinel value to close connection
                        break

                    yield self._format_sse_message(message)

                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield self._format_sse_message({
                        "event": "heartbeat",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    })

        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled for execution {execution_id}")
            raise

        except Exception as e:
            logger.error(f"Error in SSE stream for execution {execution_id}: {e}")
            yield self._format_sse_message({
                "event": "error",
                "data": {"error": str(e)}
            })

        finally:
            # Cleanup
            heartbeat_task.cancel()
            await self._disconnect(queue, execution_id)

    async def subscribe_to_squad(
        self,
        squad_id: UUID,
        user_id: UUID,
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to squad-level updates (all executions in squad).

        Args:
            squad_id: Squad ID to subscribe to
            user_id: User ID (for authorization)

        Yields:
            SSE formatted messages
        """
        # Create queue for this connection
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        # Register connection
        self.squad_connections[squad_id].add(queue)
        self.all_connections.add(queue)
        self.connection_metadata[queue] = {
            "squad_id": squad_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "type": "squad",
        }

        logger.info(f"SSE connection established for squad {squad_id} by user {user_id}")

        try:
            # Send initial connection message
            yield self._format_sse_message({
                "event": "connected",
                "data": {
                    "squad_id": str(squad_id),
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Connected to squad stream"
                }
            })

            # Start heartbeat task
            heartbeat_task = asyncio.create_task(self._send_heartbeat(queue))

            # Stream messages
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        queue.get(),
                        timeout=self.heartbeat_interval
                    )

                    if message is None:  # Sentinel value to close connection
                        break

                    yield self._format_sse_message(message)

                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield self._format_sse_message({
                        "event": "heartbeat",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    })

        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled for squad {squad_id}")
            raise

        except Exception as e:
            logger.error(f"Error in SSE stream for squad {squad_id}: {e}")
            yield self._format_sse_message({
                "event": "error",
                "data": {"error": str(e)}
            })

        finally:
            # Cleanup
            heartbeat_task.cancel()
            await self._disconnect_squad(queue, squad_id)

    async def broadcast_to_execution(
        self,
        execution_id: UUID,
        event: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Broadcast message to all subscribers of an execution.

        Args:
            execution_id: Execution ID
            event: Event type
            data: Event data
        """
        connections = self.execution_connections.get(execution_id, set())

        if not connections:
            logger.debug(f"No active connections for execution {execution_id}")
            return

        message = {
            "event": event,
            "data": {
                **data,
                "execution_id": str(execution_id),
                "timestamp": datetime.utcnow().isoformat(),
            }
        }

        # Send to all connections
        for queue in list(connections):
            try:
                await asyncio.wait_for(queue.put(message), timeout=1.0)
            except asyncio.TimeoutError:
                logger.warning(f"Queue full for connection, skipping message")
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")

        logger.debug(f"Broadcast {event} to {len(connections)} connections for execution {execution_id}")

    async def broadcast_to_squad(
        self,
        squad_id: UUID,
        event: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Broadcast message to all subscribers of a squad.

        Args:
            squad_id: Squad ID
            event: Event type
            data: Event data
        """
        connections = self.squad_connections.get(squad_id, set())

        if not connections:
            logger.debug(f"No active connections for squad {squad_id}")
            return

        message = {
            "event": event,
            "data": {
                **data,
                "squad_id": str(squad_id),
                "timestamp": datetime.utcnow().isoformat(),
            }
        }

        # Send to all connections
        for queue in list(connections):
            try:
                await asyncio.wait_for(queue.put(message), timeout=1.0)
            except asyncio.TimeoutError:
                logger.warning(f"Queue full for connection, skipping message")
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")

        logger.debug(f"Broadcast {event} to {len(connections)} connections for squad {squad_id}")

    async def _send_heartbeat(self, queue: asyncio.Queue) -> None:
        """Send periodic heartbeat to keep connection alive"""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                # Heartbeat is sent in the main loop via timeout
        except asyncio.CancelledError:
            pass

    async def _disconnect(self, queue: asyncio.Queue, execution_id: UUID) -> None:
        """Disconnect and cleanup connection"""
        # Remove from execution connections
        if execution_id in self.execution_connections:
            self.execution_connections[execution_id].discard(queue)
            if not self.execution_connections[execution_id]:
                del self.execution_connections[execution_id]

        # Remove from all connections
        self.all_connections.discard(queue)

        # Remove metadata
        if queue in self.connection_metadata:
            del self.connection_metadata[queue]

        logger.info(f"SSE connection disconnected for execution {execution_id}")

    async def _disconnect_squad(self, queue: asyncio.Queue, squad_id: UUID) -> None:
        """Disconnect and cleanup squad connection"""
        # Remove from squad connections
        if squad_id in self.squad_connections:
            self.squad_connections[squad_id].discard(queue)
            if not self.squad_connections[squad_id]:
                del self.squad_connections[squad_id]

        # Remove from all connections
        self.all_connections.discard(queue)

        # Remove metadata
        if queue in self.connection_metadata:
            del self.connection_metadata[queue]

        logger.info(f"SSE connection disconnected for squad {squad_id}")

    def _format_sse_message(self, message: Dict[str, Any]) -> str:
        """
        Format message as SSE.

        SSE format:
        event: <event_name>
        data: <json_data>

        """
        event = message.get("event", "message")
        data = message.get("data", {})

        # Convert data to JSON
        data_json = json.dumps(data, default=str)

        # Format as SSE
        return f"event: {event}\ndata: {data_json}\n\n"

    def get_connection_count(self, execution_id: Optional[UUID] = None) -> int:
        """Get number of active connections"""
        if execution_id:
            return len(self.execution_connections.get(execution_id, set()))
        return len(self.all_connections)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.all_connections),
            "execution_streams": len(self.execution_connections),
            "squad_streams": len(self.squad_connections),
            "connections_by_execution": {
                str(exec_id): len(conns)
                for exec_id, conns in self.execution_connections.items()
            },
            "connections_by_squad": {
                str(squad_id): len(conns)
                for squad_id, conns in self.squad_connections.items()
            },
        }


# Global SSE connection manager instance
sse_manager = SSEConnectionManager()
