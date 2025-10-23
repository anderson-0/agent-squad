# Agent Interaction Patterns - Hierarchical Routing & Escalation Plan

**Status**: Planning Phase
**Created**: 2025-10-22
**Purpose**: Design hierarchical agent communication with automatic timeout/retry/escalation

---

## Executive Summary

This document outlines a comprehensive plan to implement intelligent agent-to-agent communication patterns with:

- **Hierarchical Routing**: Agents know who to ask for specific types of help
- **Acknowledgment Protocol**: "Please wait" mechanism for async processing
- **Timeout & Retry**: Automatic follow-ups when agents don't respond
- **Escalation**: Route to higher authority (PM) when help isn't available
- **Default Behavior**: Built into all agents automatically

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Agent Hierarchy Design](#agent-hierarchy-design)
3. [Conversation State Machine](#conversation-state-machine)
4. [Message Flow Patterns](#message-flow-patterns)
5. [Configuration System](#configuration-system)
6. [Database Schema Changes](#database-schema-changes)
7. [Implementation Architecture](#implementation-architecture)
8. [Code Changes Required](#code-changes-required)
9. [Testing Strategy](#testing-strategy)
10. [Rollout Plan](#rollout-plan)

---

## Problem Statement

### Current Behavior
- Agents send messages directly to any other agent
- No standardized acknowledgment of questions
- No timeout handling for unanswered questions
- No escalation when help isn't available
- No defined hierarchy of who should help whom

### Desired Behavior

**Scenario Example**:
1. Backend Developer has architecture question
2. Backend sends message to Tech Lead
3. Tech Lead immediately responds: "Let me think about this, please wait..."
4. Backend waits for configurable timeout (e.g., 5 minutes)
5. **If Tech Lead responds**: Conversation continues normally
6. **If timeout expires**: Backend sends: "Are you still there?"
7. **If still no response**: Backend escalates to Project Manager
8. **If Tech Lead can't help**: Tech Lead routes question to Solution Architect

### Benefits
- **Predictable communication**: Agents know where to get help
- **No lost messages**: Timeout/retry ensures questions get answered
- **Graceful escalation**: Questions always reach someone who can help
- **Better UX**: "Please wait" messages provide feedback
- **Realistic collaboration**: Mimics real team dynamics

---

## Agent Hierarchy Design

### 1. Agent Roles & Responsibilities

```
┌─────────────────────────────────────────────────────┐
│              Project Manager (PM)                    │
│         • Final escalation point                     │
│         • Coordinates all agents                     │
│         • Makes project decisions                    │
└─────────────────────────────────────────────────────┘
                        ▲
                        │ escalation
        ┌───────────────┴───────────────┐
        │                               │
┌───────────────────┐         ┌────────────────────┐
│ Solution Architect │         │    Tech Lead       │
│ • System design    │         │ • Tech decisions   │
│ • Architecture     │◄────────┤ • Code standards   │
└───────────────────┘         └────────────────────┘
                                       ▲
                                       │ technical questions
        ┌──────────────────────────────┼──────────────────────────┐
        │                              │                          │
┌───────────────┐         ┌────────────────────┐      ┌──────────────────┐
│ Backend Dev   │         │  Frontend Dev      │      │   DevOps Eng     │
└───────────────┘         └────────────────────┘      └──────────────────┘
        ▲                          ▲                           ▲
        │                          │                           │
        │                   ┌──────────────┐                   │
        └───────────────────┤  QA Tester   │───────────────────┘
                            └──────────────┘
                            • Testing questions
                            • Bug reports
```

### 2. Help Routing Matrix

| Agent Role | Question Type | Route To (Priority Order) |
|-----------|--------------|---------------------------|
| **Backend Developer** | Implementation | 1. Tech Lead → 2. Solution Architect → 3. PM |
| | Architecture | 1. Tech Lead → 2. Solution Architect → 3. PM |
| | Database | 1. Tech Lead → 2. DevOps → 3. PM |
| | API Design | 1. Tech Lead → 2. Solution Architect → 3. PM |
| **Frontend Developer** | Implementation | 1. Tech Lead → 2. Solution Architect → 3. PM |
| | UX/Design | 1. Designer → 2. Tech Lead → 3. PM |
| | API Integration | 1. Backend Dev → 2. Tech Lead → 3. PM |
| | State Management | 1. Tech Lead → 2. Solution Architect → 3. PM |
| **QA Tester** | Test Strategy | 1. Tech Lead → 2. PM |
| | Bug Report | 1. Relevant Dev → 2. Tech Lead → 3. PM |
| | Environment Issues | 1. DevOps → 2. Tech Lead → 3. PM |
| **DevOps Engineer** | Infrastructure | 1. Solution Architect → 2. PM |
| | Deployment | 1. Tech Lead → 2. PM |
| **Tech Lead** | Architecture | 1. Solution Architect → 2. PM |
| | Project Scope | 1. PM |
| **Solution Architect** | Business Requirements | 1. PM |
| | Resource Allocation | 1. PM |
| **Designer** | Design Direction | 1. PM |
| | User Research | 1. PM |
| **AI Engineer** | ML Architecture | 1. Solution Architect → 2. PM |
| | Data Pipeline | 1. Backend Dev → 2. Tech Lead → 3. PM |

### 3. Routing Rules

```python
AGENT_ROUTING_HIERARCHY = {
    'backend_developer': {
        'implementation': ['tech_lead', 'solution_architect', 'project_manager'],
        'architecture': ['tech_lead', 'solution_architect', 'project_manager'],
        'database': ['tech_lead', 'devops_engineer', 'project_manager'],
        'api_design': ['tech_lead', 'solution_architect', 'project_manager'],
        'default': ['tech_lead', 'project_manager']
    },
    'frontend_developer': {
        'implementation': ['tech_lead', 'solution_architect', 'project_manager'],
        'design': ['designer', 'tech_lead', 'project_manager'],
        'api_integration': ['backend_developer', 'tech_lead', 'project_manager'],
        'state_management': ['tech_lead', 'solution_architect', 'project_manager'],
        'default': ['tech_lead', 'project_manager']
    },
    'qa_tester': {
        'test_strategy': ['tech_lead', 'project_manager'],
        'bug_report': ['relevant_developer', 'tech_lead', 'project_manager'],
        'environment': ['devops_engineer', 'tech_lead', 'project_manager'],
        'default': ['tech_lead', 'project_manager']
    },
    'devops_engineer': {
        'infrastructure': ['solution_architect', 'project_manager'],
        'deployment': ['tech_lead', 'project_manager'],
        'default': ['tech_lead', 'project_manager']
    },
    'tech_lead': {
        'architecture': ['solution_architect', 'project_manager'],
        'project_scope': ['project_manager'],
        'default': ['project_manager']
    },
    'solution_architect': {
        'business_requirements': ['project_manager'],
        'resource_allocation': ['project_manager'],
        'default': ['project_manager']
    },
    'designer': {
        'design_direction': ['project_manager'],
        'user_research': ['project_manager'],
        'default': ['project_manager']
    },
    'ai_engineer': {
        'ml_architecture': ['solution_architect', 'project_manager'],
        'data_pipeline': ['backend_developer', 'tech_lead', 'project_manager'],
        'default': ['tech_lead', 'project_manager']
    }
}
```

---

## Conversation State Machine

### States

```
┌──────────────┐
│  INITIATED   │  Agent sends initial question
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   WAITING    │  Received "please wait" acknowledgment
└──────┬───────┘  Timer starts (timeout_duration)
       │
       ├──────────────► Response received ──────┐
       │                                        │
       ▼                                        ▼
┌──────────────┐                        ┌──────────────┐
│   TIMEOUT    │  No response            │   ANSWERED   │
└──────┬───────┘  after timeout          └──────────────┘
       │          (send follow-up)              (RESOLVED)
       │
       ▼
┌──────────────┐
│ FOLLOW_UP    │  Sent "are you still there?"
└──────┬───────┘  Timer starts (retry_timeout)
       │
       ├──────────────► Response received ──────┐
       │                                        │
       ▼                                        ▼
┌──────────────┐                        ┌──────────────┐
│  ESCALATING  │  Still no response      │   ANSWERED   │
└──────┬───────┘  (route to next level)  └──────────────┘
       │                                       (RESOLVED)
       ▼
┌──────────────┐
│  ESCALATED   │  Question sent to higher authority
└──────────────┘  (returns to INITIATED state with new recipient)
```

### State Transitions

```python
class ConversationState(Enum):
    INITIATED = "initiated"           # Question sent
    WAITING = "waiting"               # Acknowledged, waiting for answer
    TIMEOUT = "timeout"               # No answer after timeout
    FOLLOW_UP = "follow_up"           # Sent "are you still there?"
    ESCALATING = "escalating"         # Still no answer, escalating
    ESCALATED = "escalated"           # Question re-routed
    ANSWERED = "answered"             # Got response, resolved
    CANCELLED = "cancelled"           # Asker cancelled the question
```

### Transition Triggers

| Current State | Trigger | Next State | Action |
|--------------|---------|------------|--------|
| INITIATED | Receive acknowledgment | WAITING | Start timeout timer |
| INITIATED | Receive answer | ANSWERED | Resolve conversation |
| WAITING | Timeout expires | TIMEOUT | Send follow-up |
| TIMEOUT | Send follow-up | FOLLOW_UP | Start retry timer |
| FOLLOW_UP | Receive answer | ANSWERED | Resolve conversation |
| FOLLOW_UP | Retry timeout expires | ESCALATING | Prepare escalation |
| ESCALATING | Route to next agent | ESCALATED | Send to higher authority |
| ESCALATED | New recipient acknowledges | WAITING | Start new timeout timer |

---

## Message Flow Patterns

### Pattern 1: Happy Path (Question Answered)

```
Backend Dev                Tech Lead                 System
    │                          │                       │
    ├─── "How do I cache?" ────>                      │
    │                          ├── Store conversation │
    │                          │   state: INITIATED   │
    │                          │                      │
    │<── "Let me think..." ────┤                      │
    │                          ├── Update state:      │
    │                          │   WAITING            │
    │                          ├── Start timer: 5min  │
    │                          │                      │
    │                          │ [thinking...]        │
    │                          │                      │
    │<── "Use Redis with..." ──┤                      │
    │                          ├── Update state:      │
    │                          │   ANSWERED           │
    │                          ├── Clear timer        │
    ▼                          ▼                      ▼
```

### Pattern 2: Timeout with Follow-up (Then Answered)

```
Backend Dev                Tech Lead                 System
    │                          │                       │
    ├─── "How do I cache?" ────>                      │
    │                          ├── Store state:       │
    │                          │   INITIATED          │
    │                          │                      │
    │<── "Let me think..." ────┤                      │
    │                          ├── Update state:      │
    │                          │   WAITING            │
    │                          ├── Start timer: 5min  │
    │                          │                      │
    │                    [5 minutes pass]             │
    │                          │                      │
    │                          │<─── TIMEOUT event ───┤
    │                          ├── Update state:      │
    │                          │   TIMEOUT            │
    │                          │                      │
    ├─ "Are you still there?"─>                      │
    │                          ├── Update state:      │
    │                          │   FOLLOW_UP          │
    │                          ├── Start timer: 2min  │
    │                          │                      │
    │<── "Sorry! Use Redis..." ┤                      │
    │                          ├── Update state:      │
    │                          │   ANSWERED           │
    ▼                          ▼                      ▼
```

### Pattern 3: Full Escalation

```
Backend Dev      Tech Lead      Solution Architect      PM
    │                │                  │                │
    ├─ "How cache?"─>│                  │                │
    │                │                  │                │
    │<─"Wait..."─────┤                  │                │
    │         [timeout: 5min]           │                │
    │                │                  │                │
    ├─"Still there?"─>                  │                │
    │         [timeout: 2min]           │                │
    │                │                  │                │
    │                X (no response)    │                │
    │                                   │                │
    ├─────────"How cache?"──────────────>                │
    │                                   │                │
    │                             [timeout: 5min]        │
    │                                   │                │
    │                                   X (no response)  │
    │                                                    │
    ├─────────────"Need help with caching"──────────────>
    │                                                    │
    │<──────"Let me assign another tech lead"───────────┤
    ▼                                                    ▼
```

### Pattern 4: Agent Can't Help (Routes to Expert)

```
Backend Dev          Tech Lead      Solution Architect
    │                    │                  │
    ├─ "How to design    │                  │
    │   microservices?"──>                  │
    │                    │                  │
    │<─ "Wait..."────────┤                  │
    │                    │ [analyzes]       │
    │                    │                  │
    │<─ "This is above my│                  │
    │    expertise. Let me                  │
    │    connect you with│                  │
    │    our architect"──┤                  │
    │                    │                  │
    │                    ├──"Backend needs  │
    │                    │   microservices  │
    │                    │   design help"──>│
    │                    │                  │
    │<─────────────────────"Let me help..."─┤
    ▼                    ▼                  ▼
```

---

## Configuration System

### 1. Timeout Configuration

```python
# backend/agents/configuration/interaction_config.py

from dataclasses import dataclass
from typing import Dict, List
from datetime import timedelta

@dataclass
class TimeoutConfig:
    """Timeout settings for agent interactions"""

    # Initial wait after "please wait" acknowledgment
    initial_timeout: timedelta = timedelta(minutes=5)

    # Time to wait after "are you still there?" follow-up
    retry_timeout: timedelta = timedelta(minutes=2)

    # Maximum number of escalation attempts before giving up
    max_escalation_levels: int = 3

    # Time to wait before considering a message "lost"
    message_delivery_timeout: timedelta = timedelta(seconds=30)

    # Enable/disable auto-escalation
    auto_escalation_enabled: bool = True


@dataclass
class MessageTemplates:
    """Default message templates for agent interactions"""

    # Acknowledgment when receiving a question
    acknowledgment: str = "I received your question. Let me think about this, please wait..."

    # Follow-up when no response
    follow_up: str = "Are you still there? I'm still waiting for your response."

    # Escalation notification to original asker
    escalation_notice: str = "I haven't received a response yet. I'm escalating this to {escalated_to}."

    # When agent can't help and routes to expert
    routing_notice: str = "This is outside my expertise. I'm connecting you with {expert_role} who can better assist."

    # Timeout notification to recipient who didn't respond
    timeout_notification: str = "You didn't respond to a question from {asker_role}. The question was escalated to {escalated_to}."


@dataclass
class InteractionConfig:
    """Complete configuration for agent interaction patterns"""

    timeouts: TimeoutConfig = TimeoutConfig()
    templates: MessageTemplates = MessageTemplates()
    routing_hierarchy: Dict[str, Dict[str, List[str]]] = None

    def __post_init__(self):
        if self.routing_hierarchy is None:
            self.routing_hierarchy = get_default_routing_hierarchy()


def get_default_routing_hierarchy() -> Dict[str, Dict[str, List[str]]]:
    """Returns the default agent routing hierarchy"""
    return {
        'backend_developer': {
            'implementation': ['tech_lead', 'solution_architect', 'project_manager'],
            'architecture': ['tech_lead', 'solution_architect', 'project_manager'],
            'database': ['tech_lead', 'devops_engineer', 'project_manager'],
            'api_design': ['tech_lead', 'solution_architect', 'project_manager'],
            'default': ['tech_lead', 'project_manager']
        },
        # ... (complete hierarchy from earlier)
    }
```

### 2. Environment Variables

```bash
# .env additions

# Agent Interaction Patterns
AGENT_INITIAL_TIMEOUT_MINUTES=5
AGENT_RETRY_TIMEOUT_MINUTES=2
AGENT_MAX_ESCALATION_LEVELS=3
AGENT_AUTO_ESCALATION_ENABLED=true
AGENT_MESSAGE_DELIVERY_TIMEOUT_SECONDS=30

# Enable/disable interaction patterns globally
ENABLE_HIERARCHICAL_ROUTING=true
ENABLE_AUTO_ACKNOWLEDGMENT=true
ENABLE_TIMEOUT_ESCALATION=true
```

### 3. Per-Agent Configuration Override

```python
# Allow agents to override default timeouts based on their role

ROLE_SPECIFIC_TIMEOUTS = {
    'project_manager': {
        'initial_timeout': timedelta(minutes=10),  # PM might be in meetings
        'retry_timeout': timedelta(minutes=5)
    },
    'solution_architect': {
        'initial_timeout': timedelta(minutes=15),  # Complex design work
        'retry_timeout': timedelta(minutes=5)
    },
    'backend_developer': {
        'initial_timeout': timedelta(minutes=5),
        'retry_timeout': timedelta(minutes=2)
    },
    # Default for all other roles
    'default': {
        'initial_timeout': timedelta(minutes=5),
        'retry_timeout': timedelta(minutes=2)
    }
}
```

---

## Database Schema Changes

### 1. New Table: `agent_conversations`

```sql
CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Conversation tracking
    initial_message_id UUID NOT NULL REFERENCES agent_messages(id),
    current_state VARCHAR(50) NOT NULL,  -- 'initiated', 'waiting', 'timeout', etc.

    -- Participants
    asker_id UUID NOT NULL REFERENCES agents(id),
    current_responder_id UUID NOT NULL REFERENCES agents(id),
    escalation_level INTEGER DEFAULT 0,

    -- Context
    question_type VARCHAR(100),  -- 'implementation', 'architecture', etc.
    task_execution_id UUID REFERENCES task_executions(id),

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    timeout_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB,

    CONSTRAINT fk_initial_message FOREIGN KEY (initial_message_id)
        REFERENCES agent_messages(id) ON DELETE CASCADE,
    CONSTRAINT fk_asker FOREIGN KEY (asker_id)
        REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT fk_responder FOREIGN KEY (current_responder_id)
        REFERENCES agents(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_conversations_state ON agent_conversations(current_state);
CREATE INDEX idx_conversations_asker ON agent_conversations(asker_id);
CREATE INDEX idx_conversations_responder ON agent_conversations(current_responder_id);
CREATE INDEX idx_conversations_timeout ON agent_conversations(timeout_at)
    WHERE current_state IN ('waiting', 'follow_up');
CREATE INDEX idx_conversations_task ON agent_conversations(task_execution_id);
```

### 2. New Table: `conversation_events`

```sql
CREATE TABLE conversation_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,

    -- Event details
    event_type VARCHAR(50) NOT NULL,  -- 'acknowledged', 'timeout', 'follow_up', 'escalated', 'answered'
    from_state VARCHAR(50),
    to_state VARCHAR(50) NOT NULL,

    -- Related message (if any)
    message_id UUID REFERENCES agent_messages(id),

    -- Agent who triggered this event
    triggered_by_agent_id UUID REFERENCES agents(id),

    -- Event data
    event_data JSONB,

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_conversation_events_conversation ON conversation_events(conversation_id);
CREATE INDEX idx_conversation_events_type ON conversation_events(event_type);
CREATE INDEX idx_conversation_events_created ON conversation_events(created_at);
```

### 3. Update `agent_messages` Table

```sql
-- Add columns to existing agent_messages table
ALTER TABLE agent_messages
    ADD COLUMN conversation_id UUID REFERENCES agent_conversations(id),
    ADD COLUMN is_acknowledgment BOOLEAN DEFAULT FALSE,
    ADD COLUMN is_follow_up BOOLEAN DEFAULT FALSE,
    ADD COLUMN is_escalation BOOLEAN DEFAULT FALSE,
    ADD COLUMN requires_acknowledgment BOOLEAN DEFAULT FALSE,
    ADD COLUMN parent_message_id UUID REFERENCES agent_messages(id);

-- Index for conversation threading
CREATE INDEX idx_messages_conversation ON agent_messages(conversation_id);
CREATE INDEX idx_messages_parent ON agent_messages(parent_message_id);
```

### 4. Migration Script

```python
# backend/alembic/versions/xxx_add_conversation_tracking.py

"""Add conversation tracking and escalation

Revision ID: xxx
Revises: yyy
Create Date: 2025-10-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create agent_conversations table
    op.create_table(
        'agent_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('initial_message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_state', sa.String(50), nullable=False),
        sa.Column('asker_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_responder_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('escalation_level', sa.Integer(), default=0),
        sa.Column('question_type', sa.String(100)),
        sa.Column('task_execution_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('acknowledged_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('timeout_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('metadata', postgresql.JSONB()),
        sa.ForeignKeyConstraint(['initial_message_id'], ['agent_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asker_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['current_responder_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_execution_id'], ['task_executions.id'])
    )

    # Create indexes
    op.create_index('idx_conversations_state', 'agent_conversations', ['current_state'])
    op.create_index('idx_conversations_asker', 'agent_conversations', ['asker_id'])
    op.create_index('idx_conversations_responder', 'agent_conversations', ['current_responder_id'])
    op.create_index('idx_conversations_task', 'agent_conversations', ['task_execution_id'])

    # Create conversation_events table
    op.create_table(
        'conversation_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('from_state', sa.String(50)),
        sa.Column('to_state', sa.String(50), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True)),
        sa.Column('triggered_by_agent_id', postgresql.UUID(as_uuid=True)),
        sa.Column('event_data', postgresql.JSONB()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['agent_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['agent_messages.id']),
        sa.ForeignKeyConstraint(['triggered_by_agent_id'], ['agents.id'])
    )

    # Create indexes
    op.create_index('idx_conversation_events_conversation', 'conversation_events', ['conversation_id'])
    op.create_index('idx_conversation_events_type', 'conversation_events', ['event_type'])
    op.create_index('idx_conversation_events_created', 'conversation_events', ['created_at'])

    # Update agent_messages table
    op.add_column('agent_messages', sa.Column('conversation_id', postgresql.UUID(as_uuid=True)))
    op.add_column('agent_messages', sa.Column('is_acknowledgment', sa.Boolean(), default=False))
    op.add_column('agent_messages', sa.Column('is_follow_up', sa.Boolean(), default=False))
    op.add_column('agent_messages', sa.Column('is_escalation', sa.Boolean(), default=False))
    op.add_column('agent_messages', sa.Column('requires_acknowledgment', sa.Boolean(), default=False))
    op.add_column('agent_messages', sa.Column('parent_message_id', postgresql.UUID(as_uuid=True)))

    op.create_foreign_key(
        'fk_messages_conversation',
        'agent_messages', 'agent_conversations',
        ['conversation_id'], ['id']
    )
    op.create_foreign_key(
        'fk_messages_parent',
        'agent_messages', 'agent_messages',
        ['parent_message_id'], ['id']
    )

    op.create_index('idx_messages_conversation', 'agent_messages', ['conversation_id'])
    op.create_index('idx_messages_parent', 'agent_messages', ['parent_message_id'])


def downgrade():
    op.drop_index('idx_messages_parent', 'agent_messages')
    op.drop_index('idx_messages_conversation', 'agent_messages')
    op.drop_constraint('fk_messages_parent', 'agent_messages', type_='foreignkey')
    op.drop_constraint('fk_messages_conversation', 'agent_messages', type_='foreignkey')
    op.drop_column('agent_messages', 'parent_message_id')
    op.drop_column('agent_messages', 'requires_acknowledgment')
    op.drop_column('agent_messages', 'is_escalation')
    op.drop_column('agent_messages', 'is_follow_up')
    op.drop_column('agent_messages', 'is_acknowledgment')
    op.drop_column('agent_messages', 'conversation_id')

    op.drop_index('idx_conversation_events_created', 'conversation_events')
    op.drop_index('idx_conversation_events_type', 'conversation_events')
    op.drop_index('idx_conversation_events_conversation', 'conversation_events')
    op.drop_table('conversation_events')

    op.drop_index('idx_conversations_task', 'agent_conversations')
    op.drop_index('idx_conversations_responder', 'agent_conversations')
    op.drop_index('idx_conversations_asker', 'agent_conversations')
    op.drop_index('idx_conversations_state', 'agent_conversations')
    op.drop_table('agent_conversations')
```

---

## Implementation Architecture

### 1. Core Components

```
backend/agents/interaction/
├── __init__.py
├── conversation_manager.py       # Main orchestrator
├── routing_engine.py             # Determines who to ask for help
├── timeout_handler.py            # Manages timeouts and escalations
├── acknowledgment_service.py     # Auto-sends "please wait" messages
├── escalation_service.py         # Handles routing to higher authority
└── models.py                     # Pydantic models for conversations
```

### 2. ConversationManager (Core Orchestrator)

```python
# backend/agents/interaction/conversation_manager.py

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.interaction.routing_engine import RoutingEngine
from backend.agents.interaction.timeout_handler import TimeoutHandler
from backend.agents.interaction.acknowledgment_service import AcknowledgmentService
from backend.agents.interaction.escalation_service import EscalationService
from backend.agents.interaction.models import (
    Conversation, ConversationState, ConversationEvent
)
from backend.agents.configuration.interaction_config import InteractionConfig


class ConversationManager:
    """
    Orchestrates agent-to-agent conversations with timeout/retry/escalation.

    This is the main entry point for all conversation management.
    """

    def __init__(
        self,
        db: AsyncSession,
        config: Optional[InteractionConfig] = None
    ):
        self.db = db
        self.config = config or InteractionConfig()

        # Initialize services
        self.routing = RoutingEngine(self.config.routing_hierarchy)
        self.timeout_handler = TimeoutHandler(db, self.config.timeouts)
        self.acknowledgment = AcknowledgmentService(db, self.config.templates)
        self.escalation = EscalationService(db, self.routing, self.config)


    async def initiate_question(
        self,
        asker_id: UUID,
        question_content: str,
        question_type: str,
        task_execution_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Agent asks a question. This automatically:
        1. Determines who should answer based on routing hierarchy
        2. Sends the question
        3. Creates conversation tracking
        4. Sets up timeout monitoring
        """
        # Determine who should answer this question
        responder_id = await self.routing.get_best_responder(
            asker_role=await self._get_agent_role(asker_id),
            question_type=question_type
        )

        # Send the question via message bus
        message = await self._send_message(
            sender_id=asker_id,
            recipient_id=responder_id,
            content=question_content,
            message_type='question',
            task_execution_id=task_execution_id,
            requires_acknowledgment=True
        )

        # Create conversation tracking
        conversation = await self._create_conversation(
            initial_message_id=message.id,
            asker_id=asker_id,
            responder_id=responder_id,
            question_type=question_type,
            task_execution_id=task_execution_id,
            metadata=metadata
        )

        # Schedule timeout monitoring
        await self.timeout_handler.schedule_timeout_check(
            conversation_id=conversation.id,
            timeout_at=datetime.utcnow() + self.config.timeouts.initial_timeout
        )

        return conversation


    async def handle_incoming_question(
        self,
        message_id: UUID,
        responder_id: UUID
    ) -> None:
        """
        Called when an agent receives a question that requires acknowledgment.
        Automatically sends "please wait" message.
        """
        conversation = await self._get_conversation_by_message(message_id)

        if not conversation:
            # Not a tracked conversation question
            return

        # Send automatic acknowledgment
        await self.acknowledgment.send_acknowledgment(
            conversation_id=conversation.id,
            responder_id=responder_id
        )

        # Update conversation state
        await self._transition_state(
            conversation_id=conversation.id,
            from_state=ConversationState.INITIATED,
            to_state=ConversationState.WAITING,
            event_type='acknowledged',
            triggered_by=responder_id
        )


    async def handle_timeout(self, conversation_id: UUID) -> None:
        """
        Called when a timeout occurs. Sends follow-up or escalates.
        """
        conversation = await self._get_conversation(conversation_id)

        if conversation.current_state == ConversationState.WAITING:
            # First timeout - send follow-up
            await self._send_follow_up(conversation)

        elif conversation.current_state == ConversationState.FOLLOW_UP:
            # Second timeout - escalate
            await self.escalation.escalate_conversation(conversation)


    async def handle_response(
        self,
        conversation_id: UUID,
        response_message_id: UUID
    ) -> None:
        """
        Called when the responder finally answers.
        Resolves the conversation.
        """
        await self._transition_state(
            conversation_id=conversation_id,
            from_state=None,  # Any state
            to_state=ConversationState.ANSWERED,
            event_type='answered',
            message_id=response_message_id
        )

        # Cancel any pending timeouts
        await self.timeout_handler.cancel_timeout(conversation_id)


    async def agent_cant_help(
        self,
        conversation_id: UUID,
        current_responder_id: UUID,
        reason: str
    ) -> None:
        """
        Called when an agent explicitly says they can't help.
        Routes to the next expert in hierarchy.
        """
        conversation = await self._get_conversation(conversation_id)

        # Send "routing to expert" message to asker
        await self._notify_routing_to_expert(
            conversation=conversation,
            current_responder_id=current_responder_id,
            reason=reason
        )

        # Escalate to next level
        await self.escalation.escalate_conversation(
            conversation=conversation,
            reason=f"Current responder can't help: {reason}"
        )
```

### 3. RoutingEngine

```python
# backend/agents/interaction/routing_engine.py

from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.agent import Agent


class RoutingEngine:
    """
    Determines which agent should receive a question based on:
    - Asking agent's role
    - Question type
    - Escalation level
    - Agent availability
    """

    def __init__(self, routing_hierarchy: Dict[str, Dict[str, List[str]]]):
        self.hierarchy = routing_hierarchy


    async def get_best_responder(
        self,
        asker_role: str,
        question_type: str,
        escalation_level: int = 0,
        db: Optional[AsyncSession] = None
    ) -> UUID:
        """
        Returns the agent ID that should receive this question.
        """
        # Get routing chain for this agent role and question type
        chain = self._get_routing_chain(asker_role, question_type)

        if escalation_level >= len(chain):
            # Reached end of chain, default to PM
            chain.append('project_manager')

        target_role = chain[escalation_level]

        # Find an available agent with this role
        # (In future: check agent availability, workload, etc.)
        if db:
            agent = await self._find_agent_by_role(db, target_role)
            return agent.id

        return target_role  # Return role name if no DB session


    def _get_routing_chain(self, asker_role: str, question_type: str) -> List[str]:
        """
        Returns the escalation chain for this role and question type.

        Example:
            asker_role='backend_developer', question_type='architecture'
            Returns: ['tech_lead', 'solution_architect', 'project_manager']
        """
        role_config = self.hierarchy.get(asker_role, {})

        # Try specific question type first
        chain = role_config.get(question_type)

        if not chain:
            # Fall back to default
            chain = role_config.get('default', ['project_manager'])

        return chain.copy()


    async def _find_agent_by_role(
        self,
        db: AsyncSession,
        role: str
    ) -> Agent:
        """
        Finds an available agent with the specified role.

        Future enhancements:
        - Check agent availability
        - Check agent workload
        - Round-robin if multiple agents with same role
        """
        result = await db.execute(
            select(Agent)
            .where(Agent.role == role)
            .where(Agent.is_active == True)
            .limit(1)
        )
        return result.scalar_one()
```

### 4. TimeoutHandler

```python
# backend/agents/interaction/timeout_handler.py

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.configuration.interaction_config import TimeoutConfig


class TimeoutHandler:
    """
    Manages timeout monitoring for conversations.

    In production, this would use:
    - Celery for scheduled tasks
    - Redis for distributed locking
    - Background workers

    For now, uses asyncio for simplicity.
    """

    def __init__(self, db: AsyncSession, config: TimeoutConfig):
        self.db = db
        self.config = config
        self._timeout_tasks: Dict[UUID, asyncio.Task] = {}


    async def schedule_timeout_check(
        self,
        conversation_id: UUID,
        timeout_at: datetime
    ) -> None:
        """
        Schedules a timeout check for a conversation.
        """
        delay = (timeout_at - datetime.utcnow()).total_seconds()

        if delay <= 0:
            # Already timed out
            await self._trigger_timeout(conversation_id)
            return

        # Schedule async task
        task = asyncio.create_task(
            self._wait_and_timeout(conversation_id, delay)
        )

        self._timeout_tasks[conversation_id] = task


    async def cancel_timeout(self, conversation_id: UUID) -> None:
        """
        Cancels a scheduled timeout (e.g., when question is answered).
        """
        task = self._timeout_tasks.get(conversation_id)

        if task and not task.done():
            task.cancel()
            del self._timeout_tasks[conversation_id]


    async def _wait_and_timeout(
        self,
        conversation_id: UUID,
        delay_seconds: float
    ) -> None:
        """
        Waits for the specified delay, then triggers timeout.
        """
        try:
            await asyncio.sleep(delay_seconds)
            await self._trigger_timeout(conversation_id)
        except asyncio.CancelledError:
            # Timeout was cancelled (question was answered)
            pass
        finally:
            self._timeout_tasks.pop(conversation_id, None)


    async def _trigger_timeout(self, conversation_id: UUID) -> None:
        """
        Triggers timeout handling for a conversation.

        This would call back to ConversationManager.handle_timeout()
        """
        from backend.agents.interaction.conversation_manager import ConversationManager

        manager = ConversationManager(self.db)
        await manager.handle_timeout(conversation_id)
```

### 5. Integration with Message Bus

```python
# backend/agents/communication/message_bus.py (additions)

class NATSMessageBus:
    # ... existing code ...

    async def send_message(
        self,
        sender_id: UUID,
        recipient_id: Optional[UUID],
        content: str,
        message_type: str,
        task_execution_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        requires_acknowledgment: bool = False,  # NEW
        conversation_id: Optional[UUID] = None,  # NEW
        parent_message_id: Optional[UUID] = None,  # NEW
        db: Optional[AsyncSession] = None
    ) -> AgentMessage:
        """
        Enhanced to support conversation tracking.
        """
        # Store message in database
        message = AgentMessage(
            id=uuid4(),
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content,
            message_type=message_type,
            task_execution_id=task_execution_id,
            metadata=metadata or {},
            requires_acknowledgment=requires_acknowledgment,  # NEW
            conversation_id=conversation_id,  # NEW
            parent_message_id=parent_message_id,  # NEW
            created_at=datetime.utcnow()
        )

        if db:
            db.add(message)
            await db.flush()

        # Publish to NATS
        await self._publish_to_nats(message)

        # If this is a question requiring acknowledgment, track it
        if requires_acknowledgment and message_type == 'question':
            from backend.agents.interaction.conversation_manager import ConversationManager
            manager = ConversationManager(db)
            await manager.handle_incoming_question(
                message_id=message.id,
                responder_id=recipient_id
            )

        return message
```

---

## Code Changes Required

### Summary of Files to Create/Modify

#### New Files (17 files)

1. **Configuration**
   - `backend/agents/configuration/__init__.py`
   - `backend/agents/configuration/interaction_config.py` (430 lines)

2. **Interaction Module**
   - `backend/agents/interaction/__init__.py`
   - `backend/agents/interaction/models.py` (Pydantic models - 150 lines)
   - `backend/agents/interaction/conversation_manager.py` (600 lines)
   - `backend/agents/interaction/routing_engine.py` (250 lines)
   - `backend/agents/interaction/timeout_handler.py` (200 lines)
   - `backend/agents/interaction/acknowledgment_service.py` (150 lines)
   - `backend/agents/interaction/escalation_service.py` (300 lines)

3. **Database**
   - `backend/alembic/versions/xxx_add_conversation_tracking.py` (migration - 200 lines)
   - `backend/models/conversation.py` (SQLAlchemy models - 250 lines)
   - `backend/models/conversation_event.py` (100 lines)

4. **Services**
   - `backend/services/conversation_service.py` (API layer - 300 lines)

5. **Background Workers**
   - `backend/workers/timeout_monitor.py` (Celery worker - 200 lines)

6. **Tests**
   - `backend/tests/test_agents/test_conversation_manager.py` (500 lines)
   - `backend/tests/test_agents/test_routing_engine.py` (300 lines)
   - `backend/tests/test_agents/test_timeout_handler.py` (350 lines)

#### Modified Files (8 files)

1. `backend/agents/communication/message_bus.py` (+100 lines)
2. `backend/agents/communication/nats_message_bus.py` (+150 lines)
3. `backend/models/agent_message.py` (+50 lines - new columns)
4. `backend/models/__init__.py` (+3 lines - imports)
5. `backend/core/config.py` (+20 lines - new settings)
6. `backend/services/agent_service.py` (+100 lines - conversation integration)
7. `.env.example` (+10 lines - new config)
8. `requirements.txt` (+2 lines if any new dependencies)

**Total**: ~4,500 lines of new code across 25 files

---

## Testing Strategy

### 1. Unit Tests

```python
# backend/tests/test_agents/test_routing_engine.py

import pytest
from backend.agents.interaction.routing_engine import RoutingEngine
from backend.agents.configuration.interaction_config import get_default_routing_hierarchy


@pytest.fixture
def routing_engine():
    hierarchy = get_default_routing_hierarchy()
    return RoutingEngine(hierarchy)


def test_backend_developer_implementation_question(routing_engine):
    """Backend dev asking about implementation should go to tech lead first"""
    chain = routing_engine._get_routing_chain('backend_developer', 'implementation')
    assert chain[0] == 'tech_lead'
    assert chain[1] == 'solution_architect'
    assert chain[2] == 'project_manager'


def test_backend_developer_architecture_question(routing_engine):
    """Backend dev asking about architecture should go to tech lead first"""
    chain = routing_engine._get_routing_chain('backend_developer', 'architecture')
    assert chain[0] == 'tech_lead'
    assert chain[1] == 'solution_architect'


def test_escalation_level_progression(routing_engine):
    """Escalation should progress through chain"""
    responder_0 = routing_engine.get_best_responder(
        asker_role='backend_developer',
        question_type='implementation',
        escalation_level=0
    )
    assert responder_0 == 'tech_lead'

    responder_1 = routing_engine.get_best_responder(
        asker_role='backend_developer',
        question_type='implementation',
        escalation_level=1
    )
    assert responder_1 == 'solution_architect'

    responder_2 = routing_engine.get_best_responder(
        asker_role='backend_developer',
        question_type='implementation',
        escalation_level=2
    )
    assert responder_2 == 'project_manager'


def test_unknown_question_type_uses_default(routing_engine):
    """Unknown question types should use default routing"""
    chain = routing_engine._get_routing_chain('backend_developer', 'unknown_type')
    assert chain[0] == 'tech_lead'
    assert 'project_manager' in chain
```

### 2. Integration Tests

```python
# backend/tests/test_agents/test_conversation_flow.py

import pytest
import asyncio
from datetime import timedelta
from backend.agents.interaction.conversation_manager import ConversationManager
from backend.agents.interaction.models import ConversationState


@pytest.mark.asyncio
async def test_happy_path_question_answered(db_session, test_agents):
    """Test normal flow: question → acknowledgment → answer"""
    backend_dev = test_agents['backend_developer']
    tech_lead = test_agents['tech_lead']

    manager = ConversationManager(db_session)

    # 1. Backend dev asks question
    conversation = await manager.initiate_question(
        asker_id=backend_dev.id,
        question_content="How should I implement caching?",
        question_type='implementation'
    )

    assert conversation.current_state == ConversationState.INITIATED
    assert conversation.current_responder_id == tech_lead.id

    # 2. Tech lead receives and acknowledges (automatic)
    await manager.handle_incoming_question(
        message_id=conversation.initial_message_id,
        responder_id=tech_lead.id
    )

    await db_session.refresh(conversation)
    assert conversation.current_state == ConversationState.WAITING
    assert conversation.acknowledged_at is not None

    # 3. Tech lead responds with answer
    response_message = await manager._send_message(
        sender_id=tech_lead.id,
        recipient_id=backend_dev.id,
        content="Use Redis with TTL of 1 hour",
        message_type='answer',
        conversation_id=conversation.id
    )

    await manager.handle_response(
        conversation_id=conversation.id,
        response_message_id=response_message.id
    )

    await db_session.refresh(conversation)
    assert conversation.current_state == ConversationState.ANSWERED
    assert conversation.resolved_at is not None


@pytest.mark.asyncio
async def test_timeout_and_follow_up(db_session, test_agents):
    """Test timeout flow: question → acknowledgment → timeout → follow-up → answer"""
    backend_dev = test_agents['backend_developer']
    tech_lead = test_agents['tech_lead']

    # Use very short timeout for testing
    config = InteractionConfig()
    config.timeouts.initial_timeout = timedelta(seconds=2)

    manager = ConversationManager(db_session, config)

    # 1. Backend dev asks question
    conversation = await manager.initiate_question(
        asker_id=backend_dev.id,
        question_content="How should I implement caching?",
        question_type='implementation'
    )

    # 2. Acknowledge
    await manager.handle_incoming_question(
        message_id=conversation.initial_message_id,
        responder_id=tech_lead.id
    )

    # 3. Wait for timeout
    await asyncio.sleep(3)

    await db_session.refresh(conversation)
    assert conversation.current_state == ConversationState.FOLLOW_UP

    # 4. Tech lead finally responds
    response_message = await manager._send_message(
        sender_id=tech_lead.id,
        recipient_id=backend_dev.id,
        content="Sorry for delay! Use Redis.",
        message_type='answer',
        conversation_id=conversation.id
    )

    await manager.handle_response(
        conversation_id=conversation.id,
        response_message_id=response_message.id
    )

    await db_session.refresh(conversation)
    assert conversation.current_state == ConversationState.ANSWERED


@pytest.mark.asyncio
async def test_full_escalation_chain(db_session, test_agents):
    """Test escalation: backend → tech lead (timeout) → architect (timeout) → PM"""
    backend_dev = test_agents['backend_developer']
    tech_lead = test_agents['tech_lead']
    architect = test_agents['solution_architect']
    pm = test_agents['project_manager']

    # Very short timeouts for testing
    config = InteractionConfig()
    config.timeouts.initial_timeout = timedelta(seconds=1)
    config.timeouts.retry_timeout = timedelta(seconds=1)

    manager = ConversationManager(db_session, config)

    # 1. Backend asks tech lead
    conversation = await manager.initiate_question(
        asker_id=backend_dev.id,
        question_content="How to design microservices?",
        question_type='architecture'
    )

    assert conversation.current_responder_id == tech_lead.id
    assert conversation.escalation_level == 0

    # 2. Acknowledge but don't answer (timeout)
    await manager.handle_incoming_question(
        message_id=conversation.initial_message_id,
        responder_id=tech_lead.id
    )

    # Wait for timeout + follow-up timeout
    await asyncio.sleep(3)

    # 3. Should have escalated to architect
    await db_session.refresh(conversation)
    assert conversation.current_responder_id == architect.id
    assert conversation.escalation_level == 1

    # 4. Architect acknowledges but doesn't answer (timeout again)
    # Wait for another round of timeouts
    await asyncio.sleep(3)

    # 5. Should have escalated to PM
    await db_session.refresh(conversation)
    assert conversation.current_responder_id == pm.id
    assert conversation.escalation_level == 2
```

### 3. End-to-End Demo

```python
# demo_hierarchical_routing.py

"""
Demonstrates the complete hierarchical routing and escalation system.
"""

import asyncio
from datetime import timedelta
from backend.agents.interaction.conversation_manager import ConversationManager
from backend.agents.configuration.interaction_config import InteractionConfig


async def demo_escalation_chain():
    """
    Scenario: Backend developer asks about microservices architecture.
    - Tech lead can't help, routes to architect
    - Architect provides answer
    """

    print("🎬 Demo: Hierarchical Routing with Expert Escalation\n")

    # ... setup agents ...

    config = InteractionConfig()
    manager = ConversationManager(db, config)

    # Backend asks question
    print("📤 Backend Developer → Tech Lead")
    print("   'How should we structure our microservices?'\n")

    conversation = await manager.initiate_question(
        asker_id=backend_dev.id,
        question_content="How should we structure our microservices?",
        question_type='architecture'
    )

    await asyncio.sleep(1)

    # Tech lead acknowledges
    print("📨 Tech Lead → Backend Developer")
    print("   'Let me think about this, please wait...'\n")

    await asyncio.sleep(2)

    # Tech lead realizes they need expert help
    print("🤔 Tech Lead → Solution Architect")
    print("   'This is above my expertise. Let me connect you with our architect'\n")

    await manager.agent_cant_help(
        conversation_id=conversation.id,
        current_responder_id=tech_lead.id,
        reason="Architecture design requires solution architect expertise"
    )

    await asyncio.sleep(1)

    # Architect acknowledges
    print("📨 Solution Architect → Backend Developer")
    print("   'Let me think about this, please wait...'\n")

    await asyncio.sleep(3)

    # Architect provides detailed answer
    print("✅ Solution Architect → Backend Developer")
    print("   'For microservices, I recommend: 1) Domain-driven design...")
    print("   2) API Gateway pattern 3) Service mesh for inter-service comms'\n")

    print("🎉 Question resolved! Backend developer got expert help.\n")


async def demo_timeout_escalation():
    """
    Scenario: Tech lead doesn't respond, auto-escalates to PM.
    """

    print("🎬 Demo: Timeout-Based Auto-Escalation\n")

    # Short timeouts for demo
    config = InteractionConfig()
    config.timeouts.initial_timeout = timedelta(seconds=3)
    config.timeouts.retry_timeout = timedelta(seconds=2)

    manager = ConversationManager(db, config)

    # Backend asks question
    print("📤 Backend Developer → Tech Lead")
    print("   'How do I implement caching?'\n")

    conversation = await manager.initiate_question(
        asker_id=backend_dev.id,
        question_content="How do I implement caching?",
        question_type='implementation'
    )

    await asyncio.sleep(1)

    # Tech lead acknowledges
    print("📨 Tech Lead → Backend Developer")
    print("   'Let me think about this, please wait...'\n")

    # Wait for initial timeout
    print("⏳ Waiting 3 seconds...\n")
    await asyncio.sleep(4)

    # System sends follow-up
    print("🔔 System → Tech Lead")
    print("   'Are you still there? Backend Developer is waiting for a response.'\n")

    # Wait for retry timeout
    print("⏳ Waiting 2 more seconds...\n")
    await asyncio.sleep(3)

    # System escalates to PM
    print("⬆️  System: Escalating to Project Manager\n")

    print("📤 System → Project Manager")
    print("   'Backend Developer has a question that needs attention:")
    print("    How do I implement caching?'\n")

    await asyncio.sleep(1)

    # PM assigns another tech lead
    print("✅ Project Manager → Backend Developer")
    print("   'I'll get another tech lead to help you with this.'\n")

    print("🎉 Escalation successful! Question didn't get lost.\n")


if __name__ == "__main__":
    asyncio.run(demo_escalation_chain())
    asyncio.run(demo_timeout_escalation())
```

---

## Rollout Plan

### Phase 1: Foundation (Week 1)
**Goal**: Database schema and core models

- [ ] Create database migration for `agent_conversations` and `conversation_events` tables
- [ ] Update `agent_messages` table with new columns
- [ ] Run migrations in dev environment
- [ ] Create SQLAlchemy models (`Conversation`, `ConversationEvent`)
- [ ] Create Pydantic models for API layer
- [ ] Write unit tests for models

**Deliverable**: Database ready to track conversations

### Phase 2: Configuration (Week 1-2)
**Goal**: Routing hierarchy and timeout configuration

- [ ] Create `interaction_config.py` with all config classes
- [ ] Define complete routing hierarchy for all agent roles
- [ ] Add environment variables to `.env`
- [ ] Create config validation tests
- [ ] Document configuration options

**Deliverable**: Configuration system ready

### Phase 3: Routing Engine (Week 2)
**Goal**: Determine who should answer questions

- [ ] Implement `RoutingEngine` class
- [ ] Write routing logic based on role + question type
- [ ] Add escalation level progression
- [ ] Write comprehensive unit tests
- [ ] Test all routing scenarios

**Deliverable**: Routing engine functional and tested

### Phase 4: Timeout Handler (Week 2-3)
**Goal**: Monitor conversations and trigger timeouts

- [ ] Implement `TimeoutHandler` with asyncio tasks
- [ ] Add timeout scheduling and cancellation
- [ ] Integrate with background task system (Celery/APScheduler)
- [ ] Write timeout tests with mock timers
- [ ] Test concurrent timeout handling

**Deliverable**: Timeout system working

### Phase 5: Acknowledgment Service (Week 3)
**Goal**: Auto-send "please wait" messages

- [ ] Implement `AcknowledgmentService`
- [ ] Create message templates
- [ ] Integrate with message bus
- [ ] Add acknowledgment detection
- [ ] Write integration tests

**Deliverable**: Auto-acknowledgment working

### Phase 6: Escalation Service (Week 3-4)
**Goal**: Route questions to higher authority

- [ ] Implement `EscalationService`
- [ ] Add escalation logic (next in chain)
- [ ] Create escalation notification messages
- [ ] Handle max escalation level (PM)
- [ ] Write escalation tests

**Deliverable**: Escalation functional

### Phase 7: Conversation Manager (Week 4)
**Goal**: Orchestrate all components

- [ ] Implement `ConversationManager` class
- [ ] Integrate routing, timeout, acknowledgment, escalation
- [ ] Add conversation state transitions
- [ ] Create conversation event logging
- [ ] Write end-to-end integration tests

**Deliverable**: Core system complete

### Phase 8: Message Bus Integration (Week 4-5)
**Goal**: Hook into existing NATS message bus

- [ ] Update `message_bus.py` with conversation support
- [ ] Add `requires_acknowledgment` flag handling
- [ ] Integrate conversation tracking on message send
- [ ] Update message consumers to detect acknowledgments/answers
- [ ] Test with real NATS messages

**Deliverable**: Full integration with message bus

### Phase 9: Agent Integration (Week 5)
**Goal**: Agents use the system automatically

- [ ] Update agent base class to use ConversationManager
- [ ] Add hooks for asking questions
- [ ] Add hooks for answering questions
- [ ] Add "can't help" functionality for agents
- [ ] Test with multiple agents

**Deliverable**: Agents using hierarchical routing

### Phase 10: Monitoring & Observability (Week 5-6)
**Goal**: Track system health and metrics

- [ ] Add logging for all conversation events
- [ ] Create metrics (questions asked, timeouts, escalations)
- [ ] Build admin dashboard to view conversations
- [ ] Add alerts for excessive timeouts
- [ ] Document monitoring setup

**Deliverable**: System observable and debuggable

### Phase 11: Testing & Demo (Week 6)
**Goal**: Comprehensive testing and demo

- [ ] Write demo scripts (like `demo_nats_agents.py`)
- [ ] Create visual demo of escalation chain
- [ ] Run load tests (100+ concurrent conversations)
- [ ] Fix any bugs found in testing
- [ ] Document all features

**Deliverable**: System ready for production

### Phase 12: Documentation & Rollout (Week 6-7)
**Goal**: Deploy to production

- [ ] Write user documentation
- [ ] Create migration guide
- [ ] Deploy to staging environment
- [ ] Run staging tests for 1 week
- [ ] Deploy to production with feature flag
- [ ] Monitor production metrics
- [ ] Gradual rollout to all users

**Deliverable**: System in production

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1. Foundation | Week 1 | Database schema |
| 2. Configuration | Week 1-2 | Config system |
| 3. Routing Engine | Week 2 | Routing logic |
| 4. Timeout Handler | Week 2-3 | Timeout monitoring |
| 5. Acknowledgment | Week 3 | Auto-acknowledgment |
| 6. Escalation | Week 3-4 | Escalation routing |
| 7. Conversation Manager | Week 4 | Core orchestration |
| 8. Message Bus Integration | Week 4-5 | NATS integration |
| 9. Agent Integration | Week 5 | Agents using system |
| 10. Monitoring | Week 5-6 | Observability |
| 11. Testing & Demo | Week 6 | Comprehensive tests |
| 12. Documentation & Rollout | Week 6-7 | Production deployment |

**Total Duration**: 6-7 weeks for full implementation and deployment

---

## Success Metrics

### Functional Metrics
- ✅ 95%+ of questions get acknowledged within 30 seconds
- ✅ 85%+ of questions answered without escalation
- ✅ 99%+ of questions eventually answered (with escalation)
- ✅ Average time to answer < 5 minutes
- ✅ Escalation chain always reaches PM as final fallback

### Performance Metrics
- ✅ Timeout checks run with <1 second overhead
- ✅ Routing decisions complete in <100ms
- ✅ Database queries <50ms per conversation operation
- ✅ System handles 1000+ concurrent conversations

### Quality Metrics
- ✅ 95%+ unit test coverage
- ✅ All integration tests passing
- ✅ Zero data loss in conversation tracking
- ✅ Clear audit trail for all escalations

---

## Risks & Mitigations

### Risk 1: Timeout System Overhead
**Risk**: Monitoring thousands of timeouts could impact performance

**Mitigation**:
- Use background workers (Celery) for timeout checks
- Batch timeout checks (check every 30 seconds)
- Use database indexes for efficient timeout queries
- Consider Redis for timeout tracking in high-scale scenarios

### Risk 2: Infinite Escalation Loops
**Risk**: Question gets escalated in a loop without resolution

**Mitigation**:
- Max escalation level (always end at PM)
- Escalation counter prevents re-routing to same agent
- PM as final "catch-all" that must respond
- Alert if conversation exceeds max escalation

### Risk 3: Message Delivery Failures
**Risk**: NATS message lost, conversation stuck

**Mitigation**:
- NATS JetStream provides message persistence
- Retry logic with exponential backoff
- Dead letter queue for undeliverable messages
- Manual intervention UI for stuck conversations

### Risk 4: Configuration Complexity
**Risk**: Complex routing hierarchies become hard to maintain

**Mitigation**:
- Configuration validation on startup
- Visual routing diagram in docs
- Admin UI to visualize routing paths
- Unit tests for all routing scenarios
- Version control for routing config changes

### Risk 5: Agent Availability
**Risk**: Target agent role has no available agents

**Mitigation**:
- Always have fallback to PM
- Check agent availability before routing
- Support multiple agents per role (round-robin)
- Alert when critical roles have no agents

---

## Future Enhancements

### Phase 2 Features (Post-MVP)

1. **Smart Routing**
   - ML-based routing based on question content
   - Route to agent with relevant expertise/experience
   - Learn from past successful answers

2. **Agent Workload Balancing**
   - Track questions per agent
   - Route to least-busy agent of appropriate role
   - Prevent overload of individual agents

3. **Context-Aware Escalation**
   - Include conversation history when escalating
   - Summarize previous attempts to answer
   - Highlight urgency/priority

4. **Question Similarity Detection**
   - Detect duplicate/similar questions
   - Reference existing answers
   - Build knowledge base over time

5. **Customizable Acknowledgments**
   - Agents can customize their "please wait" messages
   - Include estimated response time
   - Different templates per question type

6. **Conversation Analytics**
   - Dashboard showing escalation patterns
   - Identify bottlenecks (which agents/roles)
   - Track average response times
   - Identify frequently asked questions

7. **Human-in-the-Loop**
   - Notify real humans for critical escalations
   - Allow manual intervention in conversations
   - Override routing for special cases

---

## Conclusion

This plan provides a complete architecture for intelligent agent-to-agent communication with:

✅ **Hierarchical Routing**: Agents know who to ask based on role and question type
✅ **Acknowledgment Protocol**: "Please wait" messages provide feedback
✅ **Timeout & Retry**: No questions get lost
✅ **Automatic Escalation**: Questions always reach someone who can help
✅ **Default Behavior**: Built into all agents transparently

The system mimics realistic team dynamics where:
- Junior devs ask senior devs
- Senior devs ask tech leads
- Tech leads ask architects
- Everyone can escalate to PM if needed

Implementation is broken into 12 phases over 6-7 weeks, with clear deliverables and testing at each phase.

**Next Steps**:
1. Review and approve this plan
2. Prioritize which phases to implement first
3. Allocate engineering resources
4. Begin Phase 1 (Database Foundation)

---

**Questions for Discussion**:
1. Are the timeout durations reasonable (5 min initial, 2 min retry)?
2. Should we support manual conversation intervention from the start?
3. Do we need webhooks/notifications when questions are unanswered?
4. Should certain question types have different timeout values?
5. How should we handle "urgent" questions (skip timeouts, route directly to PM)?
