# Phase 4: Multi-Turn Conversations - Universal Plan (v2)

**Status**: Planning Phase (Updated)
**Created**: October 23, 2025
**Updated**: October 23, 2025
**Purpose**: Enable conversational, context-aware interactions for ALL participants (users AND agents)

---

## 🎯 Major Update: Universal Conversations

**Key Change:** This system now supports:
- ✅ **User ↔ Agent** conversations (users asking agents for help)
- ✅ **Agent ↔ Agent** conversations (agents asking each other for help)
- ✅ **Multi-party** conversations (future: multiple agents collaborating)

This makes the system **dramatically more powerful** and integrates with the Hierarchical Routing System.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Use Cases](#use-cases)
3. [Database Schema Design](#database-schema-design)
4. [Backend Architecture](#backend-architecture)
5. [API Design](#api-design)
6. [Integration Points](#integration-points)
7. [Implementation Phases](#implementation-phases)
8. [Testing Strategy](#testing-strategy)

---

## Executive Summary

### What We're Building

A **universal conversation system** that maintains context across multiple message exchanges between ANY participants:

```
User ↔ Agent:
  User: "How do I cache?"
  Agent: "Use Redis..."
  User: "How do I set it up?"
  Agent: "To set up Redis (from our discussion)..." ✅

Agent ↔ Agent:
  Backend Dev: "How should I structure the API?"
  Tech Lead: "Let me think about this..."
  Backend Dev: "Any thoughts yet?"
  Tech Lead: "For the API structure we discussed..." ✅
```

### Why This Matters

**For Users:**
- Natural conversations with AI agents
- Don't need to repeat context
- Build knowledge progressively

**For Agents:**
- Remember context when asking colleagues for help
- More intelligent collaboration
- Reduces redundant explanations between agents

**For the System:**
- Integrates with Hierarchical Routing (agents escalate WITH context)
- Better decision making (agents have full conversation history)
- More realistic team dynamics

---

## Use Cases

### Use Case 1: User Learning from Agent

**Scenario:** Developer learning about caching

```
User: "What is Redis?"
Agent: "Redis is an in-memory data store..."

User: "How is it different from PostgreSQL?"
Agent: "While Redis (which I explained) is in-memory..."

User: "When should I use each?"
Agent: "Based on our discussion - Redis for caching, PostgreSQL for persistence..."
```

**Value:** Progressive learning with context

### Use Case 2: Agent Asking Agent for Help (NEW!)

**Scenario:** Backend developer needs architecture advice

```
Backend Dev → Tech Lead: "How should I structure the authentication API?"
Tech Lead → Backend Dev: "Let me think about this, please wait..."

[5 minutes later]

Backend Dev → Tech Lead: "Any update on the auth structure?"
Tech Lead → Backend Dev: "For the authentication API we discussed, I recommend JWT..."

Backend Dev → Tech Lead: "What about refresh tokens?"
Tech Lead → Backend Dev: "In your JWT-based auth, add refresh tokens like this..."
```

**Value:**
- Tech Lead remembers the auth discussion
- Backend Dev doesn't repeat the question
- Conversation flows naturally

### Use Case 3: Hierarchical Escalation with Context (NEW!)

**Scenario:** Question escalates through the hierarchy WITH conversation history

```
Backend Dev → Tech Lead: "How should we design microservices for 100k req/sec?"
Tech Lead → Backend Dev: "Let me think..."

[Timeout - escalates to Solution Architect]

System → Solution Architect: "Backend Dev asked Tech Lead about microservices design.
                               Here's the conversation history: [shows full context]"

Solution Architect → Backend Dev: "I see you're designing for 100k req/sec.
                                    Based on your requirements, use event-driven..."

Backend Dev → Solution Architect: "What about data consistency?"
Solution Architect → Backend Dev: "For your event-driven microservices, use saga pattern..."
```

**Value:**
- Solution Architect sees full context from Tech Lead conversation
- Backend Dev doesn't repeat requirements
- Escalation maintains conversational flow

### Use Case 4: Multi-Turn Debugging Session (NEW!)

**Scenario:** Agent helps another agent debug an issue

```
Frontend Dev → Backend Dev: "API is returning 500 errors"
Backend Dev → Frontend Dev: "What endpoint are you calling?"

Frontend Dev → Backend Dev: "/api/users"
Backend Dev → Frontend Dev: "Let me check the logs... Found it. The database connection is timing out."

Frontend Dev → Backend Dev: "How do I fix it?"
Backend Dev → Frontend Dev: "For the timeout issue we found, increase the connection pool size..."
```

**Value:**
- Backend Dev remembers the endpoint and diagnosis
- Frontend Dev gets context-aware solutions
- Debugging flows naturally

### Use Case 5: Collaborative Problem Solving (NEW!)

**Scenario:** Multiple agents working together on a task

```
Project Manager → Squad: "We need to implement real-time notifications"

Backend Dev → PM: "I can build a WebSocket server"
Frontend Dev → PM: "I'll create the UI components"
DevOps → PM: "I'll set up Redis for pub/sub"

PM → Backend Dev: "How's the WebSocket server coming?"
Backend Dev → PM: "For the notifications system we discussed, it's ready for testing"

PM → Frontend Dev: "Can you integrate with the WebSocket server?"
Frontend Dev → PM: "Yes, based on Backend Dev's implementation..."
```

**Value:**
- All agents remember the notifications project
- Context shared across the team
- Coordinated work

---

## Database Schema Design

### Design Philosophy

**Key Decisions:**
1. **Universal Table**: One `conversations` table for all conversation types
2. **Flexible Participants**: Support any combination of users and agents
3. **Type Discrimination**: `conversation_type` field distinguishes use cases
4. **Backward Compatible**: Works with existing agent-to-agent messaging

### 1. Updated Table: `conversations`

**Purpose:** Track ALL conversation sessions (user-agent AND agent-agent)

```sql
CREATE TABLE conversations (
    -- Identity
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Conversation type
    conversation_type VARCHAR(50) NOT NULL,  -- 'user_agent', 'agent_agent', 'multi_party'

    -- Initiator (who started the conversation)
    initiator_id UUID NOT NULL,  -- Could be user_id or squad_member_id
    initiator_type VARCHAR(50) NOT NULL,  -- 'user' or 'agent'

    -- Primary responder (main agent responding)
    primary_responder_id UUID REFERENCES squad_members(id),

    -- Optional: Link to user (for user-agent conversations)
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Optional: Link to agent-agent conversation tracking
    agent_conversation_id UUID REFERENCES agent_conversations(id),  -- If part of hierarchical routing

    -- Conversation metadata
    title VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'active',  -- active, archived, deleted, escalated

    -- Context tracking
    total_messages INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,

    -- Summary and organization
    summary TEXT,
    tags TEXT[],

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_primary_responder FOREIGN KEY (primary_responder_id)
        REFERENCES squad_members(id) ON DELETE CASCADE,
    CONSTRAINT fk_agent_conversation FOREIGN KEY (agent_conversation_id)
        REFERENCES agent_conversations(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_conversations_initiator ON conversations(initiator_id, initiator_type);
CREATE INDEX idx_conversations_type ON conversations(conversation_type);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_user_id ON conversations(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_conversations_primary_responder ON conversations(primary_responder_id);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
CREATE INDEX idx_conversations_agent_conversation ON conversations(agent_conversation_id)
    WHERE agent_conversation_id IS NOT NULL;
```

### 2. Updated Table: `conversation_messages`

**Purpose:** Store messages from ANY participant (users or agents)

```sql
CREATE TABLE conversation_messages (
    -- Identity
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Sender information (flexible)
    sender_id UUID NOT NULL,  -- Could be user_id or squad_member_id
    sender_type VARCHAR(50) NOT NULL,  -- 'user' or 'agent'

    -- Message details
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,

    -- Token tracking
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,

    -- LLM metadata (for assistant messages)
    model_used VARCHAR(100),
    temperature FLOAT,
    llm_provider VARCHAR(50),

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time_ms INTEGER,

    -- Link to agent message (if this is part of agent-agent communication)
    agent_message_id UUID REFERENCES agent_messages(id),

    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT fk_conversation FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_conversation_messages_conversation ON conversation_messages(conversation_id);
CREATE INDEX idx_conversation_messages_sender ON conversation_messages(sender_id, sender_type);
CREATE INDEX idx_conversation_messages_created ON conversation_messages(created_at);
CREATE INDEX idx_conversation_messages_conversation_created
    ON conversation_messages(conversation_id, created_at);
CREATE INDEX idx_conversation_messages_agent_message ON conversation_messages(agent_message_id)
    WHERE agent_message_id IS NOT NULL;
```

### 3. New Table: `conversation_participants`

**Purpose:** Track all participants in a conversation (for multi-party support)

```sql
CREATE TABLE conversation_participants (
    -- Identity
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Participant
    participant_id UUID NOT NULL,  -- Could be user_id or squad_member_id
    participant_type VARCHAR(50) NOT NULL,  -- 'user' or 'agent'

    -- Role in conversation
    role VARCHAR(50) NOT NULL,  -- 'initiator', 'primary_responder', 'observer', 'collaborator'

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    left_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT fk_conversation FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE,

    -- Ensure unique participant per conversation
    CONSTRAINT unique_participant_per_conversation
        UNIQUE (conversation_id, participant_id, participant_type)
);

-- Indexes
CREATE INDEX idx_conversation_participants_conversation ON conversation_participants(conversation_id);
CREATE INDEX idx_conversation_participants_participant
    ON conversation_participants(participant_id, participant_type);
CREATE INDEX idx_conversation_participants_active
    ON conversation_participants(conversation_id) WHERE is_active = TRUE;
```

### 4. Migration Script

```python
# backend/alembic/versions/004_add_universal_conversations.py

"""add universal multi-turn conversations

Revision ID: 004
Revises: 003
Create Date: 2025-10-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create conversations table (universal for user-agent and agent-agent)
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_type', sa.String(50), nullable=False),
        sa.Column('initiator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('initiator_type', sa.String(50), nullable=False),
        sa.Column('primary_responder_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('total_messages', sa.Integer(), server_default='0'),
        sa.Column('total_tokens_used', sa.Integer(), server_default='0'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['primary_responder_id'], ['squad_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_conversation_id'], ['agent_conversations.id'], ondelete='SET NULL')
    )

    # Create indexes for conversations
    op.create_index('idx_conversations_initiator', 'conversations', ['initiator_id', 'initiator_type'])
    op.create_index('idx_conversations_type', 'conversations', ['conversation_type'])
    op.create_index('idx_conversations_status', 'conversations', ['status'])
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'],
                   postgresql_where=sa.text('user_id IS NOT NULL'))
    op.create_index('idx_conversations_primary_responder', 'conversations', ['primary_responder_id'])
    op.create_index('idx_conversations_last_message', 'conversations', ['last_message_at'],
                   postgresql_ops={'last_message_at': 'DESC'})
    op.create_index('idx_conversations_agent_conversation', 'conversations', ['agent_conversation_id'],
                   postgresql_where=sa.text('agent_conversation_id IS NOT NULL'))

    # Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_type', sa.String(50), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('llm_provider', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('agent_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_message_id'], ['agent_messages.id'], ondelete='SET NULL')
    )

    # Create indexes for conversation_messages
    op.create_index('idx_conversation_messages_conversation', 'conversation_messages', ['conversation_id'])
    op.create_index('idx_conversation_messages_sender', 'conversation_messages', ['sender_id', 'sender_type'])
    op.create_index('idx_conversation_messages_created', 'conversation_messages', ['created_at'])
    op.create_index('idx_conversation_messages_conversation_created', 'conversation_messages',
                   ['conversation_id', 'created_at'])
    op.create_index('idx_conversation_messages_agent_message', 'conversation_messages', ['agent_message_id'],
                   postgresql_where=sa.text('agent_message_id IS NOT NULL'))

    # Create conversation_participants table
    op.create_table(
        'conversation_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_type', sa.String(50), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('conversation_id', 'participant_id', 'participant_type',
                          name='unique_participant_per_conversation')
    )

    # Create indexes for conversation_participants
    op.create_index('idx_conversation_participants_conversation', 'conversation_participants', ['conversation_id'])
    op.create_index('idx_conversation_participants_participant', 'conversation_participants',
                   ['participant_id', 'participant_type'])
    op.create_index('idx_conversation_participants_active', 'conversation_participants', ['conversation_id'],
                   postgresql_where=sa.text('is_active = true'))

    # Update squad_members table
    op.add_column('squad_members',
                 sa.Column('max_conversation_tokens', sa.Integer(), server_default='8000'))
    op.add_column('squad_members',
                 sa.Column('conversation_memory_enabled', sa.Boolean(), server_default='true'))
    op.add_column('squad_members',
                 sa.Column('auto_generate_summary', sa.Boolean(), server_default='true'))


def downgrade():
    # Remove columns from squad_members
    op.drop_column('squad_members', 'auto_generate_summary')
    op.drop_column('squad_members', 'conversation_memory_enabled')
    op.drop_column('squad_members', 'max_conversation_tokens')

    # Drop conversation_participants table
    op.drop_index('idx_conversation_participants_active', 'conversation_participants')
    op.drop_index('idx_conversation_participants_participant', 'conversation_participants')
    op.drop_index('idx_conversation_participants_conversation', 'conversation_participants')
    op.drop_table('conversation_participants')

    # Drop conversation_messages table
    op.drop_index('idx_conversation_messages_agent_message', 'conversation_messages')
    op.drop_index('idx_conversation_messages_conversation_created', 'conversation_messages')
    op.drop_index('idx_conversation_messages_created', 'conversation_messages')
    op.drop_index('idx_conversation_messages_sender', 'conversation_messages')
    op.drop_index('idx_conversation_messages_conversation', 'conversation_messages')
    op.drop_table('conversation_messages')

    # Drop conversations table
    op.drop_index('idx_conversations_agent_conversation', 'conversations')
    op.drop_index('idx_conversations_last_message', 'conversations')
    op.drop_index('idx_conversations_primary_responder', 'conversations')
    op.drop_index('idx_conversations_user_id', 'conversations')
    op.drop_index('idx_conversations_status', 'conversations')
    op.drop_index('idx_conversations_type', 'conversations')
    op.drop_index('idx_conversations_initiator', 'conversations')
    op.drop_table('conversations')
```

---

## Backend Architecture

### 1. SQLAlchemy Models

**File:** `backend/models/conversation.py`

```python
"""
Universal Conversation Models

Supports both user-agent and agent-agent conversations.
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from enum import Enum

from backend.models.base import Base


class ConversationType(str, Enum):
    """Types of conversations supported"""
    USER_AGENT = "user_agent"
    AGENT_AGENT = "agent_agent"
    MULTI_PARTY = "multi_party"


class ParticipantType(str, Enum):
    """Types of conversation participants"""
    USER = "user"
    AGENT = "agent"


class Conversation(Base):
    """
    Universal conversation model.

    Supports:
    - User ↔ Agent conversations
    - Agent ↔ Agent conversations
    - Multi-party conversations
    """

    __tablename__ = "conversations"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Conversation type
    conversation_type = Column(String(50), nullable=False)

    # Initiator (who started the conversation)
    initiator_id = Column(UUID(as_uuid=True), nullable=False)
    initiator_type = Column(String(50), nullable=False)  # 'user' or 'agent'

    # Primary responder
    primary_responder_id = Column(UUID(as_uuid=True), ForeignKey("squad_members.id", ondelete="CASCADE"), nullable=True)

    # Optional: Link to user (for user-agent conversations)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    # Optional: Link to hierarchical routing conversation
    agent_conversation_id = Column(UUID(as_uuid=True), ForeignKey("agent_conversations.id", ondelete="SET NULL"), nullable=True)

    # Conversation metadata
    title = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="active")

    # Context tracking
    total_messages = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)

    # Summary and organization
    summary = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    metadata = Column(JSONB, default={})

    # Relationships
    user = relationship("User", back_populates="conversations", foreign_keys=[user_id])
    primary_responder = relationship("SquadMember", back_populates="conversations_as_responder")
    agent_conversation = relationship("AgentConversation", back_populates="multi_turn_conversation")
    messages = relationship("ConversationMessage", back_populates="conversation",
                          cascade="all, delete-orphan", order_by="ConversationMessage.created_at")
    participants = relationship("ConversationParticipant", back_populates="conversation",
                              cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_conversations_initiator", "initiator_id", "initiator_type"),
        Index("ix_conversations_type", "conversation_type"),
        Index("ix_conversations_status", "status"),
        Index("ix_conversations_user_id", "user_id", postgresql_where=Column('user_id').isnot(None)),
        Index("ix_conversations_primary_responder", "primary_responder_id"),
        Index("ix_conversations_last_message", "last_message_at", postgresql_ops={"last_message_at": "DESC"}),
        Index("ix_conversations_agent_conversation", "agent_conversation_id",
              postgresql_where=Column('agent_conversation_id').isnot(None)),
    )

    def is_user_conversation(self) -> bool:
        """Check if this is a user-agent conversation"""
        return self.conversation_type == ConversationType.USER_AGENT

    def is_agent_conversation(self) -> bool:
        """Check if this is an agent-agent conversation"""
        return self.conversation_type == ConversationType.AGENT_AGENT

    def __repr__(self):
        return f"<Conversation(id={self.id}, type={self.conversation_type}, status={self.status})>"


class ConversationMessage(Base):
    """
    Represents a single message within a conversation.

    Sender can be a user or an agent.
    """

    __tablename__ = "conversation_messages"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    # Sender (flexible: user or agent)
    sender_id = Column(UUID(as_uuid=True), nullable=False)
    sender_type = Column(String(50), nullable=False)  # 'user' or 'agent'

    # Message details
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Token tracking
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # LLM metadata (for assistant messages)
    model_used = Column(String(100), nullable=True)
    temperature = Column(Float, nullable=True)
    llm_provider = Column(String(50), nullable=True)

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_time_ms = Column(Integer, nullable=True)

    # Link to agent message (if part of agent-agent communication)
    agent_message_id = Column(UUID(as_uuid=True), ForeignKey("agent_messages.id", ondelete="SET NULL"), nullable=True)

    # Additional metadata
    metadata = Column(JSONB, default={})

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    agent_message = relationship("AgentMessage", back_populates="conversation_messages")

    __table_args__ = (
        Index("ix_conversation_messages_conversation", "conversation_id"),
        Index("ix_conversation_messages_sender", "sender_id", "sender_type"),
        Index("ix_conversation_messages_created", "created_at"),
        Index("ix_conversation_messages_conversation_created", "conversation_id", "created_at"),
        Index("ix_conversation_messages_agent_message", "agent_message_id",
              postgresql_where=Column('agent_message_id').isnot(None)),
    )

    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, sender_type={self.sender_type}, role={self.role})>"


class ConversationParticipant(Base):
    """
    Tracks participants in a conversation.

    Supports multi-party conversations.
    """

    __tablename__ = "conversation_participants"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    # Participant
    participant_id = Column(UUID(as_uuid=True), nullable=False)
    participant_type = Column(String(50), nullable=False)  # 'user' or 'agent'

    # Role in conversation
    role = Column(String(50), nullable=False)  # 'initiator', 'primary_responder', 'observer', 'collaborator'

    # Status
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    left_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    metadata = Column(JSONB, default={})

    # Relationships
    conversation = relationship("Conversation", back_populates="participants")

    __table_args__ = (
        UniqueConstraint('conversation_id', 'participant_id', 'participant_type',
                        name='unique_participant_per_conversation'),
        Index("ix_conversation_participants_conversation", "conversation_id"),
        Index("ix_conversation_participants_participant", "participant_id", "participant_type"),
        Index("ix_conversation_participants_active", "conversation_id",
              postgresql_where=Column('is_active').is_(True)),
    )

    def __repr__(self):
        return f"<ConversationParticipant(participant_type={self.participant_type}, role={self.role})>"
```

### 2. Updated Service Layer

**File:** `backend/services/conversation_service.py`

```python
"""
Universal Conversation Service

Handles both user-agent and agent-agent conversations.
"""
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from backend.models.conversation import (
    Conversation,
    ConversationMessage,
    ConversationParticipant,
    ConversationType,
    ParticipantType
)
from backend.models.squad import SquadMember
from backend.models.user import User
from backend.agents.factory import AgentFactory
from backend.agents.base_agent import ConversationMessage as AgentConversationMessage
from backend.core.logging import logger


class ConversationService:
    """
    Universal service for managing conversations.

    Supports:
    - User ↔ Agent conversations
    - Agent ↔ Agent conversations
    - Multi-party conversations
    """

    @staticmethod
    async def create_user_agent_conversation(
        db: AsyncSession,
        user_id: UUID,
        squad_member_id: UUID,
        title: Optional[str] = None,
        initial_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Create a user-agent conversation.

        Args:
            db: Database session
            user_id: User starting the conversation
            squad_member_id: Agent to converse with
            title: Optional conversation title
            initial_message: Optional first message
            metadata: Optional metadata

        Returns:
            Conversation instance
        """
        conversation = Conversation(
            conversation_type=ConversationType.USER_AGENT,
            initiator_id=user_id,
            initiator_type=ParticipantType.USER,
            primary_responder_id=squad_member_id,
            user_id=user_id,
            title=title or "New Conversation",
            status="active",
            metadata=metadata or {}
        )

        db.add(conversation)
        await db.flush()

        # Add participants
        user_participant = ConversationParticipant(
            conversation_id=conversation.id,
            participant_id=user_id,
            participant_type=ParticipantType.USER,
            role="initiator"
        )
        agent_participant = ConversationParticipant(
            conversation_id=conversation.id,
            participant_id=squad_member_id,
            participant_type=ParticipantType.AGENT,
            role="primary_responder"
        )

        db.add_all([user_participant, agent_participant])

        # Send initial message if provided
        if initial_message:
            await ConversationService._add_message(
                db=db,
                conversation_id=conversation.id,
                sender_id=user_id,
                sender_type=ParticipantType.USER,
                role="user",
                content=initial_message
            )

        await db.commit()
        await db.refresh(conversation)

        logger.info(f"Created user-agent conversation {conversation.id}")
        return conversation


    @staticmethod
    async def create_agent_agent_conversation(
        db: AsyncSession,
        initiator_agent_id: UUID,
        responder_agent_id: UUID,
        title: Optional[str] = None,
        initial_question: Optional[str] = None,
        agent_conversation_id: Optional[UUID] = None,  # Link to hierarchical routing
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Create an agent-agent conversation.

        This is used when one agent asks another agent for help.

        Args:
            db: Database session
            initiator_agent_id: Agent asking the question
            responder_agent_id: Agent being asked
            title: Optional conversation title
            initial_question: Optional first question
            agent_conversation_id: Optional link to hierarchical routing conversation
            metadata: Optional metadata

        Returns:
            Conversation instance
        """
        conversation = Conversation(
            conversation_type=ConversationType.AGENT_AGENT,
            initiator_id=initiator_agent_id,
            initiator_type=ParticipantType.AGENT,
            primary_responder_id=responder_agent_id,
            agent_conversation_id=agent_conversation_id,
            title=title or "Agent Collaboration",
            status="active",
            metadata=metadata or {}
        )

        db.add(conversation)
        await db.flush()

        # Add participants
        initiator_participant = ConversationParticipant(
            conversation_id=conversation.id,
            participant_id=initiator_agent_id,
            participant_type=ParticipantType.AGENT,
            role="initiator"
        )
        responder_participant = ConversationParticipant(
            conversation_id=conversation.id,
            participant_id=responder_agent_id,
            participant_type=ParticipantType.AGENT,
            role="primary_responder"
        )

        db.add_all([initiator_participant, responder_participant])

        # Send initial question if provided
        if initial_question:
            await ConversationService._add_message(
                db=db,
                conversation_id=conversation.id,
                sender_id=initiator_agent_id,
                sender_type=ParticipantType.AGENT,
                role="user",
                content=initial_question
            )

        await db.commit()
        await db.refresh(conversation)

        logger.info(f"Created agent-agent conversation {conversation.id} "
                   f"({initiator_agent_id} → {responder_agent_id})")
        return conversation


    @staticmethod
    async def _add_message(
        db: AsyncSession,
        conversation_id: UUID,
        sender_id: UUID,
        sender_type: str,
        role: str,
        content: str,
        agent_message_id: Optional[UUID] = None,
        token_info: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """
        Add a message to the conversation.

        Internal method used by both user and agent messages.
        """
        message = ConversationMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            role=role,
            content=content,
            agent_message_id=agent_message_id,
            input_tokens=token_info.get("input_tokens") if token_info else None,
            output_tokens=token_info.get("output_tokens") if token_info else None,
            total_tokens=token_info.get("total_tokens") if token_info else None,
            metadata=metadata or {}
        )

        db.add(message)

        # Update conversation
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one()

        conversation.total_messages += 1
        conversation.last_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        if token_info and token_info.get("total_tokens"):
            conversation.total_tokens_used += token_info["total_tokens"]

        await db.flush()
        return message


    @staticmethod
    async def send_message_and_get_response(
        db: AsyncSession,
        conversation_id: UUID,
        message_content: str,
        sender_id: UUID,
        sender_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message and get agent response.

        Works for both:
        - User sending to agent
        - Agent sending to another agent

        Args:
            db: Database session
            conversation_id: Conversation ID
            message_content: Message content
            sender_id: Who is sending (user or agent)
            sender_type: 'user' or 'agent'
            metadata: Optional metadata

        Returns:
            Dict with sent message, response message, and token info
        """
        start_time = datetime.utcnow()

        # Get conversation with messages
        stmt = select(Conversation).where(
            Conversation.id == conversation_id
        ).options(selectinload(Conversation.messages))
        result = await db.execute(stmt)
        conversation = result.scalar_one()

        # Verify conversation is active
        if conversation.status != "active":
            raise ValueError(f"Conversation {conversation_id} is not active")

        # Get responder agent
        stmt = select(SquadMember).where(SquadMember.id == conversation.primary_responder_id)
        result = await db.execute(stmt)
        responder_agent = result.scalar_one()

        # Check token limit
        if responder_agent.max_conversation_tokens:
            if conversation.total_tokens_used >= responder_agent.max_conversation_tokens:
                raise ValueError(f"Conversation has reached token limit")

        # Add sender's message
        sender_message = await ConversationService._add_message(
            db=db,
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_type=sender_type,
            role="user",
            content=message_content,
            metadata=metadata
        )

        # Build conversation history for agent
        conversation_history = []
        for msg in conversation.messages[:-1]:  # Exclude the message we just added
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })

        # Get or create agent instance
        agent = AgentFactory.get_agent(responder_agent.id)
        if not agent:
            agent = AgentFactory.create_agent(
                agent_id=responder_agent.id,
                role=responder_agent.role,
                llm_provider=responder_agent.llm_provider,
                llm_model=responder_agent.llm_model,
                system_prompt=responder_agent.system_prompt,
                temperature=responder_agent.config.get("temperature", 0.7)
            )

        # Get agent response with context
        history = [
            AgentConversationMessage(role=msg["role"], content=msg["content"])
            for msg in conversation_history
        ]

        agent_response = await agent.process_message(
            message=message_content,
            conversation_history=history
        )

        # Calculate response time
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Add agent's response
        response_message = ConversationMessage(
            conversation_id=conversation_id,
            sender_id=responder_agent.id,
            sender_type=ParticipantType.AGENT,
            role="assistant",
            content=agent_response.content,
            input_tokens=agent_response.metadata.get("input_tokens"),
            output_tokens=agent_response.metadata.get("output_tokens"),
            total_tokens=agent_response.metadata.get("total_tokens"),
            model_used=responder_agent.llm_model,
            temperature=responder_agent.config.get("temperature"),
            llm_provider=responder_agent.llm_provider,
            response_time_ms=response_time_ms,
            metadata=agent_response.metadata
        )

        db.add(response_message)

        # Update conversation totals
        conversation.total_messages += 1
        conversation.last_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        if response_message.total_tokens:
            conversation.total_tokens_used += response_message.total_tokens

        await db.commit()
        await db.refresh(sender_message)
        await db.refresh(response_message)

        logger.info(
            f"Conversation {conversation_id}: {sender_type} message + agent response "
            f"({response_message.total_tokens} tokens, {response_time_ms}ms)"
        )

        return {
            "sender_message": sender_message,
            "response_message": response_message,
            "tokens_used": response_message.total_tokens or 0,
            "conversation_total_tokens": conversation.total_tokens_used,
            "response_time_ms": response_time_ms
        }


    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        include_messages: bool = False,
        include_participants: bool = False
    ) -> Conversation:
        """
        Get a conversation by ID.

        Args:
            db: Database session
            conversation_id: Conversation ID
            include_messages: Load messages
            include_participants: Load participants

        Returns:
            Conversation instance
        """
        stmt = select(Conversation).where(Conversation.id == conversation_id)

        if include_messages:
            stmt = stmt.options(selectinload(Conversation.messages))

        if include_participants:
            stmt = stmt.options(selectinload(Conversation.participants))

        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")

        return conversation


    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        initiator_id: Optional[UUID] = None,
        initiator_type: Optional[str] = None,
        conversation_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List conversations with filters.

        Args:
            db: Database session
            initiator_id: Filter by initiator
            initiator_type: Filter by initiator type
            conversation_type: Filter by conversation type
            status: Filter by status
            limit: Max results
            offset: Pagination offset

        Returns:
            Dict with conversations and pagination info
        """
        filters = []

        if initiator_id:
            filters.append(Conversation.initiator_id == initiator_id)

        if initiator_type:
            filters.append(Conversation.initiator_type == initiator_type)

        if conversation_type:
            filters.append(Conversation.conversation_type == conversation_type)

        if status:
            filters.append(Conversation.status == status)

        # Get total count
        count_stmt = select(func.count(Conversation.id)).where(and_(*filters))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # Get conversations
        stmt = select(Conversation).where(and_(*filters)).order_by(
            desc(Conversation.last_message_at)
        ).limit(limit).offset(offset)

        result = await db.execute(stmt)
        conversations = result.scalars().all()

        return {
            "conversations": conversations,
            "total": total,
            "page": offset // limit + 1,
            "page_size": limit,
            "has_more": (offset + limit) < total
        }
```

---

## Integration Points

### 1. Integration with AgentMessageHandler

**When agents send messages to each other, automatically create/update conversations:**

```python
# backend/agents/interaction/agent_message_handler.py

class AgentMessageHandler:
    async def process_incoming_message(self, message: AgentMessage):
        """Process incoming message and maintain conversation context"""

        # Check if this message is part of a multi-turn conversation
        existing_conversation = await self._get_or_create_agent_conversation(
            initiator_id=message.sender_id,
            responder_id=message.recipient_id,
            agent_conversation_id=message.conversation_id  # From hierarchical routing
        )

        if existing_conversation:
            # This is a follow-up message - include conversation history
            response = await ConversationService.send_message_and_get_response(
                db=self.db,
                conversation_id=existing_conversation.id,
                message_content=message.content,
                sender_id=message.sender_id,
                sender_type=ParticipantType.AGENT
            )

            return response["response_message"]
        else:
            # First message - process normally but create conversation
            response = await self._process_new_agent_message(message)
            return response
```

### 2. Integration with Hierarchical Routing

**When escalating, transfer conversation context:**

```python
# backend/agents/interaction/escalation_service.py

class EscalationService:
    async def escalate_conversation(
        self,
        agent_conversation_id: UUID,
        next_responder_id: UUID
    ):
        """Escalate with full conversation context"""

        # Get the multi-turn conversation linked to this hierarchical conversation
        multi_turn_conv = await ConversationService.get_conversation_by_agent_conversation(
            db=self.db,
            agent_conversation_id=agent_conversation_id,
            include_messages=True
        )

        if multi_turn_conv:
            # Update the primary responder
            multi_turn_conv.primary_responder_id = next_responder_id
            multi_turn_conv.status = "escalated"

            # Add new participant
            new_participant = ConversationParticipant(
                conversation_id=multi_turn_conv.id,
                participant_id=next_responder_id,
                participant_type=ParticipantType.AGENT,
                role="escalated_responder"
            )

            self.db.add(new_participant)

            # Send escalation notification with FULL CONTEXT
            await self._send_escalation_message(
                conversation=multi_turn_conv,
                new_responder_id=next_responder_id,
                conversation_history=multi_turn_conv.messages
            )

            await self.db.commit()
```

### 3. Integration with BaseAgent

**Agents automatically use conversation context:**

```python
# In BaseAgent.process_message()

# The conversation_history parameter now comes from multi-turn conversations
async def process_message(
    self,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[ConversationMessage]] = None  # ← From multi-turn
) -> AgentResponse:
    """Process message with optional conversation history"""

    # Build messages with history
    messages = self._build_messages(message, context, conversation_history)

    # Call LLM with full context
    response = await self._call_llm(messages)

    return response
```

---

## API Design

### Updated Endpoints

```python
# backend/api/v1/endpoints/conversations.py

# USER-AGENT CONVERSATIONS
@router.post("/conversations/user-agent", response_model=ConversationResponse)
async def create_user_agent_conversation(...)

@router.post("/conversations/{id}/messages", response_model=SendMessageResponse)
async def send_message(...)

# AGENT-AGENT CONVERSATIONS (NEW!)
@router.post("/conversations/agent-agent", response_model=ConversationResponse)
async def create_agent_agent_conversation(
    request: CreateAgentConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create an agent-agent conversation.

    This allows agents to have contextual conversations with each other.
    """
    # Verify both agents exist and are accessible
    # Create conversation
    # Return conversation details


@router.get("/conversations/agent/{agent_id}", response_model=ConversationListResponse)
async def list_agent_conversations(
    agent_id: UUID,
    conversation_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List all conversations for a specific agent.

    Includes both:
    - Conversations where agent is initiator
    - Conversations where agent is responder
    """
```

---

## Implementation Phases

### Updated Timeline: 18-24 days

| Phase | Duration | What's New |
|-------|----------|------------|
| 1. Database & Models | 3-4 days | **+1 day** for agent-agent support |
| 2. Service Layer | 4-5 days | **+1 day** for agent conversation logic |
| 3. Pydantic Schemas | 2 days | **+1 day** for agent schemas |
| 4. API Endpoints | 3-4 days | **+1 day** for agent endpoints |
| 5. Integration | 3-4 days | **NEW** - Integration with hierarchical routing |
| 6. Testing & QA | 4-5 days | **+1 day** for agent-agent test cases |
| 7. Documentation | 2 days | Same |

---

## Testing Strategy

### New Test Cases for Agent-Agent Conversations

```python
@pytest.mark.asyncio
async def test_agent_asks_agent_with_context(db_session, backend_dev, tech_lead):
    """Test agent asking another agent maintains context"""

    # Backend dev asks tech lead
    conversation = await ConversationService.create_agent_agent_conversation(
        db=db_session,
        initiator_agent_id=backend_dev.id,
        responder_agent_id=tech_lead.id,
        initial_question="How should I structure the API?"
    )

    # Tech lead responds
    result1 = await ConversationService.send_message_and_get_response(
        db=db_session,
        conversation_id=conversation.id,
        message_content="How should I structure the API?",
        sender_id=backend_dev.id,
        sender_type=ParticipantType.AGENT
    )

    # Backend dev follows up
    result2 = await ConversationService.send_message_and_get_response(
        db=db_session,
        conversation_id=conversation.id,
        message_content="What about authentication?",
        sender_id=backend_dev.id,
        sender_type=ParticipantType.AGENT
    )

    # Tech lead's response should reference the API structure discussion
    response = result2["response_message"].content.lower()
    assert "api" in response or "structure" in response


@pytest.mark.asyncio
async def test_escalation_maintains_conversation_context(
    db_session, backend_dev, tech_lead, solution_architect
):
    """Test that escalation preserves conversation history"""

    # Create initial conversation
    conversation = await ConversationService.create_agent_agent_conversation(
        db=db_session,
        initiator_agent_id=backend_dev.id,
        responder_agent_id=tech_lead.id,
        initial_question="How do I design for 100k requests/sec?"
    )

    # Add some exchanges
    for i in range(3):
        await ConversationService.send_message_and_get_response(
            db=db_session,
            conversation_id=conversation.id,
            message_content=f"Follow-up question {i}",
            sender_id=backend_dev.id,
            sender_type=ParticipantType.AGENT
        )

    # Escalate to solution architect
    await EscalationService.escalate_with_context(
        db=db_session,
        conversation_id=conversation.id,
        new_responder_id=solution_architect.id
    )

    # Solution architect should see full history
    await db_session.refresh(conversation)
    assert conversation.primary_responder_id == solution_architect.id
    assert conversation.total_messages >= 6  # 3 questions + 3 responses
    assert len(conversation.messages) >= 6
```

---

## Summary of Changes from V1

### What Changed

1. **Database Schema**
   - Unified `conversations` table (not `user_conversations`)
   - Added `conversation_type`, `initiator_type`, `sender_type` fields
   - Added `conversation_participants` table for multi-party support
   - Added `agent_conversation_id` link to hierarchical routing

2. **Service Layer**
   - Split into `create_user_agent_conversation()` and `create_agent_agent_conversation()`
   - Universal `send_message_and_get_response()` for both user and agent messages
   - Support for linking conversations to hierarchical routing system

3. **Integration Points**
   - Integration with `AgentMessageHandler`
   - Integration with `EscalationService`
   - Integration with `RoutingEngine`

4. **API Endpoints**
   - Added `/conversations/agent-agent` endpoints
   - Added `/conversations/agent/{agent_id}` to list agent conversations
   - Existing user endpoints still work

5. **Testing**
   - Additional test cases for agent-agent scenarios
   - Escalation with context tests
   - Multi-party conversation tests

### What Stayed the Same

- Token tracking and limits
- Conversation archiving
- Summary generation
- Authorization model (users can only see their conversations, agents through API)
- Frontend integration approach

---

## Questions for Review

1. **Conversation Ownership**: How should we handle permissions for agent-agent conversations?
   - Option A: Only system can create them (via hierarchical routing)
   - Option B: Users can create them for their squad
   - Option C: Agents can self-initiate

2. **Conversation Limits**: Should there be limits on:
   - Max concurrent conversations per agent?
   - Max message history per conversation?

3. **Integration Priority**: Which integration is most important?
   - A. Hierarchical routing escalation with context
   - B. AgentMessageHandler automatic context
   - C. Manual agent-agent conversations via API

4. **Multi-Party Conversations**: Should we support:
   - Multiple agents in one conversation?
   - Group conversations with users + multiple agents?

5. **Backward Compatibility**: Should we:
   - Automatically create conversations for all agent-agent messages?
   - Only create when explicitly requested?
   - Make it opt-in per squad member?

---

## Next Steps

1. **Review this updated plan**
2. **Answer the questions above**
3. **Approve to begin implementation**
4. **I'll start with Phase 1: Database & Models**

This universal conversation system will make your agent squad dramatically more intelligent and collaborative! 🚀
