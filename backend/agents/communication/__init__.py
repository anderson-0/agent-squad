"""
Agent Communication System

Provides the infrastructure for agent-to-agent communication including:
- Message bus for routing messages
- A2A protocol for structured messaging
- History management for conversation storage
"""
from backend.agents.communication.message_bus import (
    MessageBus,
    get_message_bus,
    reset_message_bus,
)
from backend.agents.communication.protocol import (
    A2AProtocol,
    parse_message,
    serialize_message,
    validate_message,
    MESSAGE_TYPE_MAP,
)
from backend.agents.communication.history_manager import HistoryManager


__all__ = [
    # Message Bus
    "MessageBus",
    "get_message_bus",
    "reset_message_bus",
    # Protocol
    "A2AProtocol",
    "parse_message",
    "serialize_message",
    "validate_message",
    "MESSAGE_TYPE_MAP",
    # History
    "HistoryManager",
]
