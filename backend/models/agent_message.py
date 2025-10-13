"""
Agent Message Model - Re-export from message.py

This file exists for backward compatibility with imports.
The actual AgentMessage model is defined in message.py
"""
from backend.models.message import AgentMessage

__all__ = ["AgentMessage"]
