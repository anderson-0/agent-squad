"""
NATS Consumer Worker

Background worker that consumes messages from NATS JetStream.
Multiple instances can run for horizontal scaling.

Features:
- Pulls messages from JetStream
- Processes messages (extensible)
- Acknowledges successful processing
- Retries on failure
- Graceful shutdown
"""
import asyncio
import json
import logging
import signal
from typing import Optional, Dict, Any
from datetime import datetime

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig
from nats.errors import TimeoutError as NATSTimeoutError

from backend.agents.communication.nats_config import NATSConfig, default_nats_config

logger = logging.getLogger(__name__)


class NATSConsumerWorker:
    """
    Background worker for consuming NATS messages.

    Multiple workers can run concurrently for load distribution.
    Each worker processes messages independently.
    """

    def __init__(
        self,
        config: Optional[NATSConfig] = None,
        worker_id: str = "worker-1"
    ):
        """
        Initialize NATS consumer worker.

        Args:
            config: NATS configuration
            worker_id: Unique identifier for this worker
        """
        self.config = config or default_nats_config
        self.worker_id = worker_id
        self._nc: Optional[NATS] = None
        self._js: Optional[JetStreamContext] = None
        self._running = False
        self._shutdown_event = asyncio.Event()

    async def connect(self) -> None:
        """Connect to NATS server"""
        logger.info(f"[{self.worker_id}] Connecting to NATS at {self.config.url}")

        self._nc = NATS()
        await self._nc.connect(
            servers=[self.config.url],
            name=f"{self.config.name}-{self.worker_id}",
            max_reconnect_attempts=self.config.max_reconnect_attempts,
            reconnect_time_wait=self.config.reconnect_time_wait,
        )

        self._js = self._nc.jetstream()
        logger.info(f"[{self.worker_id}] Connected to NATS")

    async def disconnect(self) -> None:
        """Disconnect from NATS"""
        if self._nc:
            await self._nc.close()
            logger.info(f"[{self.worker_id}] Disconnected from NATS")

    async def start(self) -> None:
        """
        Start consuming messages from NATS.

        This is the main worker loop that:
        1. Pulls messages from JetStream
        2. Processes each message
        3. Acknowledges or retries
        """
        if not self._js:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        self._running = True
        logger.info(f"[{self.worker_id}] Starting consumer worker")

        # Create pull subscriber
        try:
            psub = await self._js.pull_subscribe(
                subject=self.config.consumer.filter_subject,
                durable=f"{self.config.consumer.durable}-{self.worker_id}",
            )
            logger.info(
                f"[{self.worker_id}] Subscribed to '{self.config.consumer.filter_subject}'"
            )
        except Exception as e:
            logger.error(f"[{self.worker_id}] Failed to subscribe: {e}")
            raise

        # Main processing loop
        while self._running and not self._shutdown_event.is_set():
            try:
                # Fetch batch of messages
                msgs = await psub.fetch(
                    batch=self.config.fetch_batch_size,
                    timeout=self.config.fetch_timeout
                )

                if not msgs:
                    # No messages available, wait a bit
                    await asyncio.sleep(0.5)
                    continue

                logger.debug(f"[{self.worker_id}] Fetched {len(msgs)} messages")

                # Process each message
                for msg in msgs:
                    if not self._running:
                        break

                    try:
                        await self._process_message(msg)
                        # Acknowledge successful processing
                        await msg.ack()
                    except Exception as e:
                        logger.error(
                            f"[{self.worker_id}] Error processing message: {e}",
                            exc_info=True
                        )
                        # Don't ack - message will be redelivered
                        # NATS will retry based on max_deliver setting
                        await msg.nak()  # Negative acknowledgment

            except asyncio.TimeoutError:
                # No messages available, continue loop
                continue
            except NATSTimeoutError:
                # NATS timeout, continue loop
                continue
            except Exception as e:
                logger.error(f"[{self.worker_id}] Error in consumer loop: {e}", exc_info=True)
                await asyncio.sleep(1)  # Back off on error

        logger.info(f"[{self.worker_id}] Consumer worker stopped")

    async def _process_message(self, msg) -> None:
        """
        Process a single message.

        This is where custom message processing logic goes.
        Currently logs the message. Can be extended to:
        - Trigger agent actions
        - Update databases
        - Call webhooks
        - Send notifications

        Args:
            msg: NATS message
        """
        try:
            # Parse message payload
            payload = json.loads(msg.data.decode('utf-8'))

            message_id = payload.get('id')
            message_type = payload.get('message_type')
            sender_id = payload.get('sender_id')
            recipient_id = payload.get('recipient_id')
            content = payload.get('content')

            logger.info(
                f"[{self.worker_id}] Processing message {message_id}: "
                f"type={message_type}, from={sender_id}, to={recipient_id}"
            )

            # TODO: Add custom processing logic here
            # Examples:
            # - Trigger agent workflows
            # - Update task status
            # - Send notifications
            # - Call external APIs

            # For now, just log
            logger.debug(f"[{self.worker_id}] Message content: {content[:100]}...")

        except json.JSONDecodeError as e:
            logger.error(f"[{self.worker_id}] Invalid JSON in message: {e}")
            raise
        except Exception as e:
            logger.error(f"[{self.worker_id}] Error processing message: {e}")
            raise

    async def stop(self) -> None:
        """
        Stop the consumer worker gracefully.

        Allows current messages to finish processing.
        """
        logger.info(f"[{self.worker_id}] Stopping consumer worker")
        self._running = False
        self._shutdown_event.set()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get worker statistics.

        Returns:
            Dict with worker stats
        """
        return {
            "worker_id": self.worker_id,
            "running": self._running,
            "connected": self._nc is not None and self._nc.is_connected,
        }


class NATSConsumerManager:
    """
    Manages multiple NATS consumer workers.

    Allows scaling message processing by running multiple workers.
    """

    def __init__(self, config: Optional[NATSConfig] = None, num_workers: int = 1):
        """
        Initialize consumer manager.

        Args:
            config: NATS configuration
            num_workers: Number of worker instances to run
        """
        self.config = config or default_nats_config
        self.num_workers = num_workers
        self.workers: list[NATSConsumerWorker] = []
        self.worker_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """
        Start all consumer workers.
        """
        logger.info(f"Starting {self.num_workers} NATS consumer workers")

        for i in range(self.num_workers):
            worker_id = f"worker-{i+1}"
            worker = NATSConsumerWorker(config=self.config, worker_id=worker_id)

            # Connect worker
            await worker.connect()

            # Start worker in background task
            task = asyncio.create_task(worker.start())
            self.workers.append(worker)
            self.worker_tasks.append(task)

        logger.info(f"All {self.num_workers} workers started")

    async def stop(self) -> None:
        """
        Stop all consumer workers gracefully.
        """
        logger.info("Stopping all NATS consumer workers")

        # Signal all workers to stop
        for worker in self.workers:
            await worker.stop()

        # Wait for all tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        # Disconnect all workers
        for worker in self.workers:
            await worker.disconnect()

        self.workers.clear()
        self.worker_tasks.clear()

        logger.info("All workers stopped")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all workers.

        Returns:
            Dict with manager and worker stats
        """
        return {
            "num_workers": len(self.workers),
            "workers": [worker.get_stats() for worker in self.workers]
        }


# Singleton manager instance
_consumer_manager: Optional[NATSConsumerManager] = None


async def start_nats_consumers(
    config: Optional[NATSConfig] = None,
    num_workers: int = 1
) -> NATSConsumerManager:
    """
    Start NATS consumer workers.

    Args:
        config: NATS configuration
        num_workers: Number of workers to start

    Returns:
        Consumer manager instance
    """
    global _consumer_manager

    if _consumer_manager is not None:
        logger.warning("NATS consumers already running")
        return _consumer_manager

    _consumer_manager = NATSConsumerManager(config=config, num_workers=num_workers)
    await _consumer_manager.start()

    return _consumer_manager


async def stop_nats_consumers() -> None:
    """
    Stop all NATS consumer workers.
    """
    global _consumer_manager

    if _consumer_manager is None:
        logger.warning("No NATS consumers running")
        return

    await _consumer_manager.stop()
    _consumer_manager = None


def get_consumer_manager() -> Optional[NATSConsumerManager]:
    """
    Get the consumer manager instance.

    Returns:
        Consumer manager or None if not started
    """
    return _consumer_manager


# CLI entry point for running workers standalone
async def main():
    """
    Main entry point for running workers standalone.

    Usage:
        python -m backend.workers.nats_consumer
    """
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handle shutdown signals
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start consumers
    num_workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    logger.info(f"Starting {num_workers} consumer workers")

    manager = await start_nats_consumers(num_workers=num_workers)

    # Wait for shutdown signal
    logger.info("Workers running. Press Ctrl+C to stop.")
    await shutdown_event.wait()

    # Stop consumers
    await stop_nats_consumers()
    logger.info("All workers stopped. Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
