# Agent-Squad Architecture Documentation

**Last Updated:** 2025-11-03
**Version:** 2.1 (discovery-driven workflows + Inngest Optimization)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Core Components](#core-components)
4. [Data Models](#data-models)
5. [Workflow System](#workflow-system)
6. [Agent System](#agent-system)
7. [Integration Layer](#integration-layer)
8. [API Architecture](#api-architecture)
9. [Infrastructure](#infrastructure)
10. [Security](#security)

---

## System Overview

Agent-Squad is a production-ready, multi-agent AI system that enables teams of specialized AI agents to collaborate on complex software development tasks. The system implements a discovery-driven workflow architecture that allows agents to dynamically discover, plan, and execute work.

### Key Characteristics

- **Multi-Agent Collaboration:** Teams of specialized agents (Backend Dev, Frontend Dev, QA Tester, etc.)
- **Discovery-Driven Workflows:** Agents discover opportunities and spawn tasks dynamically
- **Phase-Based Execution:** Workflows progress through Investigation → Building → Validation phases
- **Intelligent Monitoring:** PM-as-Guardian system monitors coherence and workflow health
- **Production Infrastructure:** NATS, PostgreSQL, Redis, Celery, Docker
- **MCP Integration:** Exposes capabilities via Model Context Protocol

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React/Next.js)                 │
│  - Kanban Board (Real-time)                                      │
│  - Analytics Dashboard                                           │
│  - Workflow Visualization                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/SSE
┌────────────────────────▼────────────────────────────────────────┐
│                    FastAPI Backend (API Pods)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Layer (REST + SSE)                                   │  │
│  │  - Workflows, Discovery, Branching, Intelligence          │  │
│  │  - Async Execution Endpoints (Inngest events)             │  │
│  └────────────────┬──────────────────────────────────────────┘  │
│                   │                                               │
│  ┌────────────────▼──────────────────────────────────────────┐  │
│  │  Orchestration Layer                                      │  │
│  │  - PhaseBasedWorkflowEngine                               │  │
│  │  - BranchingEngine                                        │  │
│  │  - DiscoveryEngine                                        │  │
│  │  - WorkflowIntelligence                                   │  │
│  └────────────────┬──────────────────────────────────────────┘  │
│                   │                                               │
│  ┌────────────────▼──────────────────────────────────────────┐  │
│  │  Services Layer                                           │  │
│  │  - AnalyticsService                                       │  │
│  │  - ML OpportunityDetector                                 │  │
│  │  - RAGService (Pinecone)                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ Send Events
                     ▼
         ┌─────────────────────┐
         │    Inngest Cloud    │ ◄─── NEW: Workflow Orchestration
         │  (Background Jobs)  │      Replaces: Celery
         └──────────┬──────────┘
                    │ Execute Workflows
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Background Workers (Scalable)                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Agent Layer (Agno Framework)                              │ │
│  │  - AgnoProjectManager (PM + Guardian)                      │ │
│  │  - Specialized Agents (Backend, Frontend, QA, etc.)        │ │
│  │  - AgentTaskSpawner                                        │ │
│  │  - Multi-step workflow execution (PM → Backend → QA)       │ │
│  └──────────────────┬─────────────────────────────────────────┘ │
└─────────────────────┼──────────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────────┐
    │                 │                     │
┌───▼────┐    ┌───────▼──────┐   ┌─────────▼─────┐
│PostgreSQL│   │     NATS     │   │     Redis     │
│          │   │  JetStream   │   │               │
│ Database │   │ Message Bus  │   │     Cache     │
│          │   │ (Agent Comm) │   │               │
└──────────┘   └──────────────┘   └───────────────┘
               ▲
               │ Agent-to-Agent Communication
               │ (UNCHANGED - still used for messaging)
```

### Key Changes in v2.1

**Added:**
- **Inngest Cloud**: Background workflow orchestration (replaces Celery)
- **Background Workers**: Scalable worker pods for async execution
- **Async Execution Endpoints**: API returns instantly, workflows run in background

**Unchanged:**
- **NATS JetStream**: Still handles agent-to-agent communication
- **Agent Layer**: Agents still communicate via NATS
- **Database/Redis**: No changes to data layer

---

## Core Components

### 1. Workflow Engine (`PhaseBasedWorkflowEngine`)

**Location:** `backend/agents/orchestration/phase_based_engine.py`

**Responsibilities:**
- Manage phase-based workflows (Investigation, Building, Validation)
- Handle dynamic task spawning by agents
- Manage task dependencies and blocking relationships
- Track task status and phase transitions
- Broadcast SSE events for real-time updates

**Key Methods:**
- `spawn_task()`: Create new dynamic tasks
- `get_tasks_for_execution()`: Retrieve tasks with eager loading
- `update_task_status()`: Update task status with validation
- `get_blocked_tasks()`: Identify blocked tasks efficiently

### 2. Discovery System

**Components:**
- **DiscoveryDetector** (`backend/agents/discovery/discovery_detector.py`)
  - Pattern-based discovery detection
  - Identifies optimizations, bugs, refactoring needs
- **DiscoveryEngine** (`backend/agents/discovery/discovery_engine.py`)
  - Context-aware discovery analysis
  - Value scoring and evaluation
  - Task suggestion generation
- **ML-Enhanced Discovery** (`backend/agents/discovery/ml_enhanced_discovery.py`)
  - ML-powered opportunity detection
  - Enhanced value prediction

**Flow:**
```
Agent Work → DiscoveryDetector → DiscoveryEngine → TaskSuggestions → Spawn Tasks
```

### 3. PM-as-Guardian System

**Components:**
- **CoherenceScorer** (`backend/agents/guardian/coherence_scorer.py`)
  - Calculates agent alignment with phases
  - Tracks phase, goal, quality, and task relevance
- **WorkflowHealthMonitor** (`backend/agents/guardian/workflow_health_monitor.py`)
  - Monitors overall workflow health
  - Detects anomalies (phase imbalance, blocking issues)
- **AdvancedAnomalyDetector** (`backend/agents/guardian/advanced_anomaly_detector.py`)
  - Detects phase drift, low-value tasks, stagnation
  - Identifies resource imbalance and communication gaps
- **RecommendationsEngine** (`backend/agents/guardian/recommendations_engine.py`)
  - Generates actionable recommendations
  - Prioritizes by urgency and impact

**Integration:**
- `AgnoProjectManager` orchestrates Guardian capabilities
- Tracks coherence metrics in `CoherenceMetrics` table
- Provides real-time monitoring and recommendations

### 4. Workflow Intelligence

**Component:** `WorkflowIntelligence` (`backend/agents/intelligence/workflow_intelligence.py`)

**Capabilities:**
- **Task Suggestions:** AI-powered recommendations based on workflow state
- **Outcome Predictions:** Predicts completion time and success probability
- **Task Optimization:** Reorders tasks for optimal completion

**Data Sources:**
- Guardian coherence scores
- Discovery opportunities
- Active branches
- Workflow health metrics

### 5. Branching System

**Component:** `BranchingEngine` (`backend/agents/branching/branching_engine.py`)

**Capabilities:**
- Create workflow branches from discoveries
- Manage branch lifecycle (active, merged, abandoned, completed)
- Link tasks to branches
- Merge/abandon branches with summaries

**Use Case:**
Agent discovers optimization opportunity → Creates branch → Spawns investigation tasks → Merges results back

### 6. ML-Based Detection

**Component:** `OpportunityDetector` (`backend/agents/ml/opportunity_detector.py`)

**Capabilities:**
- ML-powered opportunity detection (with pattern fallback)
- Task value prediction based on historical data
- Model training infrastructure (scikit-learn)

**Features:**
- Embedding model integration (OpenAI)
- Classification pipeline
- Graceful degradation if ML unavailable

### 7. MCP Integration

**Component:** `AgentSquadMCPServer` (`backend/integrations/mcp/servers/agent_squad_server.py`)

**MCP Tools Exposed:**
1. `spawn_task`: Spawn dynamic tasks
2. `check_workflow_health`: Get health metrics
3. `get_coherence_score`: Get agent coherence
4. `create_workflow_branch`: Create branches
5. `discover_opportunities`: Run discovery
6. `get_kanban_board`: Get board state

**Transport:** stdio (Model Context Protocol standard)

### 8. Analytics Service

**Component:** `AnalyticsService` (`backend/services/analytics_service.py`)

**Capabilities:**
- Calculate comprehensive workflow analytics
- Generate workflow graph data (nodes, edges, branches)
- Track agent performance
- Analyze coherence trends

---

## Data Models

### Core Models

#### `TaskExecution`
- Represents a main task/project execution
- Links to `Squad` and `Project`
- Has many `DynamicTask` instances
- Has many `WorkflowBranch` instances

#### `DynamicTask`
- Tasks spawned dynamically by agents
- Belongs to a `TaskExecution`
- Optional `WorkflowBranch` linkage
- Phase: `investigation`, `building`, or `validation`
- Status: `pending`, `in_progress`, `completed`, `failed`, `blocked`
- Supports blocking dependencies (many-to-many via `task_dependencies`)

#### `WorkflowBranch`
- Discovery-driven workflow branches
- Belongs to a `TaskExecution`
- Status: `active`, `merged`, `abandoned`, `completed`
- Tracks discovery origin and metadata

#### `CoherenceMetrics`
- Stores PM Guardian coherence scores
- Links to `TaskExecution` and `SquadMember` (agent)
- Tracks metrics over time for trend analysis

### Relationships

```
TaskExecution
  ├── dynamic_tasks (1:N)
  ├── workflow_branches (1:N)
  └── coherence_metrics (1:N)

DynamicTask
  ├── parent_execution (N:1)
  ├── branch (N:1, optional)
  ├── spawned_by_agent (N:1)
  └── blocks_tasks (M:N via task_dependencies)

WorkflowBranch
  ├── parent_execution (N:1)
  └── branch_tasks (1:N via DynamicTask.branch_id)
```

---

## Workflow System

### Phase-Based Execution

**Phases:**
1. **Investigation:** Explore, analyze, discover requirements
2. **Building:** Implement, code, create
3. **Validation:** Test, verify, validate

**Key Features:**
- Agents can spawn tasks in ANY phase
- No strict phase transitions (semi-structured)
- Agents discover what needs to be done
- Workflows build themselves dynamically

### Workflow Lifecycle

```
Start → Investigation → Building → Validation → Complete
         │                │            │
         └── Branch ───────┼────────────┘
                           │
                    (Parallel tracks)
```

### Task Spawning Flow

```
Agent discovers need
  → Analyzes context
  → Determines phase
  → Spawns task with rationale
  → Optionally blocks on other tasks
  → PM Guardian monitors coherence
```

---

## Agent System

### Agent Framework: Agno

**Why Agno:**
- Enterprise-grade multi-agent framework
- Persistent sessions with automatic memory management
- Tool integration (MCP support)
- Multi-agent coordination built-in

### Agent Hierarchy

```
AgnoSquadAgent (Base)
  ├── AgnoProjectManager (PM + Guardian)
  ├── AgnoBackendDeveloper
  ├── AgnoFrontendDeveloper
  ├── AgnoAITEngineer
  ├── AgnoQAEngineer
  ├── AgnoDevOpsEngineer
  ├── AgnoDesigner
  ├── AgnoTechLead
  └── AgnoSolutionArchitect
```

### Agent Capabilities

**All Agents:**
- Inherit task spawning methods (`spawn_investigation_task`, etc.)
- Have MCP tool access (Git, GitHub, Jira based on role)
- Can communicate via message bus
- Have persistent memory via Agno

**PM Agent (Special):**
- Orchestrates workflow
- Monitors coherence (Guardian)
- Detects anomalies
- Generates recommendations
- Validates task relevance

---

## Integration Layer

### Message Bus (NATS JetStream)

**Purpose:**
- Agent-to-agent communication (real-time messaging)
- Event broadcasting between agents
- Real-time status updates

**Events:**
- Task spawned
- Task status updated
- Workflow phase changed
- Discovery made
- Branch created/merged

**Use Cases:**
- Agent A sends message to Agent B
- Broadcast "task completed" event to all agents
- Real-time notifications between agents

**NOT used for:**
- Background workflow execution (that's Inngest)
- Long-running multi-step workflows

### Background Job Orchestration (Inngest)

**Purpose:**
- Execute multi-agent workflows asynchronously
- Orchestrate step-by-step agent collaboration
- Enable instant API responses

**Workflow Examples:**
- User creates task → Queue in Inngest → Workers execute PM → Backend → QA
- Multi-step workflows with retries and error handling
- Durable execution that survives crashes

**Events:**
- `agent/workflow.execute` - Start multi-agent workflow
- `agent/single.execute` - Execute single agent task

**Benefits:**
- API returns in <100ms (instant to user)
- Workflows run in background workers
- Automatic retries on failure
- Independent worker scaling

### NATS vs Inngest - Separation of Concerns

| Feature | NATS JetStream | Inngest |
|---------|----------------|---------|
| **Purpose** | Real-time messaging | Background workflows |
| **Use Case** | Agent-to-agent communication | Multi-step agent orchestration |
| **Latency** | Low (milliseconds) | Higher (seconds) |
| **Delivery** | At-least-once | Durable with retries |
| **Pattern** | Pub/Sub messaging | Step-by-step workflows |
| **Scaling** | Message distribution | Worker pool scaling |
| **Example** | "Agent A → Agent B: message" | "PM → Backend → QA workflow" |

**They work together:**
- NATS: Agents communicate during workflow execution
- Inngest: Orchestrates which agents run and when
- Both access same database (PostgreSQL)
- Both are production infrastructure

### SSE (Server-Sent Events)

**Purpose:**
- Real-time updates to frontend
- Workflow state changes
- Task status updates
- Kanban board updates

**Endpoints:**
- `/api/v1/sse/workflows/{execution_id}`

### MCP Servers

**External MCP Servers (Agents use):**
- Git MCP Server
- GitHub MCP Server
- Jira MCP Server (Atlassian)

**Internal MCP Server:**
- Agent-Squad MCP Server (exposes our capabilities)

---

## API Architecture

### API Structure

**Base Path:** `/api/v1`

**Endpoints by Stream:**

#### Stream A: Phase-Based Workflow
- `POST /workflows/{id}/tasks/spawn` - Spawn task
- `GET /workflows/{id}/tasks` - List tasks
- `GET /workflows/{id}/tasks/{task_id}` - Get task
- `PATCH /workflows/{id}/tasks/{task_id}` - Update status

#### Stream B: Task Spawning
- Integrated into workflow endpoints

#### Stream C: PM-as-Guardian
- `GET /pm-guardian/workflows/{id}/coherence` - Get coherence
- `GET /pm-guardian/workflows/{id}/health` - Get health
- `POST /pm-guardian/workflows/{id}/validate` - Validate task

#### Stream D: Discovery Engine
- `GET /discovery/workflows/{id}/analyze` - Analyze context
- `GET /discovery/workflows/{id}/suggestions` - Get suggestions

#### Stream E: Workflow Branching
- `POST /branching/workflows/{id}/branches` - Create branch
- `GET /branching/workflows/{id}/branches` - List branches
- `POST /branching/branches/{id}/merge` - Merge branch
- `POST /branching/branches/{id}/abandon` - Abandon branch

#### Stream F: Kanban Board
- `GET /kanban/workflows/{id}` - Get board
- `GET /kanban/workflows/{id}/dependencies` - Get dependency graph

#### Stream G: Advanced Guardian
- `GET /advanced-guardian/workflows/{id}/anomalies` - Detect anomalies
- `GET /advanced-guardian/workflows/{id}/recommendations` - Get recommendations
- `GET /advanced-guardian/workflows/{id}/advanced-metrics` - Get comprehensive metrics

#### Stream H: ML Detection
- `POST /ml-detection/opportunities/detect` - Detect opportunities
- `POST /ml-detection/predict-value` - Predict task value
- `POST /ml-detection/train` - Train model

#### Stream I: Workflow Intelligence
- `GET /intelligence/workflows/{id}/suggestions` - Get suggestions
- `GET /intelligence/workflows/{id}/prediction` - Predict outcomes
- `GET /intelligence/workflows/{id}/optimize-order` - Optimize ordering

#### Stream J: MCP Integration
- `GET /mcp/server/tools` - List MCP tools
- `GET /mcp/server/status` - Get server status

#### Stream K: Analytics
- `GET /analytics/workflows/{id}` - Get analytics
- `GET /analytics/workflows/{id}/graph` - Get graph data

### Authentication

All endpoints require authentication via `get_current_user` dependency (JWT tokens).

---

## Infrastructure

### Database: PostgreSQL

**Why PostgreSQL:**
- JSONB support for flexible metadata
- Strong consistency
- Excellent async support (asyncpg)
- Production-grade reliability

**Key Tables:**
- `task_executions` - Main executions
- `dynamic_tasks` - Dynamic tasks
- `workflow_branches` - Branches
- `coherence_metrics` - Guardian metrics
- `task_dependencies` - Dependency relationships
- `squad_members` - Agents
- `agent_messages` - Communication

### Message Bus: NATS JetStream

**Why NATS:**
- High performance
- At-least-once delivery
- Stream persistence
- Perfect for event-driven architecture

### Cache: Redis

**Uses:**
- Session storage
- Rate limiting
- Temporary data
- Query result caching

### Background Workflow Engine: Inngest

**Replaces:** Celery (deprecated)

**Uses:**
- Multi-agent workflow orchestration
- Background agent execution
- Step-by-step workflow coordination
- Automatic retries and error handling

**Benefits over Celery:**
- Durable execution (survives crashes)
- Built-in monitoring dashboard
- Step-by-step workflow visibility
- Better error handling and retries
- Independent worker scaling
- Instant API responses

### Vector DB: Pinecone

**Uses:**
- RAG (Retrieval-Augmented Generation)
- Code search
- Context storage

---

## Security

### Authentication
- JWT-based authentication
- Token refresh mechanism
- User sessions

### Authorization
- Role-based access control
- Squad-level isolation
- Agent permission scoping

### Data Isolation
- Squad-level data separation
- Execution-level isolation
- Agent-scoped tool access

---

## Technology Stack

### Backend
- **Framework:** FastAPI (async Python)
- **ORM:** SQLAlchemy (async)
- **Migrations:** Alembic
- **Agent Framework:** Agno
- **Message Bus:** NATS JetStream (agent communication)
- **Workflow Engine:** Inngest (background jobs)
- **Cache:** Redis
- **Vector DB:** Pinecone

### Frontend (Referenced)
- **Framework:** React/Next.js
- **Real-time:** Server-Sent Events (SSE)
- **Visualization:** D3.js / Cytoscape.js (for graph)

### Deployment
- **Containerization:** Docker / Docker Compose
- **Database:** PostgreSQL
- **Message Bus:** NATS

---

## Key Design Decisions

### 1. Phase-Based vs Linear Workflows

**Decision:** Phase-based with flexible transitions

**Rationale:**
- Enables discovery-driven workflows
- More natural for agent collaboration
- Allows parallel investigation tracks

### 2. PM-as-Guardian vs Separate Guardian

**Decision:** Enhanced PM with Guardian capabilities

**Rationale:**
- Reduces complexity
- Single source of truth for orchestration
- Integrated monitoring and validation

### 3. Dynamic Task Spawning

**Decision:** Agents spawn tasks themselves

**Rationale:**
- Enables true discovery-driven workflows
- Agents know what needs to be done
- Self-organizing workflows

### 4. Agno Framework

**Decision:** Use Agno for agent foundation

**Rationale:**
- Enterprise-grade
- Persistent sessions
- Automatic memory management
- MCP tool integration

### 5. Graceful Degradation

**Decision:** ML features work without ML libraries

**Rationale:**
- Pattern-based fallback
- No hard dependencies
- Works in all environments

---

## Performance Optimizations

### Database
- **Eager Loading:** `selectinload` to prevent N+1 queries
- **Composite Indexes:** Optimized query patterns
- **Connection Pooling:** Async session pool

### Caching
- Redis for frequently accessed data
- Query result caching
- Session caching

### Real-time Updates
- SSE for efficient real-time streaming
- Event-driven architecture
- Minimal polling

---

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers (scale to 50+ pods)
- Stateless background workers (scale to 100+ pods)
- Shared database (PostgreSQL)
- NATS for distributed communication
- Inngest for workflow distribution

### Agent Scaling

**See full documentation:** [`AGENT_SCALING_EXPLAINED.md`](../../AGENT_SCALING_EXPLAINED.md)

**Key Strategy: Agent Pool + Horizontal Scaling**

**Agent Pool (Phase 2):**
- Reuse agent instances across requests
- 100 agents per worker (cached in memory)
- 60% faster agent creation (0.126s → 0.05s)
- 70% less memory usage

**Horizontal Worker Scaling:**
- Add more workers to increase capacity
- Each worker has independent agent pool
- Total capacity = workers × 100 agents

**Scaling Math:**
```
1,000 users  → 2-5 workers   → 200-500 agent instances → 30-75 GB RAM
10,000 users → 10-20 workers → 1,000-2,000 instances  → 150-300 GB RAM
```

**Key Insights:**
- We don't create thousands of agent processes
- Agent instances are reused (pooled)
- Real bottleneck: LLM API rate limits (~3 workflows/sec)
- Horizontal scaling handles load distribution
- Inngest queues workflows efficiently

### Data Scaling
- PostgreSQL for transactional data
- Pinecone for vector search
- Redis for ephemeral data and caching

---

## Monitoring & Observability

### Metrics Tracked
- Workflow completion rates
- Agent coherence scores
- Task spawn rates
- Discovery-to-value conversion
- Branch success rates

### Logging
- Structured logging (JSON)
- Agent activity logs
- Error tracking
- Performance metrics

### Health Checks
- Workflow health scores
- Agent activity levels
- System resource usage

---

## Future Enhancements

### Potential Additions
- Advanced ML models (transformer-based)
- Enhanced visualization (3D graphs)
- More MCP servers
- Advanced analytics (time series)
- Export functionality (PDF reports)

---

## Inngest Background Workflow System

### Overview

Inngest is our background workflow orchestration engine that enables instant API responses (<100ms) while multi-agent workflows execute asynchronously.

### Architecture

```
API Request
    │
    ▼
POST /task-executions/{id}/start-async
    │
    ├─► Update status to "queued"
    ├─► Send event to Inngest
    └─► Return response (<100ms)

         ↓ (event queued)

    Inngest Cloud
         ↓ (distributes work)

    Background Worker(s)
         ↓
    Execute Workflow:
      1. Update status → "running"
      2. Get squad members
      3. Execute PM agent (with retries)
      4. Execute Backend agent (with retries)
      5. Execute QA agent (with retries)
      6. Update status → "completed"
```

### Workflow Functions

**Primary Workflows:**
- `execute_agent_workflow` - Multi-agent collaboration (PM → Backend → QA)
- `execute_single_agent_workflow` - Single agent execution

**Location:** `backend/workflows/agent_workflows.py`

### Key Features

**Durable Execution:**
- Workflows resume after crashes
- Step-by-step execution with checkpoints
- No lost work

**Automatic Retries:**
- Each step can retry on failure (2-3 times configurable)
- Database operations: 3 retries
- LLM operations: 2 retries

**Error Handling:**
- Comprehensive error tracking
- Status updates on failure
- Dead letter queue for failed workflows

**Monitoring:**
- Inngest dashboard (dev: http://localhost:8288)
- Production: https://app.inngest.com
- Real-time workflow visibility
- Performance metrics

### Deployment

**Development:**
```bash
# Terminal 1: API
uvicorn backend.core.app:app --reload

# Terminal 2: Inngest Dev Server
npx inngest-cli@latest dev

# Terminal 3: Test
curl -X POST "http://localhost:8000/api/v1/task-executions/{id}/start-async?message=Test"
```

**Production:**
```yaml
# API pods (horizontal scaling)
replicas: 3-50 (auto-scale)
command: uvicorn backend.core.app:app

# Worker pods (horizontal scaling)
replicas: 5-100 (auto-scale)
command: python -m backend.workers.inngest_worker

# Environment
INNGEST_EVENT_KEY: prod-key
INNGEST_SIGNING_KEY: signing-key
```

### Performance Impact

| Metric | Before | After |
|--------|--------|-------|
| API response | 5-30s | <100ms |
| Concurrent users | 50 | 500+ |
| Workflows/sec | 12 | 100+ |
| Timeout errors | Common | Rare |

### Files

**Core:**
- `backend/core/inngest.py` - Inngest client
- `backend/workflows/agent_workflows.py` - Workflow functions
- `backend/workers/inngest_worker.py` - Worker script

**Integration:**
- `backend/core/app.py` - Mounted at `/api/inngest`
- `backend/api/v1/endpoints/task_executions.py` - Async endpoint

**Documentation:**
- `INNGEST_IMPLEMENTATION.md` - Implementation guide

---

**Document Version:** 2.1
**Last Updated:** 2025-11-03
**Maintained By:** Agent-Squad Team
