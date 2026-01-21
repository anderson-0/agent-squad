# Agent-Squad 🚀

**Multi-agent AI system for collaborative software development with discovery-driven workflows**

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd agent-squad
./scripts/setup.sh
```

**Services:** Frontend (http://localhost:3000) | Backend API (http://localhost:8000) | Docs (http://localhost:8000/docs)

## What Is Agent-Squad?

Agent-Squad orchestrates specialized AI agents (Backend Dev, Frontend Dev, QA Tester, DevOps, PM) to collaboratively build software using **discovery-driven workflows** inspired by Hephaestus:

- **Dynamic Task Spawning:** Agents create tasks as they discover opportunities
- **Workflow Branching:** Parallel tracks for major discoveries  
- **PM-as-Guardian:** Intelligent monitoring and recommendations
- **Phase-Based:** Investigation → Building → Validation progression

## Key Features

- **Discovery Engine:** Automatically finds optimization opportunities, bugs, missing features
- **Workflow Intelligence:** AI-powered task suggestions and outcome predictions  
- **Real-Time Kanban:** Auto-generated boards with dependency visualization
- **MCP Integration:** Standard protocol for external tool integration
- **Multi-LLM Support:** OpenAI, Anthropic, Groq, Ollama (FREE local)

## Architecture

```
Frontend (Next.js) ←→ FastAPI Backend ←→ PostgreSQL/Redis/NATS
                    ↓
            Agent Layer (Agno) → Discovery Engine → Workflow Intelligence
```

**Core Components:**
- `backend/agents/` - 9 specialized agent roles with orchestration
- `backend/api/` - RESTful APIs with async processing  
- `frontend/` - React/Next.js dashboard with real-time updates
- `docs/` - Complete documentation and guides

## Project Structure

```
agent-squad/
├── backend/                    # FastAPI backend (60K+ LOC)
│   ├── agents/                 # AI agent implementations (23K LOC)
│   │   ├── agno_base.py       # Enterprise-grade Agno foundation
│   │   ├── factory.py         # Agent creation and management
│   │   ├── specialized/       # 12 specialized agent roles
│   │   ├── orchestration/     # Workflow and phase management
│   │   ├── communication/     # NATS message bus integration
│   │   ├── discovery/         # Opportunity detection engine
│   │   ├── guardian/          # PM-as-Guardian system
│   │   └── interaction/       # Message handling and routing
│   ├── api/v1/                # RESTful API endpoints (9K LOC)
│   ├── models/                # SQLAlchemy data models
│   ├── services/              # Business logic layer
│   ├── core/                  # Infrastructure and configuration
│   └── integrations/          # External service integrations
├── frontend/                   # Next.js frontend (9K+ LOC)
│   ├── app/                   # App Router structure
│   ├── components/            # React components (47 files)
│   ├── stores/                # Zustand state management
│   └── lib/                   # Utilities and API clients
├── docs/                      # Comprehensive documentation
├── templates/                 # Squad configuration templates
└── roles/                     # Agent role definitions
```

## Agent Roles

**12 Specialized Agent Types:**
- **Project Manager** - Orchestrates squad, monitors workflow health
- **Tech Lead** - Technical decisions, architecture guidance  
- **Backend Developer** - Server-side development, APIs, databases
- **Frontend Developer** - UI/UX development, React/Next.js
- **QA Tester** - Testing, quality assurance, bug detection
- **DevOps Engineer** - Infrastructure, CI/CD, deployment
- **Solution Architect** - System design, technical planning
- **AI Engineer** - AI/ML model development and integration
- **Data Scientist** - Data analysis, statistical modeling
- **Data Engineer** - Data pipelines, ETL processes
- **ML Engineer** - Machine learning operations and deployment
- **AI/ML Project Manager** - Specialized PM for AI projects

## Usage

```python
# Create squad
POST /api/v1/squads {"name": "Dev Squad", "agents": [{"role": "backend_developer"}]}

# Start workflow  
POST /api/v1/task-executions {"squad_id": "...", "description": "Build auth system"}

# Agents work autonomously, spawn tasks, create branches
```

## Development

```bash
# Local development
docker-compose up -d postgres redis nats
cd backend && alembic upgrade head
uvicorn backend.core.app:app --reload

# Testing
cd backend && pytest --cov=backend

# Code quality
ruff check backend/ && black backend/ && mypy backend/
```

## Technology Stack

**Backend:**
- **Framework:** FastAPI (async Python web framework)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Message Bus:** NATS JetStream for agent communication
- **Background Tasks:** Celery with Redis
- **AI Framework:** Agno for agent orchestration
- **LLM Providers:** OpenAI, Anthropic, Groq, Ollama
- **Authentication:** JWT with refresh tokens
- **Testing:** pytest with coverage reporting

**Frontend:**
- **Framework:** Next.js 16 with React 19
- **Styling:** Tailwind CSS v4 with shadcn/ui components
- **State Management:** Zustand for global state
- **Data Fetching:** TanStack Query for API integration
- **Animations:** Framer Motion for smooth interactions
- **Forms:** React Hook Form with Zod validation
- **Icons:** Lucide React icon library

**Infrastructure:**
- **Containerization:** Docker with multi-stage builds
- **Orchestration:** Docker Compose for local development
- **Monitoring:** Prometheus + Grafana stack
- **Background Processing:** Inngest for durable execution
- **Sandboxing:** E2B for secure code execution

## Documentation

- **[Architecture](./docs/architecture/ARCHITECTURE.md)** - Detailed system design
- **[API Docs](http://localhost:8000/docs)** - Interactive API reference  
- **[Setup Guide](./docs/SETUP.md)** - Complete installation instructions
- **[Scaling Guide](./AGENT_SCALING_EXPLAINED.md)** - Performance optimization

**Version:** 2.1 (Hephaestus + Inngest) | **License:** [Add License]