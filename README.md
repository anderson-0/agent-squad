# Agent-Squad 🚀

**A production-ready, multi-agent AI system for collaborative software development**

Agent-Squad enables teams of specialized AI agents to work together on complex software development tasks using a Hephaestus-style, discovery-driven workflow architecture.

---

## 🎯 What Is Agent-Squad?

Agent-Squad is a comprehensive platform that orchestrates multiple specialized AI agents (Backend Developer, Frontend Developer, QA Tester, DevOps Engineer, etc.) to collaboratively build software. Unlike traditional task assignment systems, Agent-Squad uses a **discovery-driven workflow** where agents:

1. **Discover** opportunities and issues as they work
2. **Spawn** tasks dynamically based on discoveries
3. **Branch** workflows when major opportunities are found
4. **Collaborate** via intelligent monitoring and recommendations

### Key Innovation: Semi-Structured, Discovery-Driven Workflows

Inspired by the Hephaestus framework, Agent-Squad workflows are **semi-structured**:
- Agents work in phases (Investigation → Building → Validation)
- But phases are flexible - agents can spawn tasks in any phase
- Workflows build themselves as agents discover what needs to be done
- No rigid task lists - everything emerges from agent discoveries

---

## 🌟 Key Features

### 1. Phase-Based Dynamic Workflows

Workflows progress through three phases:
- **Investigation:** Explore, analyze, discover requirements
- **Building:** Implement, code, create features
- **Validation:** Test, verify, validate work

Agents can spawn tasks in **any phase**, enabling true discovery-driven development.

### 2. Dynamic Task Spawning

Agents autonomously create tasks as they discover:
- Optimization opportunities
- Bugs or issues
- Refactoring needs
- Missing features

Each task includes:
- Clear rationale for why it was created
- Appropriate phase assignment
- Blocking dependencies (if needed)

### 3. Workflow Branching

When agents discover major opportunities, they can create **workflow branches**:
- Parallel investigation tracks
- Independent optimization efforts
- Risk-free experimentation

Branches can be:
- **Merged** back with results
- **Abandoned** if not valuable
- **Completed** when done

### 4. PM-as-Guardian System

The Project Manager agent serves dual roles:
- **Orchestrator:** Coordinates agent work
- **Guardian:** Monitors workflow health and agent coherence

**Guardian Capabilities:**
- Coherence scoring (agent alignment with phases)
- Workflow health monitoring
- Anomaly detection (phase drift, stagnation, etc.)
- Actionable recommendations

### 5. Discovery Engine

Automatically analyzes agent work to discover:
- Optimization opportunities
- Performance improvements
- Code quality issues
- Missing validations

**Features:**
- Pattern-based detection (always works)
- ML-enhanced detection (when available)
- Value scoring for discoveries
- Task suggestions from discoveries

### 6. Workflow Intelligence

AI-powered insights:
- **Task Suggestions:** What should be done next?
- **Outcome Predictions:** When will this complete? Success probability?
- **Task Optimization:** Best order for task completion

Uses data from:
- Guardian coherence scores
- Discovery opportunities
- Active branches
- Historical patterns

### 7. ML-Based Detection

Machine learning models for:
- Opportunity detection in code
- Task value prediction
- Model training on historical data

**Graceful Fallback:** Works with pattern matching if ML libraries unavailable

### 8. Real-Time Kanban Board

Auto-generated Kanban boards showing:
- Tasks organized by phase
- Real-time status updates
- Dependency visualization
- Branch visualization

### 9. MCP Integration

Exposes Agent-Squad capabilities via **Model Context Protocol**:
- `spawn_task`: Create tasks
- `check_workflow_health`: Monitor health
- `get_coherence_score`: Check agent alignment
- `create_workflow_branch`: Create branches
- `discover_opportunities`: Run discovery
- `get_kanban_board`: Get board state

Enables integration with:
- Claude Code
- Other MCP-compatible tools
- External orchestration systems

### 10. Comprehensive Analytics

Track and visualize:
- Workflow completion metrics
- Phase distribution
- Agent performance
- Coherence trends
- Discovery-to-value conversion
- Workflow graphs (nodes, edges, branches)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (React/Next.js)                    │
│         Kanban Board, Analytics, Visualization            │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP/SSE
┌─────────────────────▼───────────────────────────────────┐
│              FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │  API Layer                                        │  │
│  │  - Workflows, Discovery, Intelligence, etc.       │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│  ┌────────────────▼──────────────────────────────────┐  │
│  │  Orchestration Layer                              │  │
│  │  - PhaseBasedWorkflowEngine                       │  │
│  │  - DiscoveryEngine, BranchingEngine                │  │
│  │  - WorkflowIntelligence                           │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│  ┌────────────────▼──────────────────────────────────┐  │
│  │  Agent Layer (Agno Framework)                     │  │
│  │  - PM-as-Guardian                                 │  │
│  │  - Specialized Agents (9 roles)                  │  │
│  └────────────────┬─────────────────────────────────┘  │
└───────────────────┼─────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───▼────┐    ┌─────▼─────┐   ┌─────▼────┐
│PostgreSQL│   │    NATS    │   │  Redis   │
│          │   │ JetStream  │   │          │
└──────────┘   └────────────┘   └──────────┘
```

**Full Architecture Details:** See [docs/architecture/ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md)

---

## 🚀 Quick Start

### ⚡ One-Command Setup (Recommended)

Get Agent-Squad running in **under 5 minutes**:

```bash
# 1. Clone the repository
git clone <repository-url>
cd agent-squad

# 2. Run setup script
./scripts/setup.sh
```

That's it! The script will:
- ✅ Check prerequisites (Docker, Docker Compose)
- ✅ Create environment file
- ✅ Build Docker images
- ✅ Start all services (postgres, redis, nats, backend, frontend)
- ✅ Run database migrations
- ✅ Wait for services to be healthy
- ✅ Show URLs and helpful commands

**Services Running:**
- 🌐 **Frontend:** http://localhost:3000
- 🔧 **Backend API:** http://localhost:8000
- 📚 **API Docs:** http://localhost:8000/docs
- ❤️ **Health Check:** http://localhost:8000/api/v1/health

### Prerequisites

**Required:**
- [Docker](https://www.docker.com/get-started) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+
- 8GB RAM minimum
- 10GB disk space

**Optional (for LLM access):**
- OpenAI API key OR
- Anthropic API key OR
- [Ollama](https://ollama.com/download) (FREE local LLM)

### 🎁 Using Ollama (FREE Local LLM)

For **FREE local development** without API keys:

```bash
# 1. Install Ollama
brew install ollama   # macOS
# Or download from https://ollama.com/download

# 2. Pull a model
ollama pull llama3.2      # Recommended (2GB)
ollama pull llama3.2:1b   # Fastest (1.3GB)

# 3. Verify it's running
curl http://localhost:11434/api/tags
```

**Benefits:**
- ✅ **$0 cost** - Completely FREE
- ✅ **No API keys** - Zero configuration
- ✅ **100% private** - Data never leaves your machine
- ✅ **No rate limits** - Unlimited usage
- ✅ **Works offline** - No internet required

Ollama runs on your local machine and Agent-Squad will automatically use it via `host.docker.internal:11434`.

**See:** [OLLAMA_SETUP_GUIDE.md](./OLLAMA_SETUP_GUIDE.md) for detailed setup.

### Configuration (Optional)

The setup script creates `backend/.env` automatically. To customize:

```bash
# Edit environment file
nano backend/.env
```

**Key variables:**
```bash
# Database (auto-configured)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/agent_squad_dev

# Message Bus (auto-configured)
MESSAGE_BUS=nats
NATS_URL=nats://nats:4222

# Cache (auto-configured)
REDIS_URL=redis://redis:6379/0
CACHE_ENABLED=true

# LLM Providers (optional - choose at least one)
OPENAI_API_KEY=sk-...              # OpenAI GPT models
ANTHROPIC_API_KEY=sk-ant-...       # Claude models
GROQ_API_KEY=gsk_...               # Groq (fast, free tier)

# Ollama (FREE - default configuration)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2
```

### Manual Setup (Alternative)

If you prefer manual setup:

```bash
# 1. Copy environment file
cp backend/.env.example backend/.env

# 2. Edit backend/.env and add API keys (optional)
nano backend/.env

# 3. Start services
docker-compose up -d

# 4. Wait for services to be healthy
docker-compose ps
```

---

## 📖 Usage Examples

### Creating a Workflow

1. **Create a Squad:**
```python
POST /api/v1/squads
{
  "name": "Development Squad",
  "agents": [
    {"role": "project_manager"},
    {"role": "backend_developer"},
    {"role": "frontend_developer"}
  ]
}
```

2. **Start a Task Execution:**
```python
POST /api/v1/task-executions
{
  "squad_id": "...",
  "task_id": "...",
  "description": "Build user authentication system"
}
```

3. **Agents Work:**
- Agents automatically spawn tasks as they discover needs
- PM Guardian monitors and provides recommendations
- Workflows branch when major opportunities are found

### Spawning Tasks Programmatically

```python
# Via API
POST /api/v1/workflows/{execution_id}/tasks/spawn
{
  "phase": "building",
  "title": "Implement OAuth2 flow",
  "description": "Add OAuth2 authentication...",
  "rationale": "Required for user authentication",
  "blocking_task_ids": []
}

# Via Agent (automatic)
# Agents spawn tasks via AgentTaskSpawner
await agent.spawn_building_task(
    title="...",
    description="...",
    rationale="..."
)
```

### Using Discovery Engine

```python
# Analyze work context
GET /api/v1/discovery/workflows/{execution_id}/analyze?agent_id={agent_id}

# Get task suggestions
GET /api/v1/discovery/workflows/{execution_id}/suggestions?agent_id={agent_id}
```

### Checking Workflow Health

```python
# Get PM Guardian health metrics
GET /api/v1/pm-guardian/workflows/{execution_id}/health

# Get advanced metrics
GET /api/v1/advanced-guardian/workflows/{execution_id}/advanced-metrics
```

### Using MCP Tools

The Agent-Squad MCP server can be used by external systems:

```bash
# Connect to MCP server
python -m backend.integrations.mcp.servers.agent_squad_server

# Available tools:
# - spawn_task
# - check_workflow_health
# - get_coherence_score
# - create_workflow_branch
# - discover_opportunities
# - get_kanban_board
```

---

## 🎨 Workflow Example

### Scenario: Building a User Authentication System

1. **Investigation Phase:**
   - Backend Dev spawns: "Research OAuth2 providers"
   - PM spawns: "Define authentication requirements"
   - Results: Discovery of optimization opportunity

2. **Branch Created:**
   - Discovery: "Could optimize with Redis caching"
   - Branch created: "Authentication Performance Optimization"
   - Parallel track starts

3. **Building Phase:**
   - Main workflow: Implement OAuth2
   - Branch: Investigate caching strategy
   - Frontend Dev spawns: "Build login UI"
   - Tasks spawn dynamically as needed

4. **Guardian Monitoring:**
   - PM monitors coherence
   - Detects: "Backend Dev spawning many investigation tasks"
   - Recommendation: "Consider transitioning to building phase"

5. **Validation Phase:**
   - QA Tester spawns: "Test OAuth2 flow"
   - Branch merged with results
   - All tasks completed

6. **Intelligence Insights:**
   - Prediction: "Workflow will complete in 16 hours"
   - Suggestion: "Add integration tests for edge cases"

---

## 🧪 Testing

Run tests:

```bash
cd backend
pytest

# With coverage
pytest --cov=backend --cov-report=html
```

Test coverage includes:
- Unit tests for all engines and services
- Integration tests for workflows
- API endpoint tests
- Agent behavior tests

---

## 📚 Documentation

> **📖 [Complete Documentation Index](./DOCUMENTATION_INDEX.md)** - Navigate all documentation

### Core Documentation
- **[Architecture Documentation](./docs/architecture/ARCHITECTURE.md)** - Detailed system architecture (v2.1)
- **[Agent Scaling Explained](./AGENT_SCALING_EXPLAINED.md)** ⭐ - How we handle thousands of users
- **[Inngest Implementation Guide](./INNGEST_IMPLEMENTATION.md)** ⭐ - Background workflow orchestration
- **[Scaling to Thousands Plan](./SCALE_TO_THOUSANDS_OPTIMIZATION_PLAN.md)** - Performance optimization roadmap
- **[Competition Comparison](./docs/COMPETITION_COMPARISON.md)** - Comparison with Hephaestus

### API Documentation
- **[API Documentation](./docs/API.md)** - Full API reference (generated via FastAPI docs)

### Implementation Documentation
- **Stream Completion Docs:**
  - [Stream A-G Complete](./STREAM_A_G_COMPLETE.md)
  - [Stream H Complete](./STREAM_H_COMPLETE.md)
  - [Stream I Complete](./STREAM_I_COMPLETE.md)
  - [Streams J & K Complete](./STREAM_J_K_COMPLETE.md)

### API Documentation

Interactive API docs available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI (async Python)
- **Database:** PostgreSQL (async via asyncpg)
- **ORM:** SQLAlchemy (async)
- **Migrations:** Alembic
- **Agent Framework:** Agno
- **Message Bus:** NATS JetStream (agent communication)
- **Workflow Engine:** Inngest (background jobs) ⭐ NEW
- **Cache:** Redis
- **Vector DB:** Pinecone

### Integration
- **MCP:** Model Context Protocol support
- **LLM Providers:**
  - **Cloud:** OpenAI, Anthropic, Groq
  - **Local:** Ollama (FREE, no API key required) ✨
- **External Tools:** Git, GitHub, Jira (via MCP)

---

## 🔧 Development

### Project Structure

```
agent-squad/
├── backend/
│   ├── agents/              # Agent implementations
│   │   ├── orchestration/   # Workflow engine
│   │   ├── discovery/       # Discovery system
│   │   ├── guardian/        # PM Guardian
│   │   ├── intelligence/    # Workflow intelligence
│   │   ├── ml/              # ML detection
│   │   ├── branching/       # Branching engine
│   │   └── specialized/     # Agent roles
│   ├── api/v1/endpoints/    # API endpoints
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── core/                # Core utilities
│   └── integrations/        # External integrations
├── docs/                    # Documentation
└── tests/                   # Tests
```

### Running Locally

```bash
# Start database
docker-compose up -d postgres redis nats

# Run migrations
cd backend
alembic upgrade head

# Start backend
uvicorn backend.core.app:app --reload

# Start Celery worker (optional)
celery -A backend.workers.celery_app worker --loglevel=info
```

### Code Quality

```bash
# Linting
ruff check backend/

# Formatting
black backend/

# Type checking
mypy backend/
```

---

## 🎯 Key Differentiators

### vs Traditional Task Management
- ✅ **Discovery-Driven:** Tasks emerge from agent discoveries
- ✅ **Dynamic:** No rigid task lists
- ✅ **Intelligent:** AI-powered suggestions and predictions

### vs Other Multi-Agent Systems
- ✅ **Production-Ready:** Full infrastructure (DB, message bus, etc.)
- ✅ **Guardian System:** Intelligent monitoring and validation
- ✅ **Branching:** Discovery-driven parallel tracks
- ✅ **MCP Integration:** Standard protocol support

---

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## 📄 License

[Add your license here]

---

## 🙏 Acknowledgments

- **Hephaestus Framework** - Inspiration for discovery-driven workflows
- **Agno Framework** - Multi-agent foundation
- **FastAPI** - Excellent async framework
- **NATS** - High-performance message bus

---

## 📞 Support

- **Documentation:** See `docs/` directory
- **Issues:** [GitHub Issues](link-to-issues)
- **Discussions:** [GitHub Discussions](link-to-discussions)

---

**Built with ❤️ by the Agent-Squad Team**

**Version:** 2.1 (Hephaestus + Inngest Optimization)
**Last Updated:** 2025-11-03

---

## 🚀 Performance & Scalability

### Instant API Responses
- API response time: **<100ms** (was 5-30s)
- Background workflow orchestration via Inngest
- Durable execution with automatic retries

### Horizontal Scaling
- Supports **500+ concurrent users** (out of the box)
- Scales to **10,000+ users** with horizontal worker scaling
- Agent pooling reduces memory usage by 70%

### Real Bottleneck
- LLM API rate limits: ~3 workflows/sec (OpenAI GPT-4)
- Architecture handles 100+ workflows/sec when LLM allows
- Queue-based processing handles bursts efficiently

**See:** [AGENT_SCALING_EXPLAINED.md](./AGENT_SCALING_EXPLAINED.md) for detailed scaling architecture
