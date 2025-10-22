"""
Conversation and ConversationEvent Models

Tracks agent-to-agent conversations with timeout, retry, and escalation.
"""
from sqlalchemy import Column, String, ForeignKey, Index, Integer, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.sql import func
from enum import Enum

from backend.models.base import Base


class ConversationState(str, Enum):
    """Possible states for a conversation"""
    INITIATED = "initiated"           # Question sent
    WAITING = "waiting"               # Acknowledged, waiting for answer
    TIMEOUT = "timeout"               # No answer after timeout
    FOLLOW_UP = "follow_up"           # Sent "are you still there?"
    ESCALATING = "escalating"         # Still no answer, escalating
    ESCALATED = "escalated"           # Question re-routed
    ANSWERED = "answered"             # Got response, resolved
    CANCELLED = "cancelled"           # Asker cancelled the question


class Conversation(Base):
    """
    Tracks a conversation between agents with timeout and escalation.

    A conversation starts when an agent asks a question and continues
    until it's answered or escalated to the maximum level.
    """

    __tablename__ = "agent_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Initial message that started this conversation
    initial_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_messages.id", ondelete="CASCADE"),
        nullable=False
    )

    # Current state of the conversation
    current_state = Column(String(50), nullable=False, default=ConversationState.INITIATED.value)

    # Participants
    asker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("squad_members.id", ondelete="CASCADE"),
        nullable=False
    )
    current_responder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("squad_members.id", ondelete="CASCADE"),
        nullable=False
    )

    # Escalation tracking
    escalation_level = Column(Integer, nullable=False, default=0)

    # Question context
    question_type = Column(String(100), nullable=True)  # 'implementation', 'architecture', etc.

    # Task context (optional)
    task_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("task_executions.id", ondelete="SET NULL"),
        nullable=True
    )

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    acknowledged_at = Column(DateTime, nullable=True)  # When responder sent "please wait"
    timeout_at = Column(DateTime, nullable=True)  # When next timeout check should occur
    resolved_at = Column(DateTime, nullable=True)  # When conversation was answered/resolved

    # Additional metadata (using conv_metadata instead of metadata which is reserved by SQLAlchemy)
    conv_metadata = Column(JSON, nullable=False, server_default="{}")

    # Relationships
    initial_message = relationship(
        "AgentMessage",
        foreign_keys=[initial_message_id],
        backref="initiated_conversation"
    )
    asker = relationship(
        "SquadMember",
        foreign_keys=[asker_id],
        backref="asked_conversations"
    )
    current_responder = relationship(
        "SquadMember",
        foreign_keys=[current_responder_id],
        backref="responding_conversations"
    )
    task_execution = relationship("TaskExecution", backref="conversations")
    events = relationship(
        "ConversationEvent",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationEvent.created_at"
    )

    __table_args__ = (
        Index("ix_conversations_state", "current_state"),
        Index("ix_conversations_asker", "asker_id"),
        Index("ix_conversations_responder", "current_responder_id"),
        Index("ix_conversations_task", "task_execution_id"),
        # Important: index for timeout monitoring queries
        Index(
            "ix_conversations_timeout",
            "timeout_at",
            "current_state",
            postgresql_where="current_state IN ('waiting', 'follow_up')"
        ),
    )

    def __repr__(self):
        return (
            f"<Conversation(id={self.id}, state={self.current_state}, "
            f"escalation_level={self.escalation_level})>"
        )


class ConversationEvent(Base):
    """
    Tracks events that occur during a conversation (acknowledgments, timeouts, escalations, etc.)

    This provides an audit trail of what happened during the conversation.
    """

    __tablename__ = "conversation_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False
    )

    # Event details
    event_type = Column(String(50), nullable=False)  # 'acknowledged', 'timeout', 'follow_up', 'escalated', 'answered'
    from_state = Column(String(50), nullable=True)  # Previous state (can be null for first event)
    to_state = Column(String(50), nullable=False)  # New state

    # Related message (if any)
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_messages.id", ondelete="SET NULL"),
        nullable=True
    )

    # Agent who triggered this event (can be null for system events like timeout)
    triggered_by_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("squad_members.id", ondelete="SET NULL"),
        nullable=True
    )

    # Additional event data (e.g., reason for escalation, timeout duration, etc.)
    event_data = Column(JSON, nullable=False, server_default="{}")

    # Timestamp
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="events")
    message = relationship("AgentMessage", backref="conversation_events")
    triggered_by_agent = relationship("SquadMember", backref="triggered_events")

    __table_args__ = (
        Index("ix_conversation_events_conversation", "conversation_id"),
        Index("ix_conversation_events_type", "event_type"),
        Index("ix_conversation_events_created", "created_at"),
    )

    def __repr__(self):
        return (
            f"<ConversationEvent(id={self.id}, type={self.event_type}, "
            f"from={self.from_state}, to={self.to_state})>"
        )
