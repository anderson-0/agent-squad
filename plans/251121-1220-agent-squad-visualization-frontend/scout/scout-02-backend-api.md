# Backend API Architecture

## Overview

FastAPI-based REST API with comprehensive endpoints for managing AI agent squads, task executions, and real-time communication. The API follows RESTful conventions with versioned routes (`/api/v1/*`), JWT authentication, and Server-Sent Events (SSE) for real-time updates.

## Application Entry Point

**Main App**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/core/app.py`
- FastAPI app with lifespan management
- Middleware: CORS, GZip, Security Headers, Rate Limiting, Request Logging
- Metrics: Prometheus metrics at `/metrics` (if enabled)
- Background Jobs: Inngest integration at `/api/inngest`
- API Prefix: `/api/v1`

**Routes Loaded**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/router.py`

---

## Core API Routes

### 1. Authentication (`/api/v1/auth`)

**File**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/auth.py`

**Endpoints**:
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with email/password (returns JWT tokens)
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user profile
- `PUT /auth/me` - Update user profile
- `POST /auth/change-password` - Change password
- `POST /auth/password-reset/request` - Request password reset
- `POST /auth/password-reset/confirm` - Confirm password reset
- `POST /auth/verify-email` - Verify email address
- `POST /auth/verify-email/resend` - Resend verification email
- `GET /auth/status` - Check authentication status
- `POST /auth/logout` - Logout (client-side token deletion)

**Schema**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/schemas/auth.py`

**Authentication Method**: JWT Bearer tokens
- Access Token: 30 minutes (default)
- Refresh Token: 7 days (default)
- Algorithm: HS256

---

### 2. Squads (`/api/v1/squads`)

**File**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/squads.py`

**Endpoints**:
- `POST /squads` - Create new squad
- `GET /squads` - List user's squads (with filters: organization_id, status, pagination)
- `GET /squads/{squad_id}` - Get squad details
- `GET /squads/{squad_id}/details` - Get squad with all agents
- `GET /squads/{squad_id}/cost` - Get squad cost estimate
- `PUT /squads/{squad_id}` - Update squad
- `PATCH /squads/{squad_id}/status` - Update squad status (active/paused/archived)
- `DELETE /squads/{squad_id}` - Delete squad permanently

**Schema**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/schemas/squad.py`

**Key Models**:
- `SquadCreate` - Create squad request
- `SquadUpdate` - Update squad request
- `SquadResponse` - Squad details response
- `SquadWithAgents` - Squad with all members
- `SquadCostEstimate` - Cost breakdown by LLM model

**Features**:
- Caching via `squad_cache` (Redis-backed)
- Organization filtering
- Status filtering (active/paused/archived)
- Pagination support (skip/limit)
- Cost estimation per squad

---

### 3. Squad Members / Agents (`/api/v1/squad-members`)

**File**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/squad_members.py`

**Endpoints**:
- `POST /squad-members` - Add agent to squad
- `GET /squad-members` - List squad members (filters: squad_id, active_only, role)
- `GET /squad-members/{member_id}` - Get member details
- `GET /squad-members/{member_id}/config` - Get member with full config
- `GET /squad-members/by-role/{role}` - Get members by role
- `GET /squad-members/squad/{squad_id}/composition` - Get squad composition summary
- `PUT /squad-members/{member_id}` - Update member
- `PATCH /squad-members/{member_id}/deactivate` - Deactivate member
- `PATCH /squad-members/{member_id}/reactivate` - Reactivate member
- `DELETE /squad-members/{member_id}` - Delete member permanently

**Schema**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/schemas/squad_member.py`

**Key Fields**:
- `role` - Agent role (project_manager, tech_lead, backend_developer, etc.)
- `specialization` - Agent specialization (optional)
- `llm_provider` - LLM provider (openai, anthropic, groq)
- `llm_model` - LLM model (gpt-4, claude-3-opus, etc.)
- `config` - Agent configuration (JSON)
- `is_active` - Active status

**Features**:
- Role-based filtering
- Squad composition analysis
- Cache invalidation on updates
- Activation/deactivation support

---

### 4. Task Executions (`/api/v1/task-executions`)

**File**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/task_executions.py`

**Endpoints**:
- `POST /task-executions` - Start task execution
- `GET /task-executions` - List executions (filters: squad_id, status, pagination)
- `GET /task-executions/{execution_id}` - Get execution details
- `GET /task-executions/{execution_id}/summary` - Get execution summary
- `GET /task-executions/{execution_id}/messages` - Get execution messages
- `GET /task-executions/{execution_id}/logs` - Get execution logs
- `PATCH /task-executions/{execution_id}/status` - Update status
- `POST /task-executions/{execution_id}/complete` - Mark as completed
- `POST /task-executions/{execution_id}/error` - Report error
- `POST /task-executions/{execution_id}/intervention` - Human intervention
- `POST /task-executions/{execution_id}/cancel` - Cancel execution
- `POST /task-executions/{execution_id}/logs` - Add log entry
- `POST /task-executions/{execution_id}/start-async` - Start async execution (Inngest)

**Schema**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/schemas/task_execution.py`

**Key Models**:
- `TaskExecutionCreate` - Start execution request
- `TaskExecutionResponse` - Execution details
- `TaskExecutionWithMessages` - Execution with agent messages
- `TaskExecutionSummary` - Execution summary with metrics
- `HumanIntervention` - Human intervention request

**Execution States**:
- `queued` - Waiting to start
- `in_progress` - Currently executing
- `blocked` - Waiting for human intervention
- `completed` - Successfully finished
- `failed` - Failed with error
- `cancelled` - Cancelled by user

**Features**:
- Real-time status tracking
- Log aggregation (info/warning/error)
- Message filtering by type
- Human intervention support
- Async execution via Inngest (instant response)
- Cache invalidation on status changes

---

### 5. Agent Messages (`/api/v1/agent-messages`)

**Schema**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/schemas/agent_message.py`

**Message Types** (Structured A2A Protocol):
- `task_assignment` - PM assigns task to agent
- `status_request` - Request status update
- `status_update` - Status update response
- `question` - Question from agent
- `answer` - Answer to question
- `human_intervention_required` - Escalation to human
- `code_review_request` - Request code review
- `code_review_response` - Code review result
- `task_completion` - Task completed notification
- `standup` - Daily standup update

**Key Models**:
- `AgentMessageCreate` - Create message
- `AgentMessageResponse` - Message details
- `TaskAssignment` - Task assignment payload
- `StatusUpdate` - Status update payload
- `Question` - Question payload
- `Answer` - Answer payload
- `HumanInterventionRequired` - Escalation payload
- `CodeReviewRequest` - Code review request
- `CodeReviewResponse` - Code review response
- `TaskCompletion` - Completion notification
- `Standup` - Standup update

**Features**:
- Structured message protocol
- Broadcast messages (recipient_id = null)
- Direct messages (recipient_id = specific agent)
- Message metadata (JSON)
- Urgency levels (low/normal/high)
- Confidence levels (low/medium/high)

---

### 6. Server-Sent Events / Real-Time (`/api/v1/sse`)

**File**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/sse.py`

**Endpoints**:
- `GET /sse/execution/{execution_id}` - Stream execution updates
- `GET /sse/squad/{squad_id}` - Stream squad updates
- `GET /sse/stats` - Get SSE connection stats

**SSE Event Types**:
- `connected` - Initial connection
- `message` - New agent message
- `status_update` - Execution status changed
- `log` - New log entry
- `progress` - Progress update
- `error` - Error occurred
- `completed` - Execution completed
- `execution_started` - New execution started
- `execution_completed` - Execution completed
- `heartbeat` - Keep-alive (every 15 seconds)

**Headers**:
- `Cache-Control: no-cache`
- `Connection: keep-alive`
- `X-Accel-Buffering: no` (disable nginx buffering)

**Usage Example**:
```javascript
const eventSource = new EventSource('/api/v1/sse/execution/{id}', {
    headers: { 'Authorization': 'Bearer <token>' }
});

eventSource.addEventListener('message', (e) => {
    const data = JSON.parse(e.data);
    console.log('New message:', data);
});

eventSource.addEventListener('status_update', (e) => {
    const data = JSON.parse(e.data);
    console.log('Status changed:', data);
});
```

---

## Additional Endpoints (Available)

The router includes additional endpoints not detailed above:

**File**: `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/router.py`

Additional routers loaded:
- `routing_rules` - Routing rule management
- `conversations` - Conversation management
- `templates` - Squad templates
- `analytics` - Analytics and metrics
- `multi_turn_conversations` - Multi-turn conversation support
- `workflows` - Workflow management
- `pm_guardian` - PM Guardian features
- `kanban` - Kanban board management
- `discovery` - Discovery features
- `branching` - Conversation branching
- `advanced_guardian` - Advanced guardian features
- `intelligence` - Intelligence features
- `ml_detection` - ML detection
- `mcp` - Model Context Protocol
- `health` - Enhanced health checks
- `costs` - Cost tracking
- `agent_pool` - Agent pool monitoring
- `cache_metrics` - Cache performance metrics
- `task_monitoring` - Task lifecycle monitoring

---

## Authentication & Authorization

**Auth Method**: JWT Bearer Token

**Protected Endpoints**: All endpoints require authentication via `Depends(get_current_user)`

**Authorization Pattern**:
1. User must be authenticated (valid JWT token)
2. Resource ownership verified (e.g., squad belongs to user)
3. Action performed

**Example Flow**:
```python
async def get_squad(
    squad_id: UUID,
    current_user: User = Depends(get_current_user),  # Verify user
    db: AsyncSession = Depends(get_db)
):
    squad = await SquadService.get_squad(db, squad_id)
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)  # Verify ownership
    return squad
```

---

## WebSocket Endpoints

**Status**: SSE (Server-Sent Events) used instead of WebSocket

**Rationale**: SSE provides simpler unidirectional streaming (server to client) which is sufficient for status updates, logs, and messages. WebSocket would be overkill for current use cases.

**Future Consideration**: WebSocket could be added for bidirectional real-time communication if needed (e.g., live collaboration features).

---

## Request/Response Patterns

### Pagination
```python
GET /squads?skip=0&limit=100
GET /task-executions?skip=0&limit=50
```

### Filtering
```python
GET /squads?organization_id={uuid}&status=active
GET /task-executions?squad_id={uuid}&status=in_progress
GET /squad-members?squad_id={uuid}&active_only=true&role=backend_developer
```

### Error Responses
```json
{
  "detail": "Squad {id} not found"
}
```

### Success Responses
```json
{
  "id": "uuid",
  "name": "Squad Name",
  "status": "active",
  ...
}
```

---

## Caching Strategy

**Cache Layer**: Redis-backed caching for hot paths

**Cached Entities**:
- `squad_cache` - Squad details, members, organization squads
- `task_cache` - Task executions, execution status

**Cache Invalidation**:
- On create: No cache entry yet
- On update: Invalidate specific entity + related entities
- On delete: Invalidate entity + related entities

**Example**:
```python
# Get with cache
squad_cache = get_squad_cache()
squad = await squad_cache.get_squad_by_id(db, squad_id)

# Invalidate on update
await squad_cache.invalidate_squad(squad_id, org_id)
```

---

## Background Jobs (Inngest)

**Endpoint**: `/api/inngest`

**Workflows**:
- `execute_agent_workflow` - Execute multi-agent workflow
- `execute_single_agent_workflow` - Execute single agent workflow

**Usage**:
```python
POST /task-executions/{execution_id}/start-async
```

**Benefits**:
- Instant API response (< 100ms)
- Durable execution (survives crashes)
- Automatic retries on failure
- Background processing

---

## Health Checks

**Endpoints**:
- `GET /health` - Simple health check
- `GET /api/v1/health/detailed` - Detailed health check
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe

**Health Check Components**:
- Database connectivity
- Redis connectivity
- Agno framework status
- API responsiveness

---

## Key Files Summary

**Core Application**:
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/core/app.py` - FastAPI app
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/router.py` - API router
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/core/auth.py` - Authentication

**Primary Endpoints**:
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/auth.py`
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/squads.py`
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/squad_members.py`
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/task_executions.py`
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/api/v1/endpoints/sse.py`

**Schemas**:
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/schemas/auth.py`
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/schemas/squad.py`
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/schemas/squad_member.py`
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/schemas/task_execution.py`
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/schemas/agent_message.py`

---

## Frontend Integration Points

**Authentication Flow**:
1. `POST /auth/login` - Get JWT tokens
2. Store tokens in localStorage/sessionStorage
3. Include `Authorization: Bearer <token>` in all requests
4. Use `POST /auth/refresh` to refresh expired tokens

**Squad Management Flow**:
1. `GET /squads` - List user's squads
2. `POST /squads` - Create new squad
3. `GET /squads/{id}/details` - Get squad with agents
4. `POST /squad-members` - Add agents to squad

**Task Execution Flow**:
1. `POST /task-executions` - Start task
2. `GET /sse/execution/{id}` - Subscribe to real-time updates
3. Listen for SSE events: `message`, `status_update`, `log`, `completed`
4. `GET /task-executions/{id}/messages` - Get message history
5. `POST /task-executions/{id}/intervention` - Provide human input if needed

**Real-Time Updates**:
- Use SSE for server-to-client streaming
- Fallback to polling if SSE not available
- Heartbeat every 15 seconds to keep connection alive

---

## API Design Patterns

**RESTful Conventions**:
- `GET` - Read operations
- `POST` - Create operations
- `PUT` - Full update operations
- `PATCH` - Partial update operations
- `DELETE` - Delete operations

**Response Models**:
- All responses use Pydantic models
- Automatic validation and serialization
- OpenAPI schema generation

**Error Handling**:
- HTTPException for standard errors
- 404 for not found
- 401 for unauthorized
- 403 for forbidden
- 400 for bad request
- 500 for internal server error

**Dependency Injection**:
- `Depends(get_db)` - Database session
- `Depends(get_current_user)` - Current user
- `Depends(get_squad_cache)` - Cache instance

---

## Performance Considerations

**Database**:
- Async database operations (asyncpg)
- Connection pooling (5 + 10 overflow)
- Caching for hot paths (Redis)

**API**:
- GZip compression for responses
- Rate limiting in production
- Request logging for debugging

**Real-Time**:
- SSE for efficient server-to-client streaming
- Heartbeat to prevent timeout
- Automatic reconnection on client side

---

## Next Steps for Frontend

**Priority 1 - Authentication**:
- Implement login form
- Store JWT tokens
- Add token refresh logic
- Create auth context/provider

**Priority 2 - Squad Dashboard**:
- List squads (`GET /squads`)
- Create squad form (`POST /squads`)
- Squad detail view (`GET /squads/{id}/details`)

**Priority 3 - Agent Management**:
- Add agent form (`POST /squad-members`)
- Agent list view (`GET /squad-members`)
- Agent configuration editor

**Priority 4 - Task Execution**:
- Task execution UI
- Real-time updates (SSE)
- Message history display
- Human intervention modal

**Priority 5 - Real-Time Updates**:
- SSE client implementation
- Event handling
- Reconnection logic
- Fallback to polling

