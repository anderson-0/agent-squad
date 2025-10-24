# Agno Architecture Guide
**Enterprise-Grade Multi-Agent System**

**Status**: Production-Ready ✅
**Framework**: Agno (Sole Implementation)
**Message Bus**: NATS JetStream (Default)
**Last Updated**: October 23, 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Why Agno?](#why-agno)
3. [Architecture](#architecture)
4. [Core Components](#core-components)
5. [Agent Lifecycle](#agent-lifecycle)
6. [Session Management](#session-management)
7. [Message Bus Integration](#message-bus-integration)
8. [Production Deployment](#production-deployment)
9. [Migration from Legacy](#migration-from-legacy)
10. [Best Practices](#best-practices)

---

## Overview

The Agent Squad system uses **Agno** as its sole agent framework. Agno is an enterprise-grade multi-agent framework that provides:

- ✅ **Persistent Sessions**: Conversations survive server restarts
- ✅ **Automatic Memory**: Agno manages conversation history in PostgreSQL
- ✅ **Production-Ready**: Battle-tested architecture used in production
- ✅ **Session Resumption**: Resume conversations by session ID
- ✅ **Built-in Observability**: Logging, metrics, and debugging support

### What is Agno?

Agno is a Python framework for building production-grade AI agents. Unlike simple LLM wrappers, Agno provides:

1. **Session Persistence**: Sessions stored in PostgreSQL database
2. **Memory Management**: Automatic conversation history tracking
3. **Tool Integration**: Built-in support for external tools (MCP, Function Calling)
4. **Multi-Agent Coordination**: Native support for agent-to-agent communication
5. **Production Features**: Logging, monitoring, error handling out-of-the-box

---

## Why Agno?

### Before Agno (Custom Agents)

The previous implementation used custom `BaseSquadAgent` with limitations:

❌ **No Session Persistence**: Conversations lost on restart
❌ **Manual Memory Management**: Complex history tracking code
❌ **Custom Architecture**: Maintenance burden
❌ **Limited Observability**: DIY logging and monitoring
❌ **Session Resumption**: Not supported

### After Agno (Current)

Agno provides enterprise features out-of-the-box:

✅ **Automatic Session Persistence**: PostgreSQL storage
✅ **Built-in Memory**: Agno tracks history automatically
✅ **Proven Architecture**: Used by production systems
✅ **Rich Observability**: Logging, metrics, debugging
✅ **Session Resumption**: Resume any conversation

### Code Comparison

#### Before (Custom BaseSquadAgent):
```python
# Manual session management
agent = BaseSquadAgent(config)
# No persistence - lost on restart
response = await agent.process_message("Hello")
# Manual history tracking required
```

#### After (Agno):
```python
# Automatic session management
agent = AgentFactory.create_agent(
    agent_id=uuid4(),
    role="project_manager",
    session_id=existing_session_id  # Resume existing conversation
)
# Session persisted automatically
response = await agent.process_message("Continue our discussion")
# History managed by Agno automatically
```

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Agent Squad System (Agno-Based)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Agent Factory (AgentFactory)                │   │
│  │  Creates and manages all Agno-based agents              │   │
│  └────────────────────┬────────────────────────────────────┘   │
│                       │                                          │
│                       ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │        Specialized Agno Agents (9 roles)                │   │
│  │  PM, TL, BE Dev, FE Dev, QA, Architect, DevOps, AI, UX  │   │
│  │  All inherit from AgnoSquadAgent                        │   │
│  └────────────┬────────────────────────────┬───────────────┘   │
│               │                             │                    │
│               ▼                             ▼                    │
│  ┌────────────────────┐      ┌─────────────────────────┐       │
│  │  Agno Framework    │      │  NATS JetStream         │       │
│  │  • PostgreSQL DB   │      │  • Message Bus          │       │
│  │  • Session Store   │      │  • Pub/Sub              │       │
│  │  • Memory Mgmt     │      │  • Persistence          │       │
│  └────────────────────┘      └─────────────────────────┘       │
│               │                             │                    │
│               └──────────────┬──────────────┘                    │
│                              ▼                                   │
│                    ┌──────────────────┐                         │
│                    │   LLM Providers   │                         │
│                    │  OpenAI, Anthropic│                         │
│                    └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

### Component Flow

```
User Request
    ↓
FastAPI Endpoint
    ↓
AgentService (creates agent via Factory)
    ↓
AgentFactory.create_agent()
    ↓
AgnoSquadAgent instance created
    ↓
agent.process_message() → Agno manages session
    ↓
LLM Provider (OpenAI/Anthropic/Groq)
    ↓
Response stored in PostgreSQL (by Agno)
    ↓
Message sent via NATS (to other agents if needed)
    ↓
Response returned to user
```

---

## Core Components

### 1. AgentFactory

**Location**: `backend/agents/factory.py`

**Purpose**: Create and manage Agno agent instances

**Key Features**:
- ✅ Single registry for all 9 agent roles
- ✅ Agent instance caching (by UUID)
- ✅ System prompt loading from `roles/` directory
- ✅ Session resumption support

**Usage**:
```python
from backend.agents.factory import AgentFactory
from uuid import uuid4

# Create new agent
agent = AgentFactory.create_agent(
    agent_id=uuid4(),
    role="project_manager",
    llm_provider="openai",
    llm_model="gpt-4o",
    temperature=0.7,
    session_id=None  # New session
)

# Resume existing agent
agent = AgentFactory.create_agent(
    agent_id=existing_agent_id,
    role="project_manager",
    session_id="existing-session-uuid"  # Resume session
)

# Get existing agent
agent = AgentFactory.get_agent(agent_id)

# Remove agent
AgentFactory.remove_agent(agent_id)
```

### 2. AgnoSquadAgent (Base Class)

**Location**: `backend/agents/agno_base.py`

**Purpose**: Base class for all specialized agents

**Key Features**:
- ✅ Persistent sessions in PostgreSQL
- ✅ Automatic conversation history
- ✅ Multi-LLM support (OpenAI, Anthropic, Groq)
- ✅ Message bus integration (send/broadcast)
- ✅ Tool execution support (MCP)

**Key Methods**:
```python
# Process user message
response = await agent.process_message(
    message="Your message",
    context={"key": "value"}
)

# Send message to another agent
await agent.send_message(
    recipient_id=other_agent_id,
    content="Message content",
    message_type="question",
    task_execution_id=execution_id
)

# Broadcast to all agents
await agent.broadcast_message(
    content="Announcement",
    message_type="standup"
)
```

### 3. Specialized Agents (9 Roles)

**Location**: `backend/agents/specialized/agno_*.py`

All agents inherit from `AgnoSquadAgent`:

| Role | Class | Purpose |
|------|-------|---------|
| Project Manager | `AgnoProjectManagerAgent` | Orchestrates squad, delegates tasks |
| Tech Lead | `AgnoTechLeadAgent` | Technical leadership, code review |
| Backend Developer | `AgnoBackendDeveloperAgent` | Backend implementation |
| Frontend Developer | `AgnoFrontendDeveloperAgent` | Frontend implementation |
| QA Tester | `AgnoQATesterAgent` | Quality assurance, testing |
| Solution Architect | `AgnoSolutionArchitectAgent` | Architecture, system design |
| DevOps Engineer | `AgnoDevOpsEngineerAgent` | Infrastructure, deployment |
| AI Engineer | `AgnoAIEngineerAgent` | AI/ML development |
| Designer | `AgnoDesignerAgent` | UX/UI design |

**Usage**:
```python
# Create project manager
pm = AgentFactory.create_agent(
    agent_id=uuid4(),
    role="project_manager"
)

# Create backend developer with specialization
backend_dev = AgentFactory.create_agent(
    agent_id=uuid4(),
    role="backend_developer",
    specialization="python_fastapi"
)
```

---

## Agent Lifecycle

### 1. Creation

```python
agent_id = uuid4()
agent = AgentFactory.create_agent(
    agent_id=agent_id,
    role="project_manager",
    llm_provider="openai",
    llm_model="gpt-4o"
)
```

**What Happens**:
1. AgentFactory validates role
2. Loads system prompt from `roles/project_manager/default_prompt.md`
3. Creates `AgentConfig` object
4. Instantiates `AgnoProjectManagerAgent`
5. Stores in factory registry
6. **Session NOT created yet** (lazy loading)

### 2. First Message (Session Creation)

```python
response = await agent.process_message("Hello")
```

**What Happens**:
1. Agno detects no session exists
2. Creates new session in PostgreSQL
3. Generates unique `session_id`
4. Stores message in session
5. Calls LLM with message
6. Stores response in session
7. Returns response

### 3. Subsequent Messages (Session Reuse)

```python
response = await agent.process_message("Continue")
```

**What Happens**:
1. Agno uses existing `session_id`
2. Retrieves conversation history from PostgreSQL
3. Appends new message
4. Calls LLM with full history
5. Stores response
6. Returns response

### 4. Session Resumption

```python
# Later, in a new process/server
agent = AgentFactory.create_agent(
    agent_id=new_agent_id,  # Different agent ID
    role="project_manager",
    session_id=previous_session_id  # Resume session
)

response = await agent.process_message("What were we discussing?")
# Agent remembers entire conversation from session!
```

### 5. Cleanup

```python
# Remove agent from factory
AgentFactory.remove_agent(agent_id)

# Session persists in database even after agent removal
# Can be resumed anytime with same session_id
```

---

## Session Management

### Session Storage

Sessions are stored in PostgreSQL database managed by Agno:

```sql
-- Agno creates this table automatically
CREATE TABLE agno_sessions (
    session_id UUID PRIMARY KEY,
    agent_id UUID,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    conversation_history JSONB,  -- Full history
    metadata JSONB  -- Custom metadata
);
```

### Session Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│              Session Lifecycle (Agno-Managed)            │
└─────────────────────────────────────────────────────────┘

1. Agent Created
   ├─ agent_id generated
   └─ session_id = None (not created yet)

2. First process_message() call
   ├─ Agno creates session in PostgreSQL
   ├─ session_id generated
   ├─ First message stored
   └─ Response stored

3. Subsequent process_message() calls
   ├─ Agno retrieves session from PostgreSQL
   ├─ Appends message to history
   ├─ Calls LLM with full history
   └─ Stores response

4. Server Restart
   └─ Session survives in PostgreSQL ✅

5. Session Resumption (anytime)
   ├─ Create new agent with existing session_id
   └─ Full conversation history restored ✅

6. Session Expiry (optional)
   └─ Configure TTL in Agno settings
```

### Best Practices

#### ✅ DO:
- **Use session_id for multi-turn conversations**
- **Store session_id in your database** (link to user/task)
- **Resume sessions after server restart**
- **Pass session_id when creating related agents**

#### ❌ DON'T:
- **Don't delete sessions manually** (Agno manages them)
- **Don't assume session_id exists before first message**
- **Don't create multiple agents for same conversation** (reuse session_id)

---

## Message Bus Integration

All Agno agents are integrated with NATS JetStream message bus:

### Sending Messages

```python
# Point-to-point message
await agent.send_message(
    recipient_id=backend_dev_id,
    content="Implement user authentication",
    message_type="task_assignment",
    task_execution_id=execution_id,
    metadata={"priority": "high"}
)

# Broadcast message
await agent.broadcast_message(
    content="Daily standup starting now",
    message_type="standup",
    task_execution_id=execution_id
)
```

### Receiving Messages

Messages are retrieved via `MessageBus`:

```python
from backend.agents.communication.message_bus import get_message_bus

message_bus = get_message_bus()
messages = await message_bus.get_messages(agent_id)
```

### Message Persistence

- ✅ All messages stored in NATS JetStream
- ✅ Messages survive server restarts
- ✅ Configurable retention (default: 7 days)
- ✅ Message replay supported

---

## Production Deployment

### Environment Configuration

**`.env` file**:
```bash
# Database (required for Agno sessions)
DATABASE_URL=postgresql://user:pass@localhost:5432/agent_squad

# Message Bus (NATS is default)
MESSAGE_BUS=nats
NATS_URL=nats://localhost:4222
NATS_STREAM_NAME=agent-messages

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Agno Configuration (deprecated variable, always true)
USE_AGNO_AGENTS=true
```

### Docker Compose

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: agent_squad
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nats:
    image: nats:latest
    command: >
      -js
      -sd /data
    ports:
      - "4222:4222"
      - "8222:8222"
    volumes:
      - nats_data:/data

  backend:
    build: .
    depends_on:
      - postgres
      - nats
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/agent_squad
      NATS_URL: nats://nats:4222
      MESSAGE_BUS: nats
    ports:
      - "8000:8000"

volumes:
  postgres_data:
  nats_data:
```

### Production Checklist

- [ ] PostgreSQL database configured (for Agno sessions)
- [ ] NATS JetStream running (for message bus)
- [ ] LLM API keys configured (OpenAI/Anthropic)
- [ ] DATABASE_URL environment variable set
- [ ] NATS_URL environment variable set
- [ ] MESSAGE_BUS=nats (default)
- [ ] Database migrations run
- [ ] NATS stream created (auto-created on first use)
- [ ] Monitoring/logging configured
- [ ] Backup strategy for PostgreSQL

---

## Migration from Legacy

### What Was Removed?

**Deleted Files (13 total)**:
- `backend/agents/base_agent.py` (BaseSquadAgent class)
- 9 custom agent implementations (project_manager.py, tech_lead.py, etc.)
- `backend/agents/repository/` stub folder
- `test_agent_factory_agno.py` (dual-mode test)
- `convert_agents_to_agno.py` (conversion script)

**Total Code Removed**: ~4,685 lines

### What Changed?

**Updated Files (8 total)**:
1. `backend/agents/factory.py` - Simplified to Agno-only (411→331 lines)
2. `backend/services/agent_service.py` - Updated imports & methods
3. `backend/agents/communication/history_manager.py` - Fixed imports
4. `tests/test_mcp_agent_integration.py` - Uses AgnoSquadAgent
5. `tests/test_phase2_context.py` - Uses AgnoSquadAgent
6. `.env.example` - Marked USE_AGNO_AGENTS as deprecated
7. `backend/core/config.py` - Updated comment
8. Demo files (3) - Removed redundant env vars

### Migration Path

If you have existing code using `BaseSquadAgent`:

#### Before:
```python
from backend.agents.base_agent import BaseSquadAgent, AgentConfig

agent = BaseSquadAgent(config)
```

#### After:
```python
from backend.agents.factory import AgentFactory
from uuid import uuid4

agent = AgentFactory.create_agent(
    agent_id=uuid4(),
    role="project_manager",
    llm_provider="openai",
    llm_model="gpt-4o"
)
```

---

## Best Practices

### 1. Session Management

```python
# ✅ GOOD: Store session_id for multi-turn conversations
async def process_ticket(ticket_id: str):
    # Get or create session for this ticket
    session_id = await get_session_for_ticket(ticket_id)

    agent = AgentFactory.create_agent(
        agent_id=uuid4(),
        role="project_manager",
        session_id=session_id  # Resume conversation
    )

    response = await agent.process_message("Continue analysis")
    return response

# ❌ BAD: New session every time (loses context)
async def process_ticket(ticket_id: str):
    agent = AgentFactory.create_agent(
        agent_id=uuid4(),
        role="project_manager"
        # No session_id - starts fresh every time!
    )
    response = await agent.process_message("Analyze ticket")
    return response
```

### 2. Agent Reuse

```python
# ✅ GOOD: Reuse agent instance within same request
async def handle_request():
    agent = AgentFactory.create_agent(agent_id, role="project_manager")

    response1 = await agent.process_message("Question 1")
    response2 = await agent.process_message("Question 2")
    response3 = await agent.process_message("Question 3")

    return [response1, response2, response3]

# ❌ BAD: Create new agent for each message
async def handle_request():
    agent1 = AgentFactory.create_agent(uuid4(), role="project_manager")
    response1 = await agent1.process_message("Question 1")

    agent2 = AgentFactory.create_agent(uuid4(), role="project_manager")
    response2 = await agent2.process_message("Question 2")
    # Different agents = no shared context!
```

### 3. Error Handling

```python
# ✅ GOOD: Handle errors gracefully
try:
    agent = AgentFactory.create_agent(
        agent_id=uuid4(),
        role="project_manager"
    )
    response = await agent.process_message("Hello")
except ValueError as e:
    # Invalid role or configuration
    logger.error(f"Agent creation failed: {e}")
except Exception as e:
    # LLM API error, database error, etc.
    logger.error(f"Agent processing failed: {e}")
```

### 4. Cleanup

```python
# ✅ GOOD: Clean up agents when done
async def long_running_task():
    agent_id = uuid4()
    agent = AgentFactory.create_agent(agent_id, role="project_manager")

    try:
        response = await agent.process_message("Task")
        return response
    finally:
        # Remove from factory registry (session persists in DB)
        AgentFactory.remove_agent(agent_id)
```

---

## Troubleshooting

### Agent Creation Fails

**Error**: `ValueError: Unsupported role: ...`

**Solution**: Check role is in supported list:
```python
from backend.agents.factory import AgentFactory
print(AgentFactory.get_supported_roles())
# ['project_manager', 'tech_lead', 'backend_developer', ...]
```

### Session Not Persisting

**Error**: Agent forgets conversation after restart

**Solution**: Check:
1. PostgreSQL database is running
2. DATABASE_URL is configured
3. Agno has access to database
4. You're passing same `session_id` when resuming

### Message Bus Not Working

**Error**: Messages not being received

**Solution**: Check:
1. NATS is running (`docker ps | grep nats`)
2. MESSAGE_BUS=nats in environment
3. NATS_URL is correct
4. NATS stream created (auto-created on first use)

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'backend.agents.base_agent'`

**Solution**: Legacy import! Update to:
```python
from backend.agents.agno_base import AgnoSquadAgent
from backend.agents.factory import AgentFactory
```

---

## Resources

### Documentation
- **Main README**: `README.md`
- **Agents Guide**: `backend/agents/CLAUDE.md`
- **Specialized Agents**: `backend/agents/specialized/CLAUDE.md`
- **Communication**: `backend/agents/communication/CLAUDE.md`
- **This Guide**: `AGNO_ARCHITECTURE_GUIDE.md`

### Code Examples
- **Verification Script**: `verify_agno_only.py`
- **Agent Conversations Demo**: `demo_agent_conversations.py`
- **Hierarchical Squad Demo**: `demo_hierarchical_squad.py`

### External Resources
- **Agno Framework**: https://docs.agno.com
- **NATS JetStream**: https://docs.nats.io/nats-concepts/jetstream

---

## Summary

### Key Takeaways

1. ✅ **All agents use Agno** - No custom agents remain
2. ✅ **Sessions persist** - Conversations survive restarts
3. ✅ **Memory managed** - Agno handles history automatically
4. ✅ **NATS by default** - Distributed message bus
5. ✅ **Production-ready** - Battle-tested architecture

### Quick Start

```python
from backend.agents.factory import AgentFactory
from uuid import uuid4

# Create agent
agent = AgentFactory.create_agent(
    agent_id=uuid4(),
    role="project_manager",
    llm_provider="openai",
    llm_model="gpt-4o"
)

# Process message (session created automatically)
response = await agent.process_message("Hello!")

# Resume later
agent2 = AgentFactory.create_agent(
    agent_id=uuid4(),
    role="project_manager",
    session_id=agent.session_id  # Resume same conversation
)
```

### Next Steps

1. Read the [Agents Guide](backend/agents/CLAUDE.md)
2. Run `verify_agno_only.py` to test your setup
3. Try `demo_agent_conversations.py` to see agents in action
4. Deploy to production with PostgreSQL + NATS

---

**Generated**: October 23, 2025
**Version**: 1.0
**Status**: Production-Ready ✅
