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

**Technology**: agno-agi/agnoframework + Custom implementation

**Agent Types**:
- Project Manager
- Backend/Frontend Developers
- QA Testers
- Tech Leads
- Solution Architects
- DevOps Engineers
- AI Engineers
- Designers

### 6. Intelligence Layer
**Purpose**: AI/ML capabilities

**Components**:
- **LLM Providers**: OpenAI, Anthropic, etc.
- **RAG System**: Knowledge retrieval from documents
- **Learning System**: Feedback processing and improvement

**Technology**:
- OpenAI API (default)
- Pinecone (vector database)
- Custom learning pipeline

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
- **MCP Servers**: Git and Jira operations
- **Stripe**: Payment processing
- **Webhooks**: External event receivers

**Integrations**:
- GitHub, GitLab, Bitbucket (via MCP)
- Jira (via MCP)
- Stripe (payments)

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
- **Framework**: FastAPI (Python)
- **ORM**: Prisma
- **Database**: PostgreSQL (Neon/Supabase)
- **Cache**: Redis
- **Vector DB**: Pinecone
- **Orchestration**: Inngest
- **Auth**: BetterAuth
- **Payments**: Stripe

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
