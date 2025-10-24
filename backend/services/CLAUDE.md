# Services Module

## Overview

The `services/` module contains business logic layer services that handle complex operations between API endpoints and database models. Following Clean Architecture principles, services encapsulate domain logic, enforce business rules, and coordinate between different parts of the system.

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Services Layer                             │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐                                            │
│  │  API Endpoints │  ← Thin controllers (routing only)         │
│  └───────┬────────┘                                            │
│          │                                                      │
│          ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │             Business Logic Services                       │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  - Validation                                            │  │
│  │  - Business Rules                                        │  │
│  │  - Orchestration                                         │  │
│  │  - Error Handling                                        │  │
│  └───────┬──────────────────────────────────┬───────────────┘  │
│          │                                  │                   │
│          ▼                                  ▼                   │
│  ┌───────────────┐                ┌─────────────────┐         │
│  │   Database    │                │  External APIs  │         │
│  │    Models     │                │  (LLM, NATS)    │         │
│  └───────────────┘                └─────────────────┘         │
└────────────────────────────────────────────────────────────────┘
```

## Key Files

### 1. `agent_service.py` - Agent Management 🤖 ⭐

**Purpose**: Business logic for agent (Squad Member) CRUD operations and Agno agent instantiation

**Key Responsibilities**:
- Create/update/delete squad members
- Validate agent roles and configurations
- Load system prompts from files
- Instantiate Agno agents with proper configuration
- Manage agent lifecycle

**Important Methods**:

#### `create_squad_member()`
Location: `agent_service.py:24`

```python
squad_member = await AgentService.create_squad_member(
    db=db,
    squad_id=squad_id,
    role="backend_developer",
    specialization="python_fastapi",
    llm_provider="openai",
    llm_model="gpt-4o-mini",
    config={"temperature": 0.7}
)
```

**Validation**:
- Squad must exist and be active
- Role must be valid (9 roles supported)
- System prompt loaded from `/roles/{role}/` directory

**Supported Roles**:
1. `project_manager`
2. `tech_lead`
3. `backend_developer`
4. `frontend_developer`
5. `qa_tester` (alias: `tester`)
6. `solution_architect`
7. `devops_engineer`
8. `ai_engineer`
9. `designer`

---

#### `get_or_create_agent()` ⭐ AGNO-POWERED
Location: `agent_service.py:178`

```python
# Get Agno agent instance
agent = await AgentService.get_or_create_agent(
    db=db,
    squad_member_id=member_id
)

# Agent is ready to use
response = await agent.process_message("Hello!")
```

**What It Does**:
1. Retrieves squad member from database
2. Validates member is active
3. Extracts configuration (temperature, max_tokens)
4. Creates Agno agent using `AgentFactory.create_agent()`
5. Returns initialized agent ready for messages

**Agno Integration**:
- Uses `AgentFactory.create_agent()` (Agno-only)
- Each agent backed by Agno framework
- Persistent sessions in PostgreSQL
- Automatic conversation history

---

#### Other Operations

**Get Squad Member**:
```python
member = await AgentService.get_squad_member(db, member_id)
```

**Get All Squad Members**:
```python
members = await AgentService.get_squad_members(
    db=db,
    squad_id=squad_id,
    active_only=True  # Default
)
```

**Get Member by Role**:
```python
pm = await AgentService.get_squad_member_by_role(
    db=db,
    squad_id=squad_id,
    role="project_manager"
)
```

**Update Member Configuration**:
```python
member = await AgentService.update_squad_member(
    db=db,
    member_id=member_id,
    llm_provider="anthropic",
    llm_model="claude-3-5-sonnet-20240229",
    config={"temperature": 0.8}
)
```

**Deactivate/Reactivate**:
```python
# Deactivate (soft delete)
await AgentService.deactivate_squad_member(db, member_id)

# Reactivate
await AgentService.reactivate_squad_member(db, member_id)
```

**Delete (Permanent)**:
```python
await AgentService.delete_squad_member(db, member_id)
```

**Squad Composition Summary**:
```python
composition = await AgentService.get_squad_composition(db, squad_id)
# Returns:
# {
#     "squad_id": "...",
#     "total_members": 5,
#     "active_members": 5,
#     "roles": {"project_manager": 1, "backend_developer": 2, ...},
#     "llm_providers": {"openai": 3, "anthropic": 2},
#     "members": [...]
# }
```

**Business Rules**:
1. Squad must exist before adding members
2. Only one Project Manager per squad (recommended)
3. Members can be deactivated (soft delete) or deleted (permanent)
4. System prompts automatically loaded from `/roles/{role}/` files
5. Agent instances created on-demand (not stored)
6. Agno is the ONLY agent framework (no custom agents)

---

### 2. `auth_service.py` - Authentication 🔒

**Purpose**: User authentication, authorization, and session management

**Key Responsibilities**:
- User registration and login
- Password hashing (bcrypt)
- JWT token generation (access + refresh)
- Token verification
- User session management

**Key Methods**:

```python
# Register user
user = await AuthService.register_user(
    db=db,
    email="user@example.com",
    password="SecurePassword123",
    name="John Doe"
)

# Login
auth_result = await AuthService.login(
    db=db,
    email="user@example.com",
    password="SecurePassword123"
)
# Returns: {"access_token": "...", "refresh_token": "...", "user": {...}}

# Verify token
payload = await AuthService.verify_access_token(token)

# Refresh access token
new_tokens = await AuthService.refresh_access_token(refresh_token)

# Get current user
user = await AuthService.get_current_user(db, user_id)
```

**Security Features**:
- Bcrypt password hashing (cost factor: 12)
- JWT with HS256 algorithm
- Access token: 30 minutes (default)
- Refresh token: 7 days (default)
- Email uniqueness enforced

---

### 3. `conversation_service.py` - Multi-Turn Conversations 💬 ⭐

**Purpose**: Manage multi-turn conversations between users and agents with context persistence

**Key Features**:
- User-to-agent conversations
- Agent-to-agent conversations
- Conversation state tracking
- Context persistence
- Routing rules (which agent handles what)

**Key Methods**:

#### User-Agent Conversations
```python
# Start conversation
conversation = await ConversationService.create_conversation(
    db=db,
    squad_id=squad_id,
    user_id=user_id,
    initial_message="Build me a user authentication system"
)

# Send message
response = await ConversationService.send_user_message(
    db=db,
    conversation_id=conversation.id,
    user_id=user_id,
    content="Use JWT for tokens"
)

# Get conversation history
history = await ConversationService.get_conversation_history(
    db=db,
    conversation_id=conversation.id,
    limit=50
)
```

#### Agent-Agent Conversations
```python
# Send message between agents
await ConversationService.send_agent_message(
    db=db,
    conversation_id=conversation.id,
    sender_agent_id=backend_dev_id,
    recipient_agent_id=tech_lead_id,
    content="Ready for code review"
)
```

#### Conversation State Management
```python
# Update state
await ConversationService.update_conversation_state(
    db=db,
    conversation_id=conversation.id,
    state="active"  # active, paused, completed, archived
)

# Close conversation
await ConversationService.close_conversation(
    db=db,
    conversation_id=conversation.id
)
```

**States**:
- `active`: Ongoing conversation
- `paused`: Temporarily paused
- `completed`: Successfully completed
- `archived`: Archived for reference

**Routing Rules**:
- Rules determine which agent handles specific message types
- Supports pattern matching on message content
- Can route to specific roles or agents

---

### 4. `squad_analytics_service.py` - Performance Analytics 📊

**Purpose**: Track and analyze squad performance metrics

**Key Metrics**:
- Task completion rate
- Average completion time
- Agent utilization
- Success rate per agent
- Cost per task
- Token usage

**Key Methods**:

```python
# Get squad performance
performance = await SquadAnalyticsService.get_squad_performance(
    db=db,
    squad_id=squad_id,
    start_date=datetime.utcnow() - timedelta(days=30),
    end_date=datetime.utcnow()
)
# Returns:
# {
#     "total_tasks": 150,
#     "completed_tasks": 145,
#     "failed_tasks": 5,
#     "completion_rate": 96.7,
#     "avg_completion_time_seconds": 1234,
#     "total_cost_usd": 45.67
# }

# Get agent performance
agent_stats = await SquadAnalyticsService.get_agent_performance(
    db=db,
    agent_id=agent_id,
    start_date=start,
    end_date=end
)

# Get cost analysis
cost = await SquadAnalyticsService.get_cost_analysis(
    db=db,
    squad_id=squad_id,
    start_date=start,
    end_date=end
)
```

**Use Cases**:
- Dashboard metrics
- Performance reports
- Cost optimization
- Agent efficiency tracking
- Squad capacity planning

---

### 5. `squad_service.py` - Squad Management 👥

**Purpose**: Business logic for squad CRUD operations

**Key Methods**:

```python
# Create squad
squad = await SquadService.create_squad(
    db=db,
    name="Backend Team Alpha",
    organization_id=org_id,
    description="Backend development squad"
)

# Get squad with members
squad = await SquadService.get_squad(
    db=db,
    squad_id=squad_id,
    load_members=True  # Eager load members
)

# Update squad
squad = await SquadService.update_squad(
    db=db,
    squad_id=squad_id,
    name="Backend Team Alpha v2",
    status="active"
)

# Deactivate squad
await SquadService.deactivate_squad(db, squad_id)

# List organization squads
squads = await SquadService.list_organization_squads(
    db=db,
    organization_id=org_id,
    active_only=True
)
```

**Squad States**:
- `active`: Squad is operational
- `inactive`: Squad is paused
- `archived`: Squad is archived

**Business Rules**:
1. Squad must have a name
2. Squad belongs to an organization
3. Inactive squads cannot execute tasks
4. Archived squads are read-only

---

### 6. `sse_service.py` - Real-Time Updates 📡

**Purpose**: Server-Sent Events (SSE) for real-time streaming of execution updates

**Architecture**:
- Per-execution subscriptions
- Per-squad subscriptions
- Heartbeat to keep connections alive
- Automatic reconnection support

**Key Components**:

#### SSEConnectionManager
Global singleton managing all SSE connections.

```python
from backend.services.sse_service import sse_manager

# Subscribe to execution (in FastAPI endpoint)
@app.get("/executions/{execution_id}/stream")
async def stream_execution(
    execution_id: UUID,
    user_id: UUID = Depends(get_current_user)
):
    return StreamingResponse(
        sse_manager.subscribe_to_execution(execution_id, user_id),
        media_type="text/event-stream"
    )

# Subscribe to squad (all executions)
@app.get("/squads/{squad_id}/stream")
async def stream_squad(
    squad_id: UUID,
    user_id: UUID = Depends(get_current_user)
):
    return StreamingResponse(
        sse_manager.subscribe_to_squad(squad_id, user_id),
        media_type="text/event-stream"
    )
```

#### Broadcasting Events
```python
# Broadcast to execution subscribers
await sse_manager.broadcast_to_execution(
    execution_id=execution_id,
    event="status_update",
    data={"status": "in_progress", "progress": 50}
)

# Broadcast to squad subscribers
await sse_manager.broadcast_to_squad(
    squad_id=squad_id,
    event="new_execution",
    data={"execution_id": str(execution_id)}
)
```

**Event Types**:
- `connected`: Client connected
- `heartbeat`: Keep-alive ping
- `status_update`: Execution status changed
- `log`: New log entry
- `agent_message`: Agent sent message
- `completed`: Execution completed
- `error`: Error occurred

**SSE Message Format**:
```
event: status_update
data: {"execution_id": "...", "status": "in_progress", "timestamp": "..."}

event: heartbeat
data: {"timestamp": "2025-10-23T12:34:56Z"}
```

**Features**:
- Automatic heartbeat every 15 seconds
- Queue size: 100 messages per connection
- Timeout handling: 1 second per broadcast
- Graceful connection cleanup
- Connection statistics

**Connection Statistics**:
```python
stats = sse_manager.get_stats()
# Returns:
# {
#     "total_connections": 15,
#     "execution_streams": 10,
#     "squad_streams": 5,
#     "connections_by_execution": {"exec-id": 3, ...},
#     "connections_by_squad": {"squad-id": 2, ...}
# }
```

**Business Rules**:
1. Connections automatically cleaned up on disconnect
2. Failed broadcasts don't break execution
3. Heartbeat prevents connection timeout
4. Multiple clients can subscribe to same execution

---

### 7. `task_execution_service.py` - Task Execution Lifecycle 🚀

**Purpose**: Manage complete task execution lifecycle with status tracking, logging, and error handling

**Key Responsibilities**:
- Start/stop task executions
- Track execution status
- Log execution events
- Handle errors and failures
- Calculate execution metrics
- Integrate with SSE for real-time updates

**Execution Lifecycle**:
```
START → pending → in_progress → completed/failed
                      ↓
                   blocked (can resume)
```

**Key Methods**:

#### Start Execution
```python
execution = await TaskExecutionService.start_task_execution(
    db=db,
    task_id=task_id,
    squad_id=squad_id,
    execution_metadata={"priority": "high"}
)
# Returns TaskExecution with status "pending"
# Broadcasts SSE event "execution_started"
```

#### Update Status
```python
execution = await TaskExecutionService.update_execution_status(
    db=db,
    execution_id=execution_id,
    status="in_progress",  # pending | in_progress | completed | failed | blocked
    log_message="Agent started working on task"
)
# Automatically adds log entry
# Broadcasts SSE status_update event
```

#### Add Logs
```python
await TaskExecutionService.add_log(
    db=db,
    execution_id=execution_id,
    level="info",  # info | warning | error
    message="Backend API completed",
    metadata={"files_changed": 5}
)
# Broadcasts SSE log event
```

#### Complete Execution
```python
execution = await TaskExecutionService.complete_execution(
    db=db,
    execution_id=execution_id,
    result={
        "pr_url": "https://github.com/org/repo/pull/123",
        "tests_passing": True,
        "files_changed": ["src/auth.py", "tests/test_auth.py"]
    }
)
# Sets status to "completed"
# Calculates duration
# Updates task status
# Broadcasts SSE completed event
```

#### Handle Errors
```python
execution = await TaskExecutionService.handle_execution_error(
    db=db,
    execution_id=execution_id,
    error="LLM API timeout",
    error_metadata={
        "provider": "openai",
        "model": "gpt-4",
        "retry_count": 3
    }
)
# Sets status to "failed"
# Stores error details
# Updates task status
# Broadcasts SSE error event
```

#### Cancel Execution
```python
execution = await TaskExecutionService.cancel_execution(
    db=db,
    execution_id=execution_id,
    reason="User requested cancellation"
)
```

#### Get Execution Summary
```python
summary = await TaskExecutionService.get_execution_summary(
    db=db,
    execution_id=execution_id
)
# Returns:
# {
#     "id": "...",
#     "task_id": "...",
#     "squad_id": "...",
#     "status": "completed",
#     "started_at": "2025-10-23T10:00:00Z",
#     "completed_at": "2025-10-23T10:15:30Z",
#     "duration_seconds": 930,
#     "error_message": null,
#     "message_count": 25,
#     "log_count": 12,
#     "metadata": {...}
# }
```

#### Get Execution Messages
```python
messages = await TaskExecutionService.get_execution_messages(
    db=db,
    execution_id=execution_id,
    limit=100
)
```

**Business Rules**:
1. Only active squads can start executions
2. Status transitions are validated
3. All status changes logged automatically
4. SSE events broadcast for all state changes
5. Duration calculated automatically on completion
6. Failed broadcasts don't break operations

**Integration with SSE**:
Every major operation broadcasts SSE events:
- `execution_started`
- `status_update`
- `log`
- `completed`
- `error`

---

### 8. `template_service.py` - Template Management 📋

**Purpose**: Squad templates for quick setup of common team configurations

**Key Methods**:

```python
# Create template
template = await TemplateService.create_template(
    db=db,
    name="Full Stack Development Squad",
    description="Complete squad for full-stack projects",
    template_config={
        "roles": [
            {"role": "project_manager", "count": 1},
            {"role": "backend_developer", "count": 2},
            {"role": "frontend_developer", "count": 2},
            {"role": "qa_tester", "count": 1}
        ],
        "default_llm": {
            "provider": "openai",
            "model": "gpt-4o-mini"
        }
    }
)

# Apply template to create squad
squad = await TemplateService.apply_template(
    db=db,
    template_id=template_id,
    organization_id=org_id,
    squad_name="My New Squad"
)
# Automatically creates:
# - Squad
# - Squad members based on template roles
# - Loads system prompts
# - Configures LLMs

# List templates
templates = await TemplateService.list_templates(
    db=db,
    organization_id=org_id  # Optional: filter by org
)
```

**Pre-built Templates** (Examples):
- **Full Stack Squad**: PM, TL, 2 Backend, 2 Frontend, QA
- **Backend-Only Squad**: PM, TL, 3 Backend, QA
- **Microservices Squad**: PM, TL, 3 Backend, DevOps, QA
- **AI/ML Squad**: PM, TL, 2 AI Engineers, Backend, QA
- **Minimal Squad**: PM, Backend, Frontend, QA

---

## Common Patterns

### Service Layer Pattern

All services follow this pattern:

```python
class ExampleService:
    """Service for handling X operations"""

    @staticmethod
    async def operation_name(
        db: AsyncSession,
        # ... parameters
    ) -> ReturnType:
        """
        Operation description.

        Args:
            db: Database session
            ...

        Returns:
            Description

        Raises:
            HTTPException: When operation fails
        """
        # 1. Validate inputs
        # 2. Check permissions
        # 3. Execute business logic
        # 4. Update database
        # 5. Broadcast events (if needed)
        # 6. Return result
```

**Best Practices**:
1. All methods are static (services are stateless)
2. Database session passed as first parameter
3. Use async/await for all database operations
4. Raise `HTTPException` for API errors
5. Add logs for important operations
6. Broadcast SSE events for real-time updates
7. Use transactions for multi-step operations

---

## Error Handling

Services use FastAPI's `HTTPException` for errors:

```python
from fastapi import HTTPException, status

# Not found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Squad {squad_id} not found"
)

# Bad request
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail=f"Invalid role: {role}"
)

# Unauthorized
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials"
)

# Forbidden
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You don't have permission to access this squad"
)
```

---

## Testing Services

```python
import pytest
from backend.services.agent_service import AgentService
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_squad_member(db_session, squad):
    """Test creating a squad member"""
    member = await AgentService.create_squad_member(
        db=db_session,
        squad_id=squad.id,
        role="backend_developer",
        llm_provider="openai",
        llm_model="gpt-4o-mini"
    )

    assert member.id is not None
    assert member.role == "backend_developer"
    assert member.is_active == True

@pytest.mark.asyncio
async def test_get_or_create_agent(db_session, squad_member):
    """Test agent instantiation"""
    agent = await AgentService.get_or_create_agent(
        db=db_session,
        squad_member_id=squad_member.id
    )

    assert agent is not None
    assert hasattr(agent, 'process_message')
    assert agent.agent_id == squad_member.id
```

---

## Integration with Other Modules

### API Layer
Services called by API endpoints:
```python
@router.post("/squads/{squad_id}/members")
async def create_squad_member(
    squad_id: UUID,
    request: CreateMemberRequest,
    db: AsyncSession = Depends(get_db)
):
    # Thin controller - delegates to service
    return await AgentService.create_squad_member(
        db=db,
        squad_id=squad_id,
        role=request.role,
        ...
    )
```

### Agent Layer
Services instantiate agents:
```python
# Service creates Agno agent
agent = await AgentService.get_or_create_agent(db, member_id)

# Agent processes messages
response = await agent.process_message("Hello!")
```

### Message Bus
Services integrate with NATS/SSE:
```python
# Task execution service broadcasts SSE
await sse_manager.broadcast_to_execution(
    execution_id,
    "status_update",
    data
)
```

---

## Performance Considerations

### Database Queries
- Use `selectinload()` for eager loading relationships
- Add indexes on frequently queried fields
- Use pagination for large result sets
- Avoid N+1 queries

### Caching
Consider caching for:
- Squad member lists (changes infrequently)
- Templates (mostly static)
- Authentication tokens (short TTL)

### Async Operations
- All database operations are async
- Use `asyncio.gather()` for parallel operations
- Non-blocking SSE broadcasts

---

## Related Documentation

- See `../core/CLAUDE.md` for configuration
- See `../agents/CLAUDE.md` for agent architecture
- See `../models/` for database models
- See `../api/` for API endpoints
- See `../agents/agno_base.py` for Agno agent implementation
