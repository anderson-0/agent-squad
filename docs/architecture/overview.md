# Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Next.js    │    │     CLI      │    │   Mobile     │          │
│  │   Web App    │    │   (Future)   │    │   (Future)   │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│         │                    │                    │                  │
│         └────────────────────┴────────────────────┘                  │
│                              │                                        │
└──────────────────────────────┼────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   Rate      │  │    Auth     │  │   Request   │                 │
│  │  Limiting   │  │  Validation │  │   Routing   │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Backend                          │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │
│  │  │   API    │  │  Service │  │  Agent   │  │ Webhook  │  │    │
│  │  │  Routes  │  │  Layer   │  │ Factory  │  │ Handlers │  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                        Inngest                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │   │
│  │  │   Task       │  │    Agent     │  │   Workflow   │     │   │
│  │  │  Execution   │  │ Collaboration│  │   Retry      │     │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│  │    PM     │  │    Dev    │  │   Tester  │  │   Tech    │       │
│  │   Agent   │  │   Agent   │  │   Agent   │  │   Lead    │       │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘       │
│         │              │              │              │               │
│         └──────────────┴──────────────┴──────────────┘               │
│                        │                                              │
│              ┌─────────┴─────────┐                                   │
│              │  A2A Protocol     │                                   │
│              │  Message Bus      │                                   │
│              └───────────────────┘                                   │
│                                                                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │     LLM      │  │     RAG      │  │   Learning   │             │
│  │   Providers  │  │   System     │  │   System     │             │
│  │ (OpenAI/etc) │  │  (Pinecone)  │  │  (Feedback)  │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                      │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  PostgreSQL  │  │    Redis     │  │   Pinecone   │             │
│  │  (Primary)   │  │   (Cache)    │  │  (Vectors)   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │     MCP      │  │    Stripe    │  │   External   │             │
│  │   Servers    │  │   Webhooks   │  │   Webhooks   │             │
│  │ (Git/Jira)   │  │              │  │  (Jira/Git)  │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. Client Layer
**Purpose**: User interfaces for interacting with the system

**Components**:
- **Next.js Web App**: Primary interface for squad management, task monitoring
- **CLI** (Future): Command-line interface similar to Claude Code
- **Mobile** (Future): Mobile app for on-the-go management

**Key Features**:
- Squad creation and configuration
- Real-time task monitoring via SSE
- Agent message viewing
- Feedback submission

### 2. API Gateway
**Purpose**: Entry point for all client requests

**Responsibilities**:
- Request routing
- Authentication validation
- Rate limiting
- CORS handling
- Request/response transformation

**Technology**:
- Kubernetes Ingress with NGINX
- Custom middleware in FastAPI

### 3. Application Layer
**Purpose**: Core business logic and API endpoints

**Components**:
- **API Routes**: RESTful endpoints (FastAPI)
- **Service Layer**: Business logic implementation
- **Agent Factory**: Creates and configures agents
- **Webhook Handlers**: Processes external webhooks

**Technology**: Python + FastAPI

### 4. Orchestration Layer
**Purpose**: Workflow management and async task execution

**Components**:
- **Task Execution Workflows**: Multi-step task processing
- **Agent Collaboration**: Coordinates inter-agent communication
- **Retry Logic**: Handles failures with exponential backoff

**Technology**: Inngest

**Key Workflows**:
- `squad/task.assigned` → Execute task
- `squad/agent.collaborate` → Agent-to-agent communication
- `squad/task.completed` → Finalize and learn

### 5. Agent Layer
**Purpose**: AI agents that perform development tasks

**Components**:
- Specialized agents (PM, Developers, Testers, etc.)
- A2A Protocol for inter-agent communication
- Message bus for routing messages
- Context manager with RAG integration
- PM + Tech Lead collaboration system

**Technology**: Custom implementation with OpenAI/Anthropic/Groq

**Agent Types** (9 specialized):
- **Project Manager**: Webhook handling, ticket review, effort estimation, delegation
- **Tech Lead**: Code review, complexity analysis, architecture decisions
- **Backend Developers**: Python (FastAPI, Django), Node.js (Express, NestJS)
- **Frontend Developers**: React + Next.js
- **QA Testers**: Testing and verification
- **Solution Architects**: System design and architecture
- **DevOps Engineers**: Infrastructure and deployment
- **AI Engineers**: ML/AI features
- **UI/UX Designers**: Design and user experience

**Key Features**:
- Multi-LLM provider support (OpenAI, Anthropic, Groq)
- Structured A2A protocol (10 message types)
- PM + TL collaboration on ticket review
- Effort and complexity estimation
- Conversation history management
- Real-time message streaming

### 6. Intelligence Layer
**Purpose**: AI/ML capabilities

**Components**:
- **LLM Providers**: OpenAI, Anthropic, Groq
- **RAG System**: Unified knowledge retrieval (Pinecone with namespaces)
- **Learning System**: Feedback processing and improvement

**Technology**:
- OpenAI API, Anthropic Claude, Groq
- Pinecone (vector database with namespaces)
- Custom learning pipeline

**RAG Strategy** (Unified Knowledge Base):
```
Pinecone Index with Namespaces:
├── {squad_id}:code          # Code from Git repositories
├── {squad_id}:tickets       # Jira tickets & resolutions
├── {squad_id}:docs          # Confluence, Notion, Google Docs
├── {squad_id}:conversations # Past agent discussions
└── {squad_id}:decisions     # Architecture Decision Records
```

**Benefits**:
- Single query retrieves relevant context from all sources
- Cross-reference capabilities (tickets + code + docs)
- Squad-isolated namespaces for security
- Metadata tagging for precise filtering

### 7. Data Layer
**Purpose**: Persistent storage

**Components**:
- **PostgreSQL**: Primary relational database
- **Redis**: Caching and pub/sub
- **Pinecone**: Vector embeddings

**Data Categories**:
- User and authentication data
- Squad and project configurations
- Task executions and agent messages
- Feedback and learning insights
- Document embeddings

### 8. Integration Layer
**Purpose**: External system integrations

**Components**:
- **MCP Servers**: Git, Jira, knowledge bases (Phase 4)
- **Stripe**: Payment processing
- **Webhooks**: External event receivers (via Inngest)

**Integrations**:
- **Jira**: Webhooks via Inngest, API access (MVP focus)
- **ClickUp**: Future support
- **Git**: GitHub, GitLab, Bitbucket (via MCP - Phase 4)
- **Knowledge Bases**: Confluence, Notion, Google Docs (via MCP - Phase 4)
- **Stripe**: Payment and subscription management

**MCP Servers** (Phase 4 from https://smithery.ai/):
- `@modelcontextprotocol/server-github` - GitHub access
- `@modelcontextprotocol/server-git` - Git operations
- `@modelcontextprotocol/server-filesystem` - File access
- Custom: `jira-mcp-server`, `confluence-mcp-server`, `notion-mcp-server`, `gdocs-mcp-server`

**Webhook Flow** (Inngest):
```
Jira Webhook → API Endpoint → Inngest Event → Workflow
  ├── issue_created → squad/ticket.created → PM reviews
  ├── issue_updated → squad/ticket.updated → PM updates
  └── issue_commented → squad/ticket.commented → PM notifies
```

## Architectural Style

**Current**: Modular Monolith
- Single deployment unit
- Clear module boundaries
- Shared database
- Easy to develop and deploy

**Future**: Microservices (if needed)
- Extract heavy services first (Intelligence, Integration)
- Event-driven communication
- Separate databases per service
- Independent scaling

## Key Architectural Decisions

### 1. Modular Monolith First
**Why**: Simpler to develop, deploy, and maintain initially. Can extract to microservices later if needed.

**Benefits**:
- Single codebase
- Easier debugging
- ACID transactions
- Lower operational complexity

### 2. Event-Driven Orchestration
**Why**: Task execution can take hours or days. Need async, durable workflows.

**Technology**: Inngest provides:
- Durable execution
- Retries with exponential backoff
- Event-driven triggers
- Step functions

### 3. Multi-LLM Provider Support
**Why**: Users want flexibility, avoid vendor lock-in, cost optimization.

**Implementation**: Adapter pattern for LLM providers

### 4. RAG for Context
**Why**: Agents need project-specific knowledge without fine-tuning.

**Benefits**:
- Fast iteration
- No model retraining
- Up-to-date information
- Cost-effective

### 5. Real-time via SSE
**Why**: Need to stream agent messages to dashboard.

**SSE vs WebSocket**:
- SSE: Simpler, one-way, auto-reconnect
- WebSocket: Bi-directional (not needed here)

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0 (async with asyncpg)
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Vector DB**: Pinecone (serverless)
- **Orchestration**: Inngest
- **Auth**: JWT (python-jose + bcrypt)
- **Payments**: Stripe
- **Package Manager**: uv (10-100x faster than pip)

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: Zustand / React Query
- **Forms**: React Hook Form + Zod

### Infrastructure
- **Containers**: Docker
- **Orchestration**: Kubernetes (AWS EKS)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: CloudWatch
- **Tracing**: OpenTelemetry

### AI/ML
- **LLM**: OpenAI (default), Anthropic, others
- **Embeddings**: OpenAI text-embedding-3-small
- **Agent Framework**: agno-agi/agnoframework

### Integrations
- **Git**: GitHub, GitLab, Bitbucket (via MCP)
- **Tickets**: Jira (via MCP)
- **Payments**: Stripe

## Deployment Architecture

```
┌─────────────────────────────────────────────┐
│              AWS Cloud                       │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │     EKS Cluster (Kubernetes)         │  │
│  │                                       │  │
│  │  ┌────────────┐    ┌────────────┐   │  │
│  │  │  Backend   │    │  Frontend  │   │  │
│  │  │  Pods (5)  │    │  Pods (3)  │   │  │
│  │  └────────────┘    └────────────┘   │  │
│  │                                       │  │
│  │  ┌────────────┐    ┌────────────┐   │  │
│  │  │   Inngest  │    │   Redis    │   │  │
│  │  │  Worker    │    │   Cache    │   │  │
│  │  └────────────┘    └────────────┘   │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │     RDS PostgreSQL                   │  │
│  │     (Multi-AZ, Auto-scaling)         │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │     S3 (Assets, Backups)             │  │
│  └──────────────────────────────────────┘  │
│                                              │
└─────────────────────────────────────────────┘

External Services:
- Pinecone (Vector DB)
- OpenAI (LLM)
- Stripe (Payments)
- MCP Servers (Git/Jira)
```

## Next Steps

- **Design Principles**: [design-principles.md](./design-principles.md)
- **Design Patterns**: [design-patterns.md](./design-patterns.md)
- **System Components**: [components.md](./components.md)
- **Scalability**: [scalability.md](./scalability.md)
