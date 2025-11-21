# Agent System Architecture

## Overview

The Agent Squad system implements a distributed, collaborative AI agent architecture using the **Agno framework** for persistent memory and session management, **NATS JetStream** for distributed message bus, and **PostgreSQL** for persistence.

---

## Models

### Core Models (SQLAlchemy)

#### Squad & Squad Member
- **Squad** (`backend/models/squad.py:12`): Container for agent teams
  - Fields: `id`, `org_id`, `user_id`, `name`, `description`, `status`, `config`
  - Relationships: `members`, `projects`, `task_executions`, `llm_cost_entries`
  - Status: `active | paused | archived`

- **SquadMember** (`backend/models/squad.py:41`): Individual AI agents
  - Fields: `id`, `squad_id`, `role`, `specialization`, `llm_provider`, `llm_model`, `system_prompt`, `config`
  - Roles: `project_manager`, `tech_lead`, `backend_developer`, `frontend_developer`, `qa_tester`, `solution_architect`, `devops_engineer`, `ai_engineer`, `designer`
  - Relationships: `sent_messages`, `received_messages`, `multi_turn_conversations`
  - LLM Providers: `openai`, `anthropic`, `groq`, `ollama`

#### Task Execution
- **Task** (`backend/models/project.py:37`): Work items
  - Fields: `id`, `project_id`, `external_id`, `title`, `description`, `status`, `priority`, `assigned_to`
  - Status: `pending | in_progress | blocked | completed | failed`
  - Priority: `low | medium | high | urgent`

- **TaskExecution** (`backend/models/project.py:64`): Execution tracking
  - Fields: `id`, `task_id`, `squad_id`, `status`, `started_at`, `completed_at`, `logs`, `error_message`
  - Relationships: `messages`, `conversations`, `llm_cost_entries`

#### Agent Messages
- **AgentMessage** (`backend/models/agent_message.py:13`): Agent-to-agent communication
  - Fields: `id`, `task_execution_id`, `sender_id`, `recipient_id`, `content`, `message_type`, `message_metadata`
  - Message Types: `task_assignment`, `question`, `answer`, `status_update`, `code_review_request`, `code_review_response`, `task_completion`, `standup`, `human_intervention_required`
  - Conversation tracking: `conversation_id`, `parent_message_id`, `is_acknowledgment`, `is_follow_up`, `is_escalation`

#### Conversations
- **Conversation** (`backend/models/conversation.py:28`): Agent-to-agent escalation conversations
  - Fields: `id`, `initial_message_id`, `current_state`, `asker_id`, `current_responder_id`, `escalation_level`
  - States: `initiated | waiting | timeout | follow_up | escalating | escalated | answered | cancelled`
  - Tracks timeouts, acknowledgments, escalations

- **ConversationEvent** (`backend/models/conversation.py:129`): Audit trail for conversations
  - Fields: `id`, `conversation_id`, `event_type`, `from_state`, `to_state`, `message_id`, `triggered_by_agent_id`

- **MultiTurnConversation** (`backend/models/multi_turn_conversation.py:22`): User/agent dialogues
  - Types: `user_agent`, `agent_agent`, `multi_party`
  - Fields: `id`, `conversation_type`, `initiator_id`, `initiator_type`, `primary_responder_id`, `status`, `total_messages`
  - Relationships: `messages`, `participants`

---

## Agent Types and Roles

### Specialized Agents (All Agno-Powered)

#### 1. Project Manager (`agno_project_manager.py`)
- **Role**: Squad orchestrator
- **Capabilities**: 
  - Receive webhook notifications
  - Review tickets with Tech Lead
  - Estimate effort & complexity
  - Break down tasks
  - Delegate to team
  - Monitor progress
  - Conduct standups
  - Escalate to humans
- **Workflow**: `PENDING → ANALYZING → PLANNING → DELEGATED → IN_PROGRESS → REVIEWING → TESTING → COMPLETED`

#### 2. Tech Lead (`agno_tech_lead.py`)
- **Role**: Technical leadership
- **Capabilities**:
  - Review technical feasibility
  - Estimate complexity (1-10)
  - Review code/PRs
  - Provide architecture guidance
  - Make technical decisions
  - Mentor developers

#### 3. Backend Developer (`agno_backend_developer.py`)
- **Role**: Backend implementation
- **Capabilities**:
  - Analyze tasks
  - Plan implementation
  - Write code (via MCP tools)
  - Write tests
  - Create pull requests
  - Request code review
  - Troubleshoot issues

#### 4. Frontend Developer (`agno_frontend_developer.py`)
- **Role**: Frontend implementation
- **Specializations**: `react_nextjs`, `vue_nuxt`, `angular`

#### 5. QA Tester (`agno_qa_tester.py`)
- **Role**: Quality assurance
- **Test Types**: Functional, Integration, Regression, Performance, Security, Accessibility

#### 6-9. Support Roles
- **Solution Architect**: System architecture, ADRs
- **DevOps Engineer**: Infrastructure, CI/CD, deployments
- **AI Engineer**: ML models, LLM integration
- **Designer**: UX/UI design, wireframes

### Agent Hierarchy

```
Project Manager (Orchestrator)
    ├── Tech Lead (Technical Oversight)
    │   ├── Backend Developers
    │   ├── Frontend Developers
    │   ├── DevOps Engineers
    │   └── AI Engineers
    ├── Solution Architect (High-level Design)
    ├── QA Testers (Quality Gates)
    └── Designer (UX/UI)
```

---

## Message Bus Implementation

### NATS JetStream (`backend/agents/communication/nats_message_bus.py`)

**Architecture**:
- **Distributed**: Multi-server support with horizontal scaling
- **Persistent**: Messages survive restarts (JetStream storage)
- **Sub-millisecond latency**: High-performance messaging
- **Pub/Sub**: Real-time subscriptions

**Key Components**:
1. **Connection Management**:
   - Auto-reconnection
   - Error callbacks
   - Connection health monitoring

2. **Message Streams**:
   - Stream name: `agent_messages`
   - Subjects: `agent.message.*` (by type)
   - Retention: Limits-based (max messages, max age)
   - Storage: File-based persistence

3. **Message Operations**:
   - `send_message()`: Point-to-point messaging
   - `broadcast_message()`: Send to all agents
   - `subscribe()`: Real-time callbacks
   - `get_stats()`: Stream statistics

4. **Integration**:
   - SSE Service: Broadcasts to frontend
   - Database: Persists all messages
   - History Manager: Message retrieval

**Message Flow**:
```
Agent A → send_message() 
    → NATS JetStream (persist)
    → Agent B's queue
    → Database (store)
    → SSE Service (broadcast to frontend)
    → Subscribers (callbacks)
```

### Protocol (`backend/agents/communication/protocol.py`)

**Message Types**:
- `TaskAssignment`: PM → Developer
- `StatusUpdate`: Developer → PM
- `Question`: Agent → Agent (broadcast)
- `Answer`: Agent → Agent
- `CodeReviewRequest`: Developer → Tech Lead
- `CodeReviewResponse`: Tech Lead → Developer
- `TaskCompletion`: Developer → PM
- `HumanInterventionRequired`: PM → Human
- `Standup`: PM → All agents

**Parser**: A2AProtocol class with Pydantic validation

---

## Task Execution Flow

### Orchestration (`backend/agents/orchestration/orchestrator.py`)

**Workflow States**:
```
PENDING → ANALYZING → PLANNING → DELEGATED → IN_PROGRESS → REVIEWING → TESTING → COMPLETED
                                      ↓                                        ↓
                                   BLOCKED ←──────────────────────────────────┘
                                      ↓
                                   FAILED
```

**State Transitions**:
- PM analyzes task: `PENDING → ANALYZING`
- PM creates plan: `ANALYZING → PLANNING`
- PM delegates: `PLANNING → DELEGATED`
- Dev works: `DELEGATED → IN_PROGRESS`
- Code review: `IN_PROGRESS → REVIEWING`
- QA tests: `REVIEWING → TESTING`
- Complete: `TESTING → COMPLETED`

**Orchestrator Responsibilities**:
1. Execute tasks from start to finish
2. Monitor progress via state machine
3. Handle blockers (pause execution)
4. Resolve blockers (resume execution)
5. Escalate to humans when stuck
6. Collect metrics and logs

### Workflow Engine (`backend/agents/orchestration/workflow_engine.py`)

**State Machine**:
- Validates transitions
- Executes state actions
- Calculates progress (0-100%)
- Tracks time in each state
- Enforces business rules

**Progress Calculation**:
- PENDING: 0%
- ANALYZING: 12%
- PLANNING: 25%
- DELEGATED: 37%
- IN_PROGRESS: 62%
- REVIEWING: 75%
- TESTING: 87%
- COMPLETED: 100%

---

## Conversations & Dialogue Tracking

### Agent-to-Agent Conversations (`backend/models/conversation.py`)

**Purpose**: Handle escalations with timeout and retry logic

**States**:
- `initiated`: Question sent
- `waiting`: Acknowledged, waiting for answer
- `timeout`: No answer after timeout
- `follow_up`: Sent "are you still there?"
- `escalating`: Escalating to higher level
- `escalated`: Re-routed to different agent
- `answered`: Resolved
- `cancelled`: Asker cancelled

**Features**:
- Timeout monitoring
- Acknowledgment tracking
- Escalation levels
- Event audit trail

### Multi-Turn Conversations (`backend/models/multi_turn_conversation.py`)

**Purpose**: Support user ↔ agent and agent ↔ agent dialogues

**Types**:
- `user_agent`: User talking to one agent
- `agent_agent`: Two agents conversing
- `multi_party`: Multiple participants

**Message Tracking**:
- Role: `user`, `assistant`, `system`
- Token usage (input/output)
- LLM metadata (model, provider, temperature)
- Response time

---

## Key Files

### Core Agent Framework
- `/backend/agents/agno_base.py` - Base agent class (Agno-powered)
- `/backend/agents/factory.py` - Agent creation factory
- `/backend/core/agno_config.py` - Agno framework configuration

### Specialized Agents
- `/backend/agents/specialized/agno_project_manager.py` - PM agent
- `/backend/agents/specialized/agno_tech_lead.py` - Tech Lead agent
- `/backend/agents/specialized/agno_backend_developer.py` - Backend dev
- `/backend/agents/specialized/agno_frontend_developer.py` - Frontend dev
- `/backend/agents/specialized/agno_qa_tester.py` - QA tester
- `/backend/agents/specialized/agno_solution_architect.py` - Architect
- `/backend/agents/specialized/agno_devops_engineer.py` - DevOps
- `/backend/agents/specialized/agno_ai_engineer.py` - AI/ML engineer
- `/backend/agents/specialized/agno_designer.py` - Designer

### Communication
- `/backend/agents/communication/nats_message_bus.py` - NATS message bus
- `/backend/agents/communication/message_bus.py` - In-memory fallback
- `/backend/agents/communication/protocol.py` - A2A protocol parser
- `/backend/agents/communication/history_manager.py` - Message history
- `/backend/agents/communication/message_utils.py` - Utilities

### Orchestration
- `/backend/agents/orchestration/orchestrator.py` - Task orchestrator
- `/backend/agents/orchestration/workflow_engine.py` - State machine
- `/backend/agents/orchestration/delegation_engine.py` - Task delegation
- `/backend/agents/orchestration/phase_based_engine.py` - Phase management

### Models
- `/backend/models/squad.py` - Squad & SquadMember
- `/backend/models/project.py` - Task & TaskExecution
- `/backend/models/agent_message.py` - AgentMessage
- `/backend/models/conversation.py` - Conversation & ConversationEvent
- `/backend/models/multi_turn_conversation.py` - MultiTurnConversation
- `/backend/models/llm_cost_tracking.py` - LLM cost tracking
- `/backend/models/workflow.py` - Workflow phases & dynamic tasks

### Services
- `/backend/services/agent_service.py` - Agent CRUD operations
- `/backend/services/squad_service.py` - Squad management
- `/backend/services/task_execution_service.py` - Task execution
- `/backend/services/conversation_service.py` - Conversation management
- `/backend/services/sse_service.py` - Real-time frontend updates

---

## Data Flow Summary

### Message Flow
```
1. Agent A creates message
2. Message Bus (NATS) routes to Agent B
3. Persist to database (AgentMessage table)
4. SSE broadcasts to frontend
5. History Manager stores for retrieval
6. Agent B retrieves and processes
```

### Task Execution Flow
```
1. User creates task → PENDING
2. PM analyzes → ANALYZING
3. PM plans with TL → PLANNING
4. PM delegates → DELEGATED
5. Devs implement → IN_PROGRESS
6. TL reviews → REVIEWING
7. QA tests → TESTING
8. Complete → COMPLETED
```

### Conversation Flow
```
1. Agent A asks question → initiated
2. Agent B acknowledges → waiting
3. If timeout → follow_up
4. If still timeout → escalating
5. Re-route to higher level → escalated
6. Agent C answers → answered
```

---

## Technology Stack

- **Agent Framework**: Agno (persistent sessions, memory management)
- **Message Bus**: NATS JetStream (distributed, persistent)
- **Database**: PostgreSQL (persistence)
- **LLM Providers**: OpenAI, Anthropic, Groq, Ollama
- **Real-time Updates**: SSE (Server-Sent Events)
- **ORM**: SQLAlchemy (async)
- **Validation**: Pydantic

---

## Key Insights for Frontend Visualization

1. **Squad Structure**: Hierarchical with PM at top, TL overseeing devs
2. **Message Flow**: All messages go through NATS → Database → SSE
3. **Task States**: Clear progression with % completion
4. **Conversation States**: Track timeout/escalation lifecycle
5. **Real-time**: SSE provides live updates to frontend
6. **Cost Tracking**: All LLM usage tracked per agent
7. **Relationships**: Squad → Members → Messages → Conversations → Tasks

---

## Recommended Visualization Components

1. **Squad Hierarchy Tree**: Show agent roles and relationships
2. **Message Timeline**: Real-time message flow between agents
3. **Task Kanban Board**: Workflow states (PENDING → COMPLETED)
4. **Conversation Threads**: Thread view with escalations
5. **Agent Status Dashboard**: Active/idle, current task, workload
6. **Cost Analytics**: Token usage, cost per agent/task
7. **Workflow Progress**: State machine visualization

