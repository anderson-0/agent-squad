"""
NATS JetStream Configuration

Configuration settings for NATS messaging system.
"""
from pydantic import BaseModel
from typing import List, Optional


class NATSStreamConfig(BaseModel):
    """Configuration for NATS JetStream stream"""

    name: str = "agent-messages"
    subjects: List[str] = [
        "agent.message.>",  # All agent messages
        "agent.status.>",  # Agent status updates
        "agent.task.>",  # Task-related events
    ]
    retention: str = "limits"  # Keep based on limits
    max_msgs: int = 1_000_000  # 1 million messages max
    max_age: int = 7 * 24 * 60 * 60  # 7 days in seconds
    storage: str = "file"  # File-based storage
    max_msg_size: int = 1024 * 1024  # 1MB per message
    discard: str = "old"  # Discard oldest when full
    duplicate_window: int = 120  # 2 minute deduplication window


class NATSConsumerConfig(BaseModel):
    """Configuration for NATS JetStream consumer"""

    durable: str = "agent-processor"  # Durable consumer name
    deliver_policy: str = "all"  # Process all messages
    ack_policy: str = "explicit"  # Manual acknowledgment required
    ack_wait: int = 30  # 30 seconds ack timeout
    max_deliver: int = 3  # Retry 3 times on failure
    filter_subject: str = "agent.>"  # Process all agent messages
    replay_policy: str = "instant"  # Replay at max speed


class NATSConfig(BaseModel):
    """Main NATS configuration"""

    # Connection
    url: str = "nats://localhost:4222"
    name: str = "agent-squad-app"
    max_reconnect_attempts: int = 10
    reconnect_time_wait: int = 2  # seconds

    # Stream configuration
    stream: NATSStreamConfig = NATSStreamConfig()

    # Consumer configuration
    consumer: NATSConsumerConfig = NATSConsumerConfig()

    # Timeouts
    connect_timeout: int = 10  # seconds
    request_timeout: int = 5  # seconds

    # Publish settings
    publish_timeout: int = 5  # seconds
    publish_retry_attempts: int = 3

    # Pull subscribe settings
    fetch_batch_size: int = 100
    fetch_timeout: int = 2  # seconds


# Default configuration instance
default_nats_config = NATSConfig()
