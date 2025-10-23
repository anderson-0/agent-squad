"""
Multi-Turn Conversation Models

Universal conversation support for:
- User ↔ Agent conversations
- Agent ↔ Agent conversations
- Multi-party conversations

Note: This is separate from the hierarchical routing Conversation model in conversation.py,
which handles agent escalations. This model handles ongoing multi-turn dialogues with context.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, ARRAY, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend.models.base import Base


class MultiTurnConversation(Base):
    """
    Universal conversation model supporting multiple conversation types with message history.

    Conversation Types:
    - user_agent: User talking to a single agent
    - agent_agent: Agent-to-agent conversation
    - multi_party: Multiple users and/or agents

    Initiator Types & Sender Types:
    - user: Human user
    - agent: AI agent (squad member)
    """
    __tablename__ = "conversations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Conversation classification
    conversation_type = Column(String(50), nullable=False, index=True)  # 'user_agent', 'agent_agent', 'multi_party'

    # Initiator information (who started this conversation)
    initiator_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    initiator_type = Column(String(50), nullable=False, index=True)  # 'user' or 'agent'

    # Optional foreign keys (based on conversation type)
    primary_responder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("squad_members.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    agent_conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="SET NULL"),
        nullable=True
    )

    # Conversation metadata
    title = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="active", index=True)  # 'active', 'archived', 'closed'
    total_messages = Column(Integer, nullable=False, default=0)
    total_tokens_used = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    last_message_at = Column(DateTime, nullable=True, index=True)
    archived_at = Column(DateTime, nullable=True)

    # Additional metadata (JSONB for flexibility) - using conv_metadata because metadata is reserved by SQLAlchemy
    conv_metadata = Column(JSONB, nullable=True, default=dict)

    # Relationships
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at"
    )
    participants = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    # Relationships to User and SquadMember
    user = relationship("User", back_populates="multi_turn_conversations", foreign_keys=[user_id])
    primary_responder = relationship("SquadMember", back_populates="multi_turn_conversations", foreign_keys=[primary_responder_id])

    # Link to hierarchical routing conversation (if applicable)
    agent_conversation = relationship("Conversation", foreign_keys=[agent_conversation_id])

    def __repr__(self):
        return f"<MultiTurnConversation(id={self.id}, type={self.conversation_type}, status={self.status}, messages={self.total_messages})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "conversation_type": self.conversation_type,
            "initiator_id": str(self.initiator_id),
            "initiator_type": self.initiator_type,
            "primary_responder_id": str(self.primary_responder_id) if self.primary_responder_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "agent_conversation_id": str(self.agent_conversation_id) if self.agent_conversation_id else None,
            "title": self.title,
            "status": self.status,
            "total_messages": self.total_messages,
            "total_tokens_used": self.total_tokens_used,
            "summary": self.summary,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "metadata": self.conv_metadata
        }

    @property
    def is_active(self) -> bool:
        """Check if conversation is active"""
        return self.status == "active"

    @property
    def is_user_agent(self) -> bool:
        """Check if this is a user-agent conversation"""
        return self.conversation_type == "user_agent"

    @property
    def is_agent_agent(self) -> bool:
        """Check if this is an agent-agent conversation"""
        return self.conversation_type == "agent_agent"

    @property
    def is_multi_party(self) -> bool:
        """Check if this is a multi-party conversation"""
        return self.conversation_type == "multi_party"

    def get_context_window(self, max_messages: Optional[int] = None) -> List:
        """
        Get conversation context window for LLM.

        Args:
            max_messages: Maximum number of recent messages to include

        Returns:
            List of message dicts formatted for LLM context
        """
        messages = self.messages
        if max_messages:
            messages = messages[-max_messages:]

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "sender_id": str(msg.sender_id),
                "sender_type": msg.sender_type,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]


class ConversationMessage(Base):
    """
    Individual messages within a multi-turn conversation.

    Tracks all messages from both users and agents, including token usage and metadata.
    """
    __tablename__ = "conversation_messages"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to conversation
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Sender information
    sender_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sender_type = Column(String(50), nullable=False, index=True)  # 'user' or 'agent'

    # Message content
    role = Column(String(50), nullable=False, index=True)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Token tracking (for agent messages)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # LLM metadata (for agent messages)
    model_used = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=True)
    llm_provider = Column(String(50), nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Performance tracking
    response_time_ms = Column(Integer, nullable=True)

    # Optional link to hierarchical routing message
    agent_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_messages.id", ondelete="SET NULL"),
        nullable=True
    )

    # Additional metadata - using conv_metadata because metadata is reserved by SQLAlchemy
    conv_metadata = Column(JSONB, nullable=True, default=dict)

    # Relationships
    conversation = relationship("MultiTurnConversation", back_populates="messages")
    agent_message = relationship("AgentMessage", foreign_keys=[agent_message_id])

    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, sender_type={self.sender_type}, role={self.role})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "sender_id": str(self.sender_id),
            "sender_type": self.sender_type,
            "role": self.role,
            "content": self.content,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "model_used": self.model_used,
            "temperature": self.temperature,
            "llm_provider": self.llm_provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "response_time_ms": self.response_time_ms,
            "agent_message_id": str(self.agent_message_id) if self.agent_message_id else None,
            "metadata": self.conv_metadata
        }


class ConversationParticipant(Base):
    """
    Tracks participants in a multi-turn conversation.

    Supports multi-party conversations where multiple users and/or agents participate.
    """
    __tablename__ = "conversation_participants"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to conversation
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Participant information
    participant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    participant_type = Column(String(50), nullable=False, index=True)  # 'user' or 'agent'

    # Role in conversation
    role = Column(String(50), nullable=False)  # 'initiator', 'responder', 'observer', 'moderator'

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Timestamps
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

    # Additional metadata - using conv_metadata because metadata is reserved by SQLAlchemy
    conv_metadata = Column(JSONB, nullable=True, default=dict)

    # Relationships
    conversation = relationship("MultiTurnConversation", back_populates="participants")

    def __repr__(self):
        return f"<ConversationParticipant(id={self.id}, type={self.participant_type}, role={self.role}, active={self.is_active})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "participant_id": str(self.participant_id),
            "participant_type": self.participant_type,
            "role": self.role,
            "is_active": self.is_active,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
            "metadata": self.conv_metadata
        }
