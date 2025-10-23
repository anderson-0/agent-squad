"""
Agent Message Model
"""
from sqlalchemy import Column, String, ForeignKey, Index, Text, JSON, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.sql import func

from backend.models.base import Base


class AgentMessage(Base):
    """Agent-to-Agent Message model"""

    __tablename__ = "agent_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_execution_id = Column(
        UUID(as_uuid=True), ForeignKey("task_executions.id", ondelete="CASCADE"), nullable=True
    )
    sender_id = Column(UUID(as_uuid=True), ForeignKey("squad_members.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(
        UUID(as_uuid=True), ForeignKey("squad_members.id", ondelete="SET NULL"), nullable=True
    )  # null for broadcast
    content = Column(Text, nullable=False)
    message_type = Column(String, nullable=False)  # task_assignment, question, response, etc.
    message_metadata = Column(JSON, nullable=False, server_default="{}")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Conversation tracking (new columns for hierarchical routing)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="SET NULL"),
        nullable=True
    )
    is_acknowledgment = Column(Boolean, nullable=False, default=False)  # Is this a "please wait" message?
    is_follow_up = Column(Boolean, nullable=False, default=False)  # Is this an "are you still there?" message?
    is_escalation = Column(Boolean, nullable=False, default=False)  # Is this an escalation notification?
    requires_acknowledgment = Column(Boolean, nullable=False, default=False)  # Does this message need acknowledgment?
    parent_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_messages.id", ondelete="SET NULL"),
        nullable=True
    )  # For threading conversations

    # Relationships
    task_execution = relationship("TaskExecution", back_populates="messages")
    sender = relationship("SquadMember", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("SquadMember", foreign_keys=[recipient_id], back_populates="received_messages")
    conversation = relationship("Conversation", foreign_keys=[conversation_id], backref="messages")
    parent_message = relationship("AgentMessage", remote_side=[id], backref="replies")

    __table_args__ = (
        Index("ix_agent_messages_task_execution_id", "task_execution_id"),
        Index("ix_agent_messages_task_execution_id_created_at", "task_execution_id", "created_at"),
        Index("ix_agent_messages_sender_id", "sender_id"),
        Index("ix_agent_messages_recipient_id", "recipient_id"),
        Index("ix_agent_messages_conversation", "conversation_id"),
        Index("ix_agent_messages_parent", "parent_message_id"),
    )
