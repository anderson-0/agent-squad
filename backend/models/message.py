"""
Agent Message Model
"""
from sqlalchemy import Column, String, ForeignKey, Index, Text, JSON, DateTime
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
        UUID(as_uuid=True), ForeignKey("task_executions.id", ondelete="CASCADE"), nullable=False
    )
    sender_id = Column(UUID(as_uuid=True), ForeignKey("squad_members.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(
        UUID(as_uuid=True), ForeignKey("squad_members.id", ondelete="SET NULL"), nullable=True
    )  # null for broadcast
    content = Column(Text, nullable=False)
    message_type = Column(String, nullable=False)  # task_assignment, question, response, etc.
    metadata = Column(JSON, nullable=False, server_default="{}")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    task_execution = relationship("TaskExecution", back_populates="messages")
    sender = relationship("SquadMember", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("SquadMember", foreign_keys=[recipient_id], back_populates="received_messages")

    __table_args__ = (
        Index("ix_agent_messages_task_execution_id", "task_execution_id"),
        Index("ix_agent_messages_task_execution_id_created_at", "task_execution_id", "created_at"),
        Index("ix_agent_messages_sender_id", "sender_id"),
        Index("ix_agent_messages_recipient_id", "recipient_id"),
    )
