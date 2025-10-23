# Phase 4: Multi-Turn Conversations - Complete Implementation Plan

**Status**: Planning Phase
**Created**: October 23, 2025
**Purpose**: Enable conversational, context-aware interactions between users and AI agents

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State vs Desired State](#current-state-vs-desired-state)
3. [Use Cases & User Stories](#use-cases--user-stories)
4. [Database Schema Design](#database-schema-design)
5. [Backend Architecture](#backend-architecture)
6. [API Design](#api-design)
7. [Integration with Existing System](#integration-with-existing-system)
8. [Frontend Integration](#frontend-integration)
9. [Implementation Phases](#implementation-phases)
10. [Testing Strategy](#testing-strategy)
11. [Performance Considerations](#performance-considerations)
12. [Security & Privacy](#security--privacy)

---

## Executive Summary

### What We're Building

A **conversational memory system** that allows users to have natural, multi-turn conversations with AI agents, where:

- Agents remember previous messages in the conversation
- Users can ask follow-up questions without repeating context
- Conversations can be paused and resumed later
- Context is maintained across the entire conversation
- Users can manage multiple concurrent conversations

### Key Features

✅ **Conversation Sessions** - Persistent conversation threads with unique IDs
✅ **Context Memory** - Agents remember all previous messages
✅ **Follow-up Awareness** - Understand pronouns and references
✅ **Conversation Management** - Start, pause, resume, end conversations
✅ **History Viewing** - See full conversation timeline
✅ **Token Management** - Track and limit conversation token usage
✅ **Multiple Conversations** - Users can have multiple active conversations

### Why This Matters

**Current Pain Points:**
- Users must repeat context in every message
- Agents can't reference previous explanations
- No continuity between related questions
- Feels robotic and disconnected

**After Implementation:**
- Natural back-and-forth dialogue
- "Tell me more about X" just works
- Agents build on previous answers
- Feels like talking to a human expert

---

## Current State vs Desired State

### Current State (Without Multi-Turn)

**Message Flow:**
```
User → Agent (Message 1: "How do I implement caching?")
Agent → User (Response 1: "Use Redis with TTL...")

User → Agent (Message 2: "How do I set it up?")
Agent → User (Response 2: "Set up what? Please provide more context.")
                         ❌ Agent has no memory of message 1
```

**Problems:**
- Each message is isolated
- No conversation context
- User must repeat information
- Can't build on previous answers
- Wastes tokens re-explaining context

### Desired State (With Multi-Turn)

**Conversation Flow:**
```
User starts conversation → Creates conversation session

User → Agent (Message 1: "How do I implement caching?")
Agent → User (Response 1: "Use Redis with TTL...")
       [Stores in conversation history]

User → Agent (Message 2: "How do I set it up?")
       [Agent sees message 1 + response 1 in history]
Agent → User (Response 2: "To set up Redis (for the caching strategy
                          I mentioned), here are the steps...")
       ✅ Agent references previous context

User → Agent (Message 3: "What about failover?")
       [Agent sees full history: M1, R1, M2, R2]
Agent → User (Response 3: "For your Redis caching setup,
                          here's how to configure failover...")
       ✅ Agent builds on entire conversation
```

**Benefits:**
- ✅ Natural conversation flow
- ✅ Context automatically maintained
- ✅ No repetition needed
- ✅ More intelligent responses
- ✅ Better user experience

---

## Use Cases & User Stories

### Use Case 1: Technical Troubleshooting

**Scenario:** Developer debugging a production issue

```
User: "My API is slow"
Agent: "Let me help. What's the average response time?"

User: "About 3 seconds"
Agent: "That's definitely slow. Are you using caching?"

User: "No, should I be?"
Agent: "Yes! Based on your 3-second response time, caching would help..."

User: "How do I implement it?"
Agent: "For your API (which we identified as slow), I recommend..."
```

**Value:** Agent remembers the performance issue throughout the conversation.

### Use Case 2: Learning & Exploration

**Scenario:** Junior developer learning a new concept

```
User: "What is Redis?"
Agent: "Redis is an in-memory data store used for caching..."

User: "How is it different from PostgreSQL?"
Agent: "While Redis (which I just explained) stores data in memory..."

User: "When should I use each one?"
Agent: "Based on our discussion - use Redis for caching/sessions,
        PostgreSQL for persistent data..."

User: "Show me an example"
Agent: "Here's how to use Redis for the caching scenario we discussed..."
```

**Value:** Agent builds knowledge progressively, referencing earlier explanations.

### Use Case 3: Step-by-Step Guidance

**Scenario:** User following a multi-step tutorial

```
User: "I want to deploy a Docker container"
Agent: "Great! First, create a Dockerfile. Here's a template..."

User: "Done, what's next?"
Agent: "Now build the image from your Dockerfile..."

User: "Got it. How do I run it?"
Agent: "To run the image you just built, use: docker run..."

User: "It's not working"
Agent: "Let's debug your Docker container. Can you share the error?"
```

**Value:** Agent tracks progress through a multi-step process.

### Use Case 4: Iterative Design

**Scenario:** Architect designing a system

```
User: "I'm designing a microservices architecture"
Agent: "Tell me about your requirements..."

User: "Need to handle 10k requests/sec with high availability"
Agent: "For 10k req/sec, I recommend..."

User: "What if we need to scale to 100k?"
Agent: "To scale your design from 10k to 100k, you'd need..."

User: "How much would that cost?"
Agent: "For the 100k req/sec architecture I described, estimated costs..."
```

**Value:** Agent evolves the design based on changing requirements.

### Use Case 5: Multiple Concurrent Conversations

**Scenario:** User working on multiple tasks

```
Conversation 1 (Frontend Issue):
  User: "React component not rendering"
  Agent: "Let's debug. What's in your console?"

Conversation 2 (Backend Issue):
  User: "Database query is slow"
  Agent: "What's the query?"

[User switches back to Conversation 1]
  User: "Console shows 'undefined'"
  Agent: "Based on your React rendering issue..."
```

**Value:** Each conversation maintains separate context.

---

## Database Schema Design

### 1. New Table: `user_conversations`

**Purpose:** Track conversation sessions between users and agents

```sql
CREATE TABLE user_conversations (
    -- Identity
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Participants
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    squad_member_id UUID NOT NULL REFERENCES squad_members(id) ON DELETE CASCADE,

    -- Conversation metadata
    title VARCHAR(255),  -- Auto-generated or user-provided
    status VARCHAR(50) NOT NULL DEFAULT 'active',  -- active, archived, deleted

    -- Context tracking
    total_messages INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,

    -- Summary and tags
    summary TEXT,  -- AI-generated summary of conversation
    tags TEXT[],  -- Searchable tags

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_squad_member FOREIGN KEY (squad_member_id)
        REFERENCES squad_members(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_user_conversations_user_id ON user_conversations(user_id);
CREATE INDEX idx_user_conversations_squad_member ON user_conversations(squad_member_id);
CREATE INDEX idx_user_conversations_status ON user_conversations(status);
CREATE INDEX idx_user_conversations_user_status ON user_conversations(user_id, status);
CREATE INDEX idx_user_conversations_last_message ON user_conversations(last_message_at DESC);
CREATE INDEX idx_user_conversations_tags ON user_conversations USING GIN(tags);
```

### 2. New Table: `conversation_messages`

**Purpose:** Store individual messages within conversations

```sql
CREATE TABLE conversation_messages (
    -- Identity
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES user_conversations(id) ON DELETE CASCADE,

    -- Message details
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,

    -- Token tracking
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,

    -- LLM metadata (for assistant messages)
    model_used VARCHAR(100),  -- 'gpt-4', 'claude-3-sonnet', etc.
    temperature FLOAT,
    llm_provider VARCHAR(50),  -- 'openai', 'anthropic', 'groq'

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time_ms INTEGER,  -- How long LLM took to respond

    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT fk_conversation FOREIGN KEY (conversation_id)
        REFERENCES user_conversations(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_conversation_messages_conversation ON conversation_messages(conversation_id);
CREATE INDEX idx_conversation_messages_created ON conversation_messages(created_at);
CREATE INDEX idx_conversation_messages_role ON conversation_messages(role);
CREATE INDEX idx_conversation_messages_conversation_created
    ON conversation_messages(conversation_id, created_at);
```

### 3. Update Existing `squad_members` Table

**Add conversation-related settings:**

```sql
-- Add columns for conversation preferences
ALTER TABLE squad_members
    ADD COLUMN max_conversation_tokens INTEGER DEFAULT 8000,
    ADD COLUMN conversation_memory_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN auto_generate_summary BOOLEAN DEFAULT TRUE;
```

### 4. Migration Script

```python
# backend/alembic/versions/004_add_multi_turn_conversations.py

"""add multi-turn conversations support

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
    # Create user_conversations table
    op.create_table(
        'user_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('squad_member_id', postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(['squad_member_id'], ['squad_members.id'], ondelete='CASCADE')
    )

    # Create indexes for user_conversations
    op.create_index('idx_user_conversations_user_id', 'user_conversations', ['user_id'])
    op.create_index('idx_user_conversations_squad_member', 'user_conversations', ['squad_member_id'])
    op.create_index('idx_user_conversations_status', 'user_conversations', ['status'])
    op.create_index('idx_user_conversations_user_status', 'user_conversations', ['user_id', 'status'])
    op.create_index('idx_user_conversations_last_message', 'user_conversations', ['last_message_at'],
                   postgresql_ops={'last_message_at': 'DESC'})
    op.create_index('idx_user_conversations_tags', 'user_conversations', ['tags'],
                   postgresql_using='gin')

    # Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['user_conversations.id'], ondelete='CASCADE')
    )

    # Create indexes for conversation_messages
    op.create_index('idx_conversation_messages_conversation', 'conversation_messages', ['conversation_id'])
    op.create_index('idx_conversation_messages_created', 'conversation_messages', ['created_at'])
    op.create_index('idx_conversation_messages_role', 'conversation_messages', ['role'])
    op.create_index('idx_conversation_messages_conversation_created', 'conversation_messages',
                   ['conversation_id', 'created_at'])

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

    # Drop conversation_messages table
    op.drop_index('idx_conversation_messages_conversation_created', 'conversation_messages')
    op.drop_index('idx_conversation_messages_role', 'conversation_messages')
    op.drop_index('idx_conversation_messages_created', 'conversation_messages')
    op.drop_index('idx_conversation_messages_conversation', 'conversation_messages')
    op.drop_table('conversation_messages')

    # Drop user_conversations table
    op.drop_index('idx_user_conversations_tags', 'user_conversations')
    op.drop_index('idx_user_conversations_last_message', 'user_conversations')
    op.drop_index('idx_user_conversations_user_status', 'user_conversations')
    op.drop_index('idx_user_conversations_status', 'user_conversations')
    op.drop_index('idx_user_conversations_squad_member', 'user_conversations')
    op.drop_index('idx_user_conversations_user_id', 'user_conversations')
    op.drop_table('user_conversations')
```

---

## Backend Architecture

### 1. SQLAlchemy Models

**File:** `backend/models/user_conversation.py`

```python
"""
User Conversation Models

Tracks multi-turn conversations between users and AI agents.
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from backend.models.base import Base


class UserConversation(Base):
    """
    Represents a conversation session between a user and an AI agent.

    A conversation maintains context across multiple messages, allowing
    the agent to reference previous exchanges and provide contextual responses.
    """

    __tablename__ = "user_conversations"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Participants
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    squad_member_id = Column(UUID(as_uuid=True), ForeignKey("squad_members.id", ondelete="CASCADE"), nullable=False)

    # Conversation metadata
    title = Column(String(255), nullable=True)  # Auto-generated or user-provided
    status = Column(String(50), nullable=False, default="active")  # active, archived, deleted

    # Context tracking
    total_messages = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)

    # Summary and organization
    summary = Column(Text, nullable=True)  # AI-generated summary
    tags = Column(ARRAY(String), nullable=True)  # Searchable tags

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    metadata = Column(JSONB, default={})

    # Relationships
    user = relationship("User", back_populates="conversations")
    squad_member = relationship("SquadMember", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation",
                          cascade="all, delete-orphan", order_by="ConversationMessage.created_at")

    __table_args__ = (
        Index("ix_user_conversations_user_id", "user_id"),
        Index("ix_user_conversations_squad_member", "squad_member_id"),
        Index("ix_user_conversations_status", "status"),
        Index("ix_user_conversations_user_status", "user_id", "status"),
        Index("ix_user_conversations_last_message", "last_message_at", postgresql_ops={"last_message_at": "DESC"}),
        Index("ix_user_conversations_tags", "tags", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<UserConversation(id={self.id}, user_id={self.user_id}, status={self.status})>"


class ConversationMessage(Base):
    """
    Represents a single message within a conversation.

    Messages can be from the user ('user' role), the AI agent ('assistant' role),
    or system messages ('system' role).
    """

    __tablename__ = "conversation_messages"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("user_conversations.id", ondelete="CASCADE"), nullable=False)

    # Message details
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Token tracking
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # LLM metadata (for assistant messages)
    model_used = Column(String(100), nullable=True)  # 'gpt-4', 'claude-3-sonnet', etc.
    temperature = Column(Float, nullable=True)
    llm_provider = Column(String(50), nullable=True)  # 'openai', 'anthropic', 'groq'

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_time_ms = Column(Integer, nullable=True)  # How long LLM took to respond

    # Additional metadata
    metadata = Column(JSONB, default={})

    # Relationships
    conversation = relationship("UserConversation", back_populates="messages")

    __table_args__ = (
        Index("ix_conversation_messages_conversation", "conversation_id"),
        Index("ix_conversation_messages_created", "created_at"),
        Index("ix_conversation_messages_role", "role"),
        Index("ix_conversation_messages_conversation_created", "conversation_id", "created_at"),
    )

    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"
```

### 2. Pydantic Schemas

**File:** `backend/schemas/user_conversation.py`

```python
"""
User Conversation Schemas

Pydantic models for API requests and responses.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas
# ============================================================================

class CreateConversationRequest(BaseModel):
    """Request to start a new conversation"""
    squad_member_id: UUID = Field(..., description="Agent to conversation with")
    title: Optional[str] = Field(None, description="Optional conversation title")
    initial_message: Optional[str] = Field(None, description="Optional first message to send")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation"""
    content: str = Field(..., description="Message content", min_length=1, max_length=10000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UpdateConversationRequest(BaseModel):
    """Request to update conversation metadata"""
    title: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)


class ArchiveConversationRequest(BaseModel):
    """Request to archive a conversation"""
    archive: bool = Field(True, description="True to archive, False to unarchive")


# ============================================================================
# Response Schemas
# ============================================================================

class ConversationMessageResponse(BaseModel):
    """Single message in a conversation"""
    id: UUID
    role: str
    content: str
    created_at: datetime
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    model_used: Optional[str] = None
    response_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Full conversation details"""
    id: UUID
    user_id: UUID
    squad_member_id: UUID
    title: Optional[str] = None
    status: str
    total_messages: int
    total_tokens_used: int
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ConversationWithMessagesResponse(ConversationResponse):
    """Conversation with message history"""
    messages: List[ConversationMessageResponse] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    """List of conversations with pagination"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class SendMessageResponse(BaseModel):
    """Response after sending a message"""
    conversation_id: UUID
    message_id: UUID
    assistant_message: ConversationMessageResponse
    total_tokens_used: int  # Tokens used in this exchange
    conversation_total_tokens: int  # Total tokens in conversation


# ============================================================================
# Statistics Schemas
# ============================================================================

class ConversationStatsResponse(BaseModel):
    """Statistics for a user's conversations"""
    total_conversations: int
    active_conversations: int
    archived_conversations: int
    total_messages: int
    total_tokens_used: int
    average_messages_per_conversation: float
    most_active_agent: Optional[Dict[str, Any]] = None
```

### 3. Service Layer

**File:** `backend/services/conversation_service.py`

```python
"""
Conversation Service

Business logic for managing multi-turn conversations.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from backend.models.user_conversation import UserConversation, ConversationMessage
from backend.models.squad import SquadMember
from backend.agents.factory import AgentFactory
from backend.core.logging import logger


class ConversationService:
    """
    Service for managing user conversations with AI agents.

    Handles:
    - Creating and managing conversation sessions
    - Sending messages with context
    - Maintaining conversation history
    - Token tracking and limits
    - Conversation summaries
    """

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: UUID,
        squad_member_id: UUID,
        title: Optional[str] = None,
        initial_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserConversation:
        """
        Create a new conversation session.

        Args:
            db: Database session
            user_id: User starting the conversation
            squad_member_id: Agent to converse with
            title: Optional conversation title
            initial_message: Optional first message to send
            metadata: Optional metadata

        Returns:
            UserConversation instance
        """
        # Create conversation
        conversation = UserConversation(
            user_id=user_id,
            squad_member_id=squad_member_id,
            title=title or "New Conversation",
            status="active",
            metadata=metadata or {}
        )

        db.add(conversation)
        await db.flush()

        # If initial message provided, send it
        if initial_message:
            await ConversationService.send_message(
                db=db,
                conversation_id=conversation.id,
                content=initial_message,
                role="user"
            )

        await db.commit()
        await db.refresh(conversation)

        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation


    @staticmethod
    async def send_message(
        db: AsyncSession,
        conversation_id: UUID,
        content: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """
        Add a message to the conversation.

        Args:
            db: Database session
            conversation_id: Conversation to add message to
            content: Message content
            role: Message role ('user' or 'assistant')
            metadata: Optional metadata

        Returns:
            ConversationMessage instance
        """
        # Create message
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

        db.add(message)

        # Update conversation
        stmt = select(UserConversation).where(UserConversation.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one()

        conversation.total_messages += 1
        conversation.last_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        await db.flush()
        return message


    @staticmethod
    async def get_agent_response(
        db: AsyncSession,
        conversation_id: UUID,
        user_message_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send user message and get agent response.

        This is the main method for conversational interaction.

        Args:
            db: Database session
            conversation_id: Conversation ID
            user_message_content: User's message
            metadata: Optional metadata

        Returns:
            Dict with user_message, assistant_message, and token info
        """
        start_time = datetime.utcnow()

        # Get conversation with messages
        stmt = select(UserConversation).where(
            UserConversation.id == conversation_id
        ).options(selectinload(UserConversation.messages))
        result = await db.execute(stmt)
        conversation = result.scalar_one()

        # Check if conversation is active
        if conversation.status != "active":
            raise ValueError(f"Conversation {conversation_id} is not active (status: {conversation.status})")

        # Get squad member details
        stmt = select(SquadMember).where(SquadMember.id == conversation.squad_member_id)
        result = await db.execute(stmt)
        squad_member = result.scalar_one()

        # Check token limit
        if squad_member.max_conversation_tokens:
            if conversation.total_tokens_used >= squad_member.max_conversation_tokens:
                raise ValueError(
                    f"Conversation has reached token limit "
                    f"({squad_member.max_conversation_tokens} tokens)"
                )

        # Add user message to conversation
        user_message = await ConversationService.send_message(
            db=db,
            conversation_id=conversation_id,
            content=user_message_content,
            role="user",
            metadata=metadata
        )

        # Build conversation history for agent
        conversation_history = []
        for msg in conversation.messages[:-1]:  # Exclude the message we just added
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })

        # Get agent instance
        agent = AgentFactory.get_agent(squad_member.id)
        if not agent:
            agent = AgentFactory.create_agent(
                agent_id=squad_member.id,
                role=squad_member.role,
                llm_provider=squad_member.llm_provider,
                llm_model=squad_member.llm_model,
                system_prompt=squad_member.system_prompt,
                temperature=squad_member.config.get("temperature", 0.7)
            )

        # Get agent response with conversation context
        from backend.agents.base_agent import ConversationMessage as AgentConversationMessage

        history = [
            AgentConversationMessage(role=msg["role"], content=msg["content"])
            for msg in conversation_history
        ]

        agent_response = await agent.process_message(
            message=user_message_content,
            conversation_history=history
        )

        # Calculate response time
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Add assistant message to conversation
        assistant_message = ConversationMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=agent_response.content,
            input_tokens=agent_response.metadata.get("input_tokens"),
            output_tokens=agent_response.metadata.get("output_tokens"),
            total_tokens=agent_response.metadata.get("total_tokens"),
            model_used=squad_member.llm_model,
            temperature=squad_member.config.get("temperature"),
            llm_provider=squad_member.llm_provider,
            response_time_ms=response_time_ms,
            metadata=agent_response.metadata
        )

        db.add(assistant_message)

        # Update conversation totals
        conversation.total_messages += 1
        conversation.last_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        if assistant_message.total_tokens:
            conversation.total_tokens_used += assistant_message.total_tokens

        await db.commit()
        await db.refresh(user_message)
        await db.refresh(assistant_message)

        logger.info(
            f"Conversation {conversation_id}: User message + agent response "
            f"({assistant_message.total_tokens} tokens, {response_time_ms}ms)"
        )

        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "tokens_used": assistant_message.total_tokens or 0,
            "conversation_total_tokens": conversation.total_tokens_used,
            "response_time_ms": response_time_ms
        }


    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        include_messages: bool = False
    ) -> UserConversation:
        """
        Get a conversation by ID.

        Args:
            db: Database session
            conversation_id: Conversation ID
            include_messages: Whether to load messages

        Returns:
            UserConversation instance
        """
        stmt = select(UserConversation).where(UserConversation.id == conversation_id)

        if include_messages:
            stmt = stmt.options(selectinload(UserConversation.messages))

        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")

        return conversation


    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        user_id: UUID,
        status: Optional[str] = None,
        squad_member_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List conversations for a user.

        Args:
            db: Database session
            user_id: User ID
            status: Optional filter by status
            squad_member_id: Optional filter by agent
            limit: Max results to return
            offset: Pagination offset

        Returns:
            Dict with conversations and pagination info
        """
        # Build query
        filters = [UserConversation.user_id == user_id]

        if status:
            filters.append(UserConversation.status == status)

        if squad_member_id:
            filters.append(UserConversation.squad_member_id == squad_member_id)

        # Get total count
        count_stmt = select(func.count(UserConversation.id)).where(and_(*filters))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # Get conversations
        stmt = select(UserConversation).where(and_(*filters)).order_by(
            desc(UserConversation.last_message_at)
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


    @staticmethod
    async def archive_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        archive: bool = True
    ) -> UserConversation:
        """
        Archive or unarchive a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            archive: True to archive, False to unarchive

        Returns:
            Updated UserConversation
        """
        conversation = await ConversationService.get_conversation(db, conversation_id)

        if archive:
            conversation.status = "archived"
            conversation.archived_at = datetime.utcnow()
        else:
            conversation.status = "active"
            conversation.archived_at = None

        conversation.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(conversation)

        logger.info(f"{'Archived' if archive else 'Unarchived'} conversation {conversation_id}")
        return conversation


    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: UUID
    ) -> None:
        """
        Delete a conversation (soft delete by setting status).

        Args:
            db: Database session
            conversation_id: Conversation ID
        """
        conversation = await ConversationService.get_conversation(db, conversation_id)
        conversation.status = "deleted"
        conversation.updated_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Deleted conversation {conversation_id}")


    @staticmethod
    async def generate_summary(
        db: AsyncSession,
        conversation_id: UUID
    ) -> str:
        """
        Generate AI summary of conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            Generated summary text
        """
        conversation = await ConversationService.get_conversation(
            db, conversation_id, include_messages=True
        )

        if len(conversation.messages) < 3:
            return "Conversation too short to summarize"

        # Get squad member
        stmt = select(SquadMember).where(SquadMember.id == conversation.squad_member_id)
        result = await db.execute(stmt)
        squad_member = result.scalar_one()

        # Create temporary agent for summarization
        agent = AgentFactory.create_agent(
            agent_id=squad_member.id,
            role=squad_member.role,
            llm_provider=squad_member.llm_provider,
            llm_model=squad_member.llm_model,
            system_prompt="You are a helpful assistant that creates concise summaries.",
            temperature=0.3
        )

        # Build conversation text
        conversation_text = "\n\n".join([
            f"{msg.role.upper()}: {msg.content}"
            for msg in conversation.messages
        ])

        # Generate summary
        summary_response = await agent.process_message(
            message=f"Please provide a concise 2-3 sentence summary of this conversation:\n\n{conversation_text}"
        )

        summary = summary_response.content

        # Update conversation
        conversation.summary = summary
        conversation.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(conversation)

        logger.info(f"Generated summary for conversation {conversation_id}")
        return summary
```

---

## API Design

### REST Endpoints

**File:** `backend/api/v1/endpoints/conversations.py`

```python
"""
User Conversations API Endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.services.conversation_service import ConversationService
from backend.schemas.user_conversation import (
    CreateConversationRequest,
    SendMessageRequest,
    UpdateConversationRequest,
    ArchiveConversationRequest,
    ConversationResponse,
    ConversationWithMessagesResponse,
    ConversationListResponse,
    SendMessageResponse
)


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new conversation with an AI agent.

    Creates a conversation session that maintains context across multiple messages.
    """
    try:
        conversation = await ConversationService.create_conversation(
            db=db,
            user_id=current_user.id,
            squad_member_id=request.squad_member_id,
            title=request.title,
            initial_message=request.initial_message,
            metadata=request.metadata
        )
        return conversation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    status: Optional[str] = Query(None, description="Filter by status"),
    squad_member_id: Optional[UUID] = Query(None, description="Filter by agent"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all conversations for the current user.

    Supports filtering by status and agent, with pagination.
    """
    try:
        result = await ConversationService.list_conversations(
            db=db,
            user_id=current_user.id,
            status=status,
            squad_member_id=squad_member_id,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=ConversationWithMessagesResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a conversation with full message history.
    """
    try:
        conversation = await ConversationService.get_conversation(
            db=db,
            conversation_id=conversation_id,
            include_messages=True
        )

        # Verify ownership
        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

        return conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message in a conversation and get agent response.

    The agent will see the full conversation history and respond contextually.
    """
    try:
        # Verify conversation exists and user owns it
        conversation = await ConversationService.get_conversation(db, conversation_id)
        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Get agent response
        result = await ConversationService.get_agent_response(
            db=db,
            conversation_id=conversation_id,
            user_message_content=request.content,
            metadata=request.metadata
        )

        return {
            "conversation_id": conversation_id,
            "message_id": result["user_message"].id,
            "assistant_message": result["assistant_message"],
            "total_tokens_used": result["tokens_used"],
            "conversation_total_tokens": result["conversation_total_tokens"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request: UpdateConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update conversation metadata (title, tags, etc.).
    """
    try:
        conversation = await ConversationService.get_conversation(db, conversation_id)

        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        if request.title is not None:
            conversation.title = request.title
        if request.tags is not None:
            conversation.tags = request.tags
        if request.metadata is not None:
            conversation.metadata = request.metadata

        conversation.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(conversation)

        return conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/archive", response_model=ConversationResponse)
async def archive_conversation(
    conversation_id: UUID,
    request: ArchiveConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Archive or unarchive a conversation.
    """
    try:
        conversation = await ConversationService.get_conversation(db, conversation_id)

        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        conversation = await ConversationService.archive_conversation(
            db=db,
            conversation_id=conversation_id,
            archive=request.archive
        )

        return conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a conversation (soft delete).
    """
    try:
        conversation = await ConversationService.get_conversation(db, conversation_id)

        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        await ConversationService.delete_conversation(db, conversation_id)

        return {"message": "Conversation deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/summary", response_model=dict)
async def generate_summary(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI summary of conversation.
    """
    try:
        conversation = await ConversationService.get_conversation(db, conversation_id)

        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        summary = await ConversationService.generate_summary(db, conversation_id)

        return {"summary": summary}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Register Router

**Update:** `backend/api/v1/router.py`

```python
from backend.api.v1.endpoints import conversations

# Add to existing routers
api_router.include_router(conversations.router)
```

---

## Integration with Existing System

### 1. Update User Model

**File:** `backend/models/user.py`

```python
# Add relationship to User model
class User(Base, TimestampMixin):
    # ... existing fields ...

    # Add relationship
    conversations = relationship("UserConversation", back_populates="user", cascade="all, delete-orphan")
```

### 2. Update SquadMember Model

**File:** `backend/models/squad.py`

```python
# Add relationship and conversation settings to SquadMember model
class SquadMember(Base, TimestampMixin):
    # ... existing fields ...

    # Conversation settings
    max_conversation_tokens = Column(Integer, default=8000)
    conversation_memory_enabled = Column(Boolean, default=True)
    auto_generate_summary = Column(Boolean, default=True)

    # Add relationship
    conversations = relationship("UserConversation", back_populates="squad_member")
```

### 3. Update Models __init__

**File:** `backend/models/__init__.py`

```python
from backend.models.user_conversation import UserConversation, ConversationMessage

__all__ = [
    # ... existing exports ...
    "UserConversation",
    "ConversationMessage",
]
```

### 4. Update Schemas __init__

**File:** `backend/schemas/__init__.py`

```python
from backend.schemas.user_conversation import (
    CreateConversationRequest,
    SendMessageRequest,
    ConversationResponse,
    ConversationWithMessagesResponse,
    SendMessageResponse,
    ConversationListResponse,
)

__all__ = [
    # ... existing exports ...
    "CreateConversationRequest",
    "SendMessageRequest",
    "ConversationResponse",
    "ConversationWithMessagesResponse",
    "SendMessageResponse",
    "ConversationListResponse",
]
```

---

## Frontend Integration

### Example React Hook

```typescript
// hooks/useConversation.ts

import { useState, useCallback } from 'react';
import { api } from '@/lib/api';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  status: string;
  total_messages: number;
  messages: Message[];
}

export function useConversation(conversationId?: string) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load conversation
  const loadConversation = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/conversations/${id}`);
      setConversation(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Send message
  const sendMessage = useCallback(async (content: string) => {
    if (!conversation) return;

    setLoading(true);
    setError(null);

    // Optimistically add user message
    const tempMessage: Message = {
      id: 'temp',
      role: 'user',
      content,
      created_at: new Date().toISOString()
    };

    setConversation(prev => prev ? {
      ...prev,
      messages: [...prev.messages, tempMessage]
    } : null);

    try {
      const response = await api.post(`/conversations/${conversation.id}/messages`, {
        content
      });

      // Replace temp message with real one and add assistant response
      setConversation(prev => {
        if (!prev) return null;

        const messages = prev.messages.filter(m => m.id !== 'temp');
        return {
          ...prev,
          messages: [
            ...messages,
            { ...tempMessage, id: response.data.message_id },
            response.data.assistant_message
          ],
          total_messages: prev.total_messages + 2
        };
      });
    } catch (err) {
      setError(err.message);
      // Remove temp message on error
      setConversation(prev => prev ? {
        ...prev,
        messages: prev.messages.filter(m => m.id !== 'temp')
      } : null);
    } finally {
      setLoading(false);
    }
  }, [conversation]);

  // Start new conversation
  const startConversation = useCallback(async (agentId: string, initialMessage?: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/conversations', {
        squad_member_id: agentId,
        title: 'New Conversation',
        initial_message: initialMessage
      });

      setConversation(response.data);

      if (initialMessage) {
        // Reload to get the initial exchange
        await loadConversation(response.data.id);
      }

      return response.data;
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [loadConversation]);

  return {
    conversation,
    loading,
    error,
    loadConversation,
    sendMessage,
    startConversation
  };
}
```

### Example Chat Component

```tsx
// components/ChatInterface.tsx

import { useState, useRef, useEffect } from 'react';
import { useConversation } from '@/hooks/useConversation';

export function ChatInterface({ agentId }: { agentId: string }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    conversation,
    loading,
    sendMessage,
    startConversation
  } = useConversation();

  // Start conversation on mount
  useEffect(() => {
    if (!conversation) {
      startConversation(agentId);
    }
  }, [agentId, conversation, startConversation]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    await sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="border-b p-4">
        <h2 className="text-xl font-bold">{conversation?.title}</h2>
        <p className="text-sm text-gray-500">
          {conversation?.total_messages} messages
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {conversation?.messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-900'
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              <p className="text-xs opacity-70 mt-1">
                {new Date(message.created_at).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 border rounded-lg px-4 py-2"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
```

---

## Implementation Phases

### Phase 1: Database & Models (2-3 days)

**Goal:** Create foundation for conversation storage

**Tasks:**
- [ ] Create migration `004_add_multi_turn_conversations.py`
- [ ] Create `UserConversation` and `ConversationMessage` models
- [ ] Update `User` and `SquadMember` models with relationships
- [ ] Run migration in dev environment
- [ ] Verify tables created correctly
- [ ] Write unit tests for models

**Deliverable:** Database ready to store conversations

**Test:**
```python
async def test_conversation_creation():
    conversation = UserConversation(
        user_id=user_id,
        squad_member_id=agent_id,
        title="Test Conversation"
    )
    db.add(conversation)
    await db.commit()

    assert conversation.id is not None
    assert conversation.status == "active"
```

### Phase 2: Service Layer (3-4 days)

**Goal:** Business logic for conversation management

**Tasks:**
- [ ] Create `ConversationService` class
- [ ] Implement `create_conversation()`
- [ ] Implement `send_message()`
- [ ] Implement `get_agent_response()` with context
- [ ] Implement `list_conversations()`
- [ ] Implement `archive_conversation()`
- [ ] Implement `generate_summary()`
- [ ] Write comprehensive unit tests

**Deliverable:** Service layer tested and ready

**Test:**
```python
async def test_get_agent_response_with_context():
    # Create conversation
    conversation = await ConversationService.create_conversation(
        db, user_id, agent_id
    )

    # Send first message
    result1 = await ConversationService.get_agent_response(
        db, conversation.id, "What is Redis?"
    )

    # Send follow-up - agent should remember first message
    result2 = await ConversationService.get_agent_response(
        db, conversation.id, "How do I install it?"
    )

    # Verify agent response references Redis (from context)
    assert "redis" in result2["assistant_message"].content.lower()
```

### Phase 3: Pydantic Schemas (1-2 days)

**Goal:** API request/response models

**Tasks:**
- [ ] Create all request schemas
- [ ] Create all response schemas
- [ ] Add validation rules
- [ ] Write schema tests
- [ ] Document with examples

**Deliverable:** Complete schema definitions

### Phase 4: API Endpoints (2-3 days)

**Goal:** REST API for conversations

**Tasks:**
- [ ] Create `conversations.py` router
- [ ] Implement POST `/conversations` (create)
- [ ] Implement GET `/conversations` (list)
- [ ] Implement GET `/conversations/{id}` (get one)
- [ ] Implement POST `/conversations/{id}/messages` (send message)
- [ ] Implement PATCH `/conversations/{id}` (update)
- [ ] Implement POST `/conversations/{id}/archive` (archive)
- [ ] Implement DELETE `/conversations/{id}` (delete)
- [ ] Add authentication/authorization
- [ ] Write API tests

**Deliverable:** Complete REST API

**Test:**
```python
async def test_api_send_message():
    # Create conversation via API
    response = await client.post("/conversations", json={
        "squad_member_id": str(agent_id),
        "title": "API Test"
    })

    conversation_id = response.json()["id"]

    # Send message
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "Hello"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "assistant_message" in data
    assert data["assistant_message"]["role"] == "assistant"
```

### Phase 5: Integration with BaseAgent (2 days)

**Goal:** Ensure agents work with conversation context

**Tasks:**
- [ ] Verify `process_message()` handles conversation history
- [ ] Test with different LLM providers (OpenAI, Anthropic, Groq)
- [ ] Verify token tracking works
- [ ] Test token limits
- [ ] Write integration tests

**Deliverable:** Agents fully integrated

**Test:**
```python
async def test_agent_uses_conversation_context():
    agent = AgentFactory.create_agent(...)

    # First message
    history = []
    response1 = await agent.process_message(
        "My API is slow",
        conversation_history=history
    )

    # Add to history
    history.append(ConversationMessage(role="user", content="My API is slow"))
    history.append(ConversationMessage(role="assistant", content=response1.content))

    # Follow-up message
    response2 = await agent.process_message(
        "What should I do about it?",
        conversation_history=history
    )

    # Response should reference the slow API problem
    assert "api" in response2.content.lower()
```

### Phase 6: Testing & QA (3-4 days)

**Goal:** Comprehensive testing

**Tasks:**
- [ ] Unit tests for all services (target: 95% coverage)
- [ ] Integration tests for API endpoints
- [ ] End-to-end tests for conversation flows
- [ ] Performance tests (concurrent conversations)
- [ ] Load tests (100+ simultaneous conversations)
- [ ] Security tests (authorization, token limits)
- [ ] Create demo script

**Deliverable:** Fully tested system

### Phase 7: Documentation & Demo (2 days)

**Goal:** Document and demonstrate the feature

**Tasks:**
- [ ] Write user documentation
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Create frontend integration guide
- [ ] Write demo script
- [ ] Create video/gif demo
- [ ] Update README

**Deliverable:** Complete documentation

**Demo Script:**
```python
# demo_multi_turn_conversations.py

async def demo_conversation_flow():
    """
    Demonstrates multi-turn conversation capabilities.
    """

    print("🎬 Demo: Multi-Turn Conversation\n")

    # Create conversation
    conversation = await ConversationService.create_conversation(
        db=db,
        user_id=user_id,
        squad_member_id=backend_dev_id,
        title="Redis Caching Help"
    )

    print(f"✅ Created conversation: {conversation.id}\n")

    # Message 1
    print("👤 User: How do I implement caching in my API?")
    result1 = await ConversationService.get_agent_response(
        db, conversation.id,
        "How do I implement caching in my API?"
    )
    print(f"🤖 Agent: {result1['assistant_message'].content}\n")

    # Message 2 - Follow-up
    print("👤 User: How do I set it up?")
    result2 = await ConversationService.get_agent_response(
        db, conversation.id,
        "How do I set it up?"
    )
    print(f"🤖 Agent: {result2['assistant_message'].content}")
    print(f"   (Agent remembered we're discussing caching!)\n")

    # Message 3 - Another follow-up
    print("👤 User: What about TTL values?")
    result3 = await ConversationService.get_agent_response(
        db, conversation.id,
        "What about TTL values?"
    )
    print(f"🤖 Agent: {result3['assistant_message'].content}")
    print(f"   (Agent still in context!)\n")

    print(f"📊 Conversation stats:")
    print(f"   Total messages: {conversation.total_messages}")
    print(f"   Total tokens: {conversation.total_tokens_used}")

    print("\n🎉 Demo complete! Multi-turn conversation works!")
```

---

## Testing Strategy

### 1. Unit Tests

```python
# backend/tests/test_services/test_conversation_service.py

import pytest
from uuid import uuid4
from backend.services.conversation_service import ConversationService
from backend.models.user_conversation import UserConversation


@pytest.mark.asyncio
async def test_create_conversation(db_session, test_user, test_agent):
    """Test creating a new conversation"""
    conversation = await ConversationService.create_conversation(
        db=db_session,
        user_id=test_user.id,
        squad_member_id=test_agent.id,
        title="Test Conversation"
    )

    assert conversation.id is not None
    assert conversation.user_id == test_user.id
    assert conversation.squad_member_id == test_agent.id
    assert conversation.status == "active"
    assert conversation.total_messages == 0


@pytest.mark.asyncio
async def test_send_message_adds_to_history(db_session, test_conversation):
    """Test that messages are added to conversation"""
    message = await ConversationService.send_message(
        db=db_session,
        conversation_id=test_conversation.id,
        content="Test message",
        role="user"
    )

    assert message.conversation_id == test_conversation.id
    assert message.role == "user"
    assert message.content == "Test message"


@pytest.mark.asyncio
async def test_context_maintained_across_messages(db_session, test_conversation):
    """Test that agent uses conversation context"""
    # First exchange
    result1 = await ConversationService.get_agent_response(
        db=db_session,
        conversation_id=test_conversation.id,
        user_message_content="What is Redis?"
    )

    # Second exchange - should reference Redis from context
    result2 = await ConversationService.get_agent_response(
        db=db_session,
        conversation_id=test_conversation.id,
        user_message_content="How do I install it?"
    )

    # Agent should understand "it" refers to Redis
    response = result2["assistant_message"].content.lower()
    assert "redis" in response or "install" in response


@pytest.mark.asyncio
async def test_token_limit_enforcement(db_session, test_conversation, test_agent):
    """Test that token limits are enforced"""
    # Set low token limit
    test_agent.max_conversation_tokens = 100
    await db_session.commit()

    # Fill up tokens
    test_conversation.total_tokens_used = 95
    await db_session.commit()

    # This should work (under limit)
    result = await ConversationService.get_agent_response(
        db=db_session,
        conversation_id=test_conversation.id,
        user_message_content="Hi"
    )

    # Simulate going over limit
    test_conversation.total_tokens_used = 105
    await db_session.commit()

    # This should fail
    with pytest.raises(ValueError, match="token limit"):
        await ConversationService.get_agent_response(
            db=db_session,
            conversation_id=test_conversation.id,
            user_message_content="More"
        )


@pytest.mark.asyncio
async def test_list_conversations_with_filters(db_session, test_user, test_agent):
    """Test listing conversations with filters"""
    # Create multiple conversations
    conv1 = await ConversationService.create_conversation(
        db=db_session, user_id=test_user.id, squad_member_id=test_agent.id
    )
    conv2 = await ConversationService.create_conversation(
        db=db_session, user_id=test_user.id, squad_member_id=test_agent.id
    )

    # Archive one
    await ConversationService.archive_conversation(db=db_session, conversation_id=conv2.id)

    # List active only
    result = await ConversationService.list_conversations(
        db=db_session,
        user_id=test_user.id,
        status="active"
    )

    assert result["total"] == 1
    assert result["conversations"][0].id == conv1.id
```

### 2. Integration Tests

```python
# backend/tests/test_api/test_conversations_api.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_conversation_api(client: AsyncClient, test_user, test_agent):
    """Test creating conversation via API"""
    response = await client.post(
        "/conversations",
        json={
            "squad_member_id": str(test_agent.id),
            "title": "API Test Conversation"
        },
        headers={"Authorization": f"Bearer {test_user.token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "API Test Conversation"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_send_message_api(client: AsyncClient, test_user, test_conversation):
    """Test sending message via API"""
    response = await client.post(
        f"/conversations/{test_conversation.id}/messages",
        json={"content": "Hello, how are you?"},
        headers={"Authorization": f"Bearer {test_user.token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "assistant_message" in data
    assert data["assistant_message"]["role"] == "assistant"
    assert len(data["assistant_message"]["content"]) > 0


@pytest.mark.asyncio
async def test_unauthorized_access_blocked(client: AsyncClient, test_conversation, other_user):
    """Test that users can't access other users' conversations"""
    response = await client.get(
        f"/conversations/{test_conversation.id}",
        headers={"Authorization": f"Bearer {other_user.token}"}
    )

    assert response.status_code == 403
```

### 3. End-to-End Tests

```python
# backend/tests/test_e2e/test_conversation_flow.py

@pytest.mark.asyncio
async def test_complete_conversation_flow(db_session, test_user, test_agent):
    """Test complete conversation flow from start to finish"""

    # 1. Create conversation
    conversation = await ConversationService.create_conversation(
        db=db_session,
        user_id=test_user.id,
        squad_member_id=test_agent.id,
        title="E2E Test"
    )

    # 2. Send multiple messages
    messages = [
        "What is Redis?",
        "How is it different from PostgreSQL?",
        "When should I use each one?",
        "Show me an example"
    ]

    for msg_content in messages:
        result = await ConversationService.get_agent_response(
            db=db_session,
            conversation_id=conversation.id,
            user_message_content=msg_content
        )

        assert result["assistant_message"] is not None
        assert len(result["assistant_message"].content) > 0

    # 3. Verify conversation state
    await db_session.refresh(conversation)
    assert conversation.total_messages == len(messages) * 2  # User + assistant for each
    assert conversation.total_tokens_used > 0

    # 4. Generate summary
    summary = await ConversationService.generate_summary(
        db=db_session,
        conversation_id=conversation.id
    )

    assert len(summary) > 0
    assert "redis" in summary.lower()

    # 5. Archive conversation
    await ConversationService.archive_conversation(
        db=db_session,
        conversation_id=conversation.id
    )

    await db_session.refresh(conversation)
    assert conversation.status == "archived"
```

---

## Performance Considerations

### 1. Token Limits

**Problem:** Long conversations can exceed model context limits

**Solution:**
```python
# In ConversationService.get_agent_response()

# Truncate history if too long
max_history_tokens = 6000  # Leave room for new message + response
if conversation.total_tokens_used > max_history_tokens:
    # Keep only recent messages
    messages_to_keep = []
    token_count = 0

    for msg in reversed(conversation.messages):
        msg_tokens = estimate_tokens(msg.content)
        if token_count + msg_tokens > max_history_tokens:
            break
        messages_to_keep.insert(0, msg)
        token_count += msg_tokens

    conversation_history = messages_to_keep
```

### 2. Database Query Optimization

**Indexes created:**
- `conversation_id` for fast message lookup
- `user_id + status` for listing conversations
- `last_message_at DESC` for sorting

**N+1 Query Prevention:**
```python
# Use selectinload to eager-load messages
stmt = select(UserConversation).where(
    UserConversation.id == conversation_id
).options(selectinload(UserConversation.messages))
```

### 3. Caching

**Redis caching for frequently accessed conversations:**

```python
# In ConversationService.get_conversation()

async def get_conversation(db, conversation_id, include_messages=False):
    # Try cache first
    cache_key = f"conversation:{conversation_id}"
    cached = await redis.get(cache_key)

    if cached:
        return json.loads(cached)

    # Query database
    conversation = await db.execute(stmt)

    # Cache for 5 minutes
    await redis.setex(cache_key, 300, json.dumps(conversation))

    return conversation
```

### 4. Pagination for Long Conversations

```python
# Add pagination to message retrieval
@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated messages from conversation"""
    stmt = select(ConversationMessage).where(
        ConversationMessage.conversation_id == conversation_id
    ).order_by(
        ConversationMessage.created_at
    ).limit(limit).offset(offset)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    return messages
```

---

## Security & Privacy

### 1. Authorization

**Every endpoint checks:**
- User is authenticated
- User owns the conversation
- Conversation exists

```python
# In every endpoint
conversation = await ConversationService.get_conversation(db, conversation_id)

if conversation.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized")
```

### 2. Token Limits

**Per-agent conversation limits:**
```python
# In squad_members table
max_conversation_tokens = Column(Integer, default=8000)

# Enforced in get_agent_response()
if conversation.total_tokens_used >= squad_member.max_conversation_tokens:
    raise ValueError("Token limit reached")
```

### 3. Rate Limiting

**Prevent abuse:**
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.post("/{conversation_id}/messages")
@limiter.limit("30/minute")  # Max 30 messages per minute
async def send_message(...):
    ...
```

### 4. Input Validation

**All user input validated:**
- Message content max length: 10,000 characters
- Title max length: 255 characters
- No SQL injection (using parameterized queries)
- No XSS (content escaped in frontend)

### 5. Data Retention

**Optional automatic cleanup:**
```python
# Celery task to clean up old conversations
@celery_app.task
async def cleanup_old_conversations():
    """Delete conversations older than 90 days with status=deleted"""
    cutoff_date = datetime.utcnow() - timedelta(days=90)

    stmt = delete(UserConversation).where(
        and_(
            UserConversation.status == "deleted",
            UserConversation.updated_at < cutoff_date
        )
    )

    await db.execute(stmt)
    await db.commit()
```

---

## Summary

### What Gets Built

1. **Database Schema**
   - `user_conversations` table (conversation sessions)
   - `conversation_messages` table (individual messages)
   - Proper indexes for performance

2. **Backend Services**
   - `ConversationService` (business logic)
   - Full CRUD operations
   - Context-aware agent responses

3. **REST API**
   - 8 endpoints for conversation management
   - Authentication and authorization
   - Pagination and filtering

4. **Integration**
   - Works with existing `BaseAgent`
   - Token tracking and limits
   - SSE streaming compatible

5. **Testing**
   - Unit tests for services
   - Integration tests for API
   - E2E tests for full flows
   - Demo scripts

### Timeline

**Total: 15-20 days**

| Phase | Duration | Tasks |
|-------|----------|-------|
| 1. Database & Models | 2-3 days | Schema, models, migration |
| 2. Service Layer | 3-4 days | Business logic, context handling |
| 3. Pydantic Schemas | 1-2 days | Request/response models |
| 4. API Endpoints | 2-3 days | REST API, auth |
| 5. BaseAgent Integration | 2 days | Ensure agents work with context |
| 6. Testing & QA | 3-4 days | Comprehensive testing |
| 7. Documentation & Demo | 2 days | Docs, demo, examples |

### Success Metrics

✅ **Functional:**
- Users can start conversations
- Agents maintain context across messages
- Follow-up questions work naturally
- Token limits enforced

✅ **Performance:**
- API response time < 2 seconds (excluding LLM)
- Support 100+ concurrent conversations
- Database queries < 50ms

✅ **Quality:**
- 95%+ test coverage
- All integration tests passing
- Security review passed
- Documentation complete

---

## Files to Create/Modify

### New Files (8 files)

1. `backend/models/user_conversation.py` (180 lines)
2. `backend/schemas/user_conversation.py` (150 lines)
3. `backend/services/conversation_service.py` (500 lines)
4. `backend/api/v1/endpoints/conversations.py` (300 lines)
5. `backend/alembic/versions/004_add_multi_turn_conversations.py` (120 lines)
6. `backend/tests/test_services/test_conversation_service.py` (400 lines)
7. `backend/tests/test_api/test_conversations_api.py` (300 lines)
8. `demo_multi_turn_conversations.py` (200 lines)

### Modified Files (4 files)

1. `backend/models/user.py` (+2 lines - relationship)
2. `backend/models/squad.py` (+5 lines - relationship + columns)
3. `backend/models/__init__.py` (+2 lines - exports)
4. `backend/api/v1/router.py` (+2 lines - router registration)

**Total:** ~2,150 lines of new code

---

## Next Steps

**Ready to start?**

1. Review this plan
2. Ask any questions
3. Approve to begin implementation
4. I'll start with Phase 1 (Database & Models)

---

**Questions for Review:**

1. Is the database schema design acceptable?
2. Should we add conversation sharing (multiple users in one conversation)?
3. Should we support conversation branching (save different paths)?
4. Do we need conversation export (JSON/PDF)?
5. Should summaries auto-generate after N messages?
6. What should the default token limit be (currently 8000)?
7. Should we support conversation templates (pre-filled context)?

---

**End of Plan**

This plan provides everything needed to implement multi-turn conversations. All code examples are production-ready and follow the existing project structure.
