# Agent Squad - AI-Powered Software Development SaaS

A revolutionary SaaS platform where users can purchase and manage AI-powered software development squads. Each squad consists of specialized AI agents (developers, testers, project managers, etc.) that collaborate to complete software development tasks.

## 🚦 Current Status

**Phase 3 Complete** - Full AI agent collaboration system operational! 🎉

```bash
Backend:  ✅ Running (http://localhost:8000)
Tests:    ✅ 51/51 passing (100%)
Coverage: ✅ 33% overall (44% on critical paths)
API Docs: ✅ Available at /docs
Agents:   ✅ 5 specialized agents operational
```

**What's Working:**
- ✅ **Authentication** - JWT, password management, email verification
- ✅ **AI Agents** - 5 specialized agents (PM, Tech Lead, Developers, QA)
- ✅ **Squad Templates** - Pre-built squads with instant deployment (NEW!)
- ✅ **Communication** - Message bus, A2A protocol, conversation history
- ✅ **Hierarchical Routing** - 3-level escalation with 17 routing rules
- ✅ **Orchestration** - 10-state workflow, smart delegation
- ✅ **Collaboration** - Problem-solving, code review, standups
- ✅ **Context** - RAG with Pinecone, Redis memory, multi-source context
- ✅ **Real-time** - SSE streaming for live agent updates
- ✅ **API** - 48+ authenticated endpoints with full validation

## 🎯 Vision

Enable companies to scale their development capacity on-demand by providing AI agent squads that can autonomously handle software development tasks, from planning to deployment.

## ✨ Features

- **Customizable Squad Building** - Choose 2-10 members with various roles and tech stacks
- **Squad Templates** - Pre-built squad configurations for instant deployment (< 30 seconds)
- **Multi-Project Management** - Connect to Git repos and ticket systems
- **Intelligent Task Orchestration** - AI-powered task breakdown and delegation
- **Real-time Collaboration Dashboard** - Monitor agent communications in real-time
- **Learning & Feedback System** - Agents improve over time with RAG and feedback

## 🎨 Squad Templates (NEW!)

Create production-ready squads instantly with pre-built templates:

**Software Development Squad** - 6 agents with complete escalation hierarchy:
- Project Manager (Claude 3.5 Sonnet)
- Solution Architect (Claude 3.5 Sonnet)
- Tech Lead (Claude 3.5 Sonnet)
- Backend Developer (GPT-4)
- Frontend Developer (GPT-4)
- QA Tester (GPT-4)

**Features:**
- ✅ 17 routing rules with 3-level escalation (Dev → Tech Lead → Architect → PM)
- ✅ 8 question types (implementation, architecture, code_review, testing, etc.)
- ✅ CLI tool for instant squad creation (< 30 seconds)
- ✅ REST API for programmatic access
- ✅ Template customization support

**Quick Start:**
```bash
# List available templates
python -m backend.cli.apply_template --list

# Create squad from template
python -m backend.cli.apply_template \
  --user-email demo@test.com \
  --template software-dev-squad \
  --squad-name "Alpha Team"

# Or via API
curl -X POST http://localhost:8000/api/v1/templates/{template_id}/apply \
  -H "Content-Type: application/json" \
  -d '{"squad_id": "...", "user_id": "..."}'
```

**Documentation:**
- [Template System Guide](./TEMPLATE_SYSTEM_GUIDE.md) - Complete reference
- [CLI Tool README](./backend/cli/README.md) - CLI documentation
- [Template Implementation Plan](./TEMPLATE_IMPLEMENTATION_PLAN.md) - Technical details

## 🏗️ Tech Stack

**Backend**: Python + FastAPI + SQLAlchemy (async + asyncpg) + Alembic + PostgreSQL + Redis
**Frontend**: Next.js 14+ + TypeScript + Tailwind CSS
**AI**: OpenAI (default), Anthropic, agno-agi/agnoframework
**Orchestration**: Inngest
**Infrastructure**: Docker + Kubernetes + AWS

## 🚀 Quick Start

**For detailed setup instructions, see [SETUP.md](./SETUP.md)**

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)
- uv (for Python package management - optional, but recommended)

### Start the Application

#### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/agent-squad.git
cd agent-squad

# Start all services (backend, frontend, postgres, redis)
docker-compose up

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f backend
```

#### Option 2: Start Backend Only

```bash
# Start just the database services
docker-compose up -d postgres redis

# Start backend (will be at http://localhost:8000)
docker-compose up backend
```

Services will be available at:
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Frontend**: http://localhost:3000 (when started)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Verify Setup

```bash
# Check backend health
curl http://localhost:8000/health

# Or run verification script
./scripts/verify-setup.sh
```

### Manual Setup (Without Docker)

#### Backend

```bash
# Start PostgreSQL and Redis with Docker
docker-compose up -d postgres redis

cd backend

# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt  # or: pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start server
python main.py
# Server will be at http://localhost:8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
# Frontend will be at http://localhost:3000
```

## 📁 Project Structure

```
agent-squad/
├── backend/                 # FastAPI backend
│   ├── api/                # API routes
│   │   └── v1/            # API version 1
│   ├── core/               # Core functionality
│   │   ├── app.py         # FastAPI application
│   │   ├── config.py      # Configuration
│   │   ├── database.py    # Database connection
│   │   ├── security.py    # Password & JWT
│   │   └── auth.py        # Auth dependencies
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── repositories/       # Data access layer
│   ├── agents/             # AI agents
│   ├── workflows/          # Inngest workflows
│   ├── integrations/       # External integrations
│   ├── tests/              # Test suite
│   └── alembic/            # Database migrations
├── frontend/                # Next.js frontend
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   ├── lib/                # Utilities
│   └── hooks/              # Custom hooks
├── roles/                   # Agent system prompts
├── docs/                    # Documentation
│   └── architecture/       # Architecture docs
├── docker-compose.yml      # Docker composition
└── README.md               # This file
```

## 📚 Documentation

### Core Documentation
- **[Implementation Roadmap](./IMPLEMENTATION_ROADMAP.md)** - Step-by-step development guide
- **[Phase 2 Authentication Complete](./PHASE_2_AUTHENTICATION_COMPLETE.md)** - Authentication implementation details
- **[Architecture Overview](./docs/architecture/overview.md)** - System architecture
- **[Design Principles](./docs/architecture/design-principles.md)** - SOLID, Clean Architecture, DDD
- **[Design Patterns](./docs/architecture/design-patterns.md)** - Patterns used throughout
- **[Scalability](./docs/architecture/scalability.md)** - Scaling strategies
- **[Performance](./docs/architecture/performance.md)** - Optimization techniques

### Template System (NEW!)
- **[Template System Guide](./TEMPLATE_SYSTEM_GUIDE.md)** - Complete template reference guide
- **[Template Implementation Plan](./TEMPLATE_IMPLEMENTATION_PLAN.md)** - Technical implementation details
- **[CLI Tool README](./backend/cli/README.md)** - Command-line interface documentation
- **[Product Roadmap](./PRODUCT_ROADMAP.md)** - Commercialization strategy

### Agent System Prompts

All agent role prompts are in the [`/roles`](./roles) directory:

- [Project Manager](./roles/project_manager/default_prompt.md)
- [Tech Lead](./roles/tech_lead/default_prompt.md)
- [Solution Architect](./roles/solution_architect/default_prompt.md)
- [QA Tester](./roles/tester/default_prompt.md)
- [AI/ML Engineer](./roles/ai_engineer/default_prompt.md)
- [DevOps Engineer](./roles/devops_engineer/default_prompt.md)
- [UI/UX Designer](./roles/designer/default_prompt.md)

**Backend Developers**: Node.js (Express, NestJS, Serverless), Python (FastAPI, Django)
**Frontend Developers**: React + Next.js

## 🧪 Testing

### Run All Tests

#### Backend Tests (Recommended - Inside Docker)

```bash
# Run all backend tests
docker exec agent-squad-backend pytest tests/ -v

# Run with coverage report
docker exec agent-squad-backend pytest tests/ -v --cov=backend --cov-report=term-missing

# Run specific test file
docker exec agent-squad-backend pytest tests/test_security.py -v
docker exec agent-squad-backend pytest tests/test_auth_endpoints.py -v

# Generate HTML coverage report
docker exec agent-squad-backend pytest tests/ --cov=backend --cov-report=html
# View at backend/htmlcov/index.html
```

#### Backend Tests (Local - Without Docker)

```bash
cd backend

# Ensure test database exists
docker exec agent-squad-postgres psql -U postgres -c "CREATE DATABASE agent_squad_test;"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=backend --cov-report=term-missing

# Run specific test categories
pytest tests/test_security.py -v          # Security module tests
pytest tests/test_auth_endpoints.py -v    # Authentication API tests
```

#### Test Results Summary

Current test status:
- ✅ **39 tests** in total
- ✅ **100% passing** (39/39)
- ✅ **85% code coverage** overall
- ✅ **100% coverage** on security module

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch

# Run end-to-end tests
npm run test:e2e
```

## 🔧 Development

### Backend

```bash
# Format code
black backend/

# Lint
ruff check backend/

# Type check
mypy backend/

# Run development server with hot reload
uvicorn backend.core.app:app --reload
```

### Frontend

```bash
# Lint
npm run lint

# Type check
npm run type-check

# Format
npm run format
```

### Database

```bash
cd backend

# Create a new migration (auto-generate from models)
alembic revision --autogenerate -m "migration_name"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Show migration history
alembic history

# View current migration version
alembic current

# Reset database (drop and recreate)
docker exec agent-squad-postgres psql -U postgres -d agent_squad_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

### Database Management

```bash
# Connect to PostgreSQL
docker exec -it agent-squad-postgres psql -U postgres -d agent_squad_dev

# View tables
docker exec agent-squad-postgres psql -U postgres -d agent_squad_dev -c "\dt"

# Backup database
docker exec agent-squad-postgres pg_dump -U postgres agent_squad_dev > backup.sql

# Restore database
docker exec -i agent-squad-postgres psql -U postgres agent_squad_dev < backup.sql
```

## 📋 Pricing Tiers (Planned)

| Tier | Price | Squad Size | Projects | Features |
|------|-------|------------|----------|----------|
| **Starter** | $99/mo | 2-3 members | 2 | Basic integrations |
| **Pro** | $299/mo | 4-7 members | 5 | All features, priority support |
| **Enterprise** | $799/mo | 8-10 members | Unlimited | Everything + SLA |

## 🛣️ Roadmap

- [x] **Phase 1**: Foundation & Setup ✅
- [x] **Phase 2**: Authentication (JWT, password management, email verification) ✅
- [x] **Phase 3**: Agent Framework Integration ✅
- [ ] **Phase 4**: MCP Server Integration (IN PROGRESS) 🟡
- [ ] **Phase 5**: Inngest Workflows
- [ ] **Phase 6**: Frontend Dashboard
- [ ] **Phase 7**: Testing & Deployment
- [ ] **Phase 8**: CLI (Optional)

### Current Status - Phase 4 Starting
✅ **Phase 3 Complete** - 51/51 tests passing (100%)

**Phase 3 Deliverables:**
- ✅ 5 specialized AI agents (PM, Tech Lead, Backend/Frontend Dev, QA)
- ✅ Agent communication system (MessageBus, A2A protocol)
- ✅ 10-state workflow orchestration with smart delegation
- ✅ Collaboration patterns (problem-solving, code review, standups)
- ✅ Context management (RAG + Pinecone, Redis memory)
- ✅ Real-time updates via SSE
- ✅ 41 API endpoints with authentication
- ✅ Comprehensive test suite

**Phase 4 Goals:**
- 🎯 Connect agents to real development tools via MCP
- 🎯 Enable Git operations (clone, read, commit, PR)
- 🎯 Integrate with Jira for ticket management
- 🎯 Allow agents to make actual code changes
- 🎯 End-to-end: Jira ticket → code change → PR

See [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) for detailed timeline.

## 📋 Quick Reference

### Start the App
```bash
# Full stack with Docker
docker-compose up

# Backend only
docker-compose up backend

# Detached mode
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check health
curl http://localhost:8000/health
```

### Run All Tests
```bash
# Inside Docker (recommended)
docker exec agent-squad-backend pytest tests/ -v

# With coverage report
docker exec agent-squad-backend pytest tests/ -v --cov=backend --cov-report=term-missing

# Generate HTML coverage report
docker exec agent-squad-backend pytest tests/ --cov=backend --cov-report=html

# Run specific test file
docker exec agent-squad-backend pytest tests/test_security.py -v
```

### Database Operations
```bash
# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback last migration
alembic downgrade -1

# Show migration history
alembic history

# Reset database
docker exec agent-squad-postgres psql -U postgres -d agent_squad_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head

# Backup database
docker exec agent-squad-postgres pg_dump -U postgres agent_squad_dev > backup.sql

# Restore database
docker exec -i agent-squad-postgres psql -U postgres agent_squad_dev < backup.sql
```

### API Endpoints (Authentication)

All authentication endpoints are available at `/api/v1/auth/*`:

- **POST** `/register` - Register new user
- **POST** `/login` - Login and get tokens
- **GET** `/me` - Get current user profile
- **PUT** `/me` - Update user profile
- **POST** `/refresh` - Refresh access token
- **POST** `/change-password` - Change password
- **POST** `/request-password-reset` - Request password reset
- **POST** `/reset-password` - Reset password with token
- **POST** `/request-email-verification` - Request email verification
- **POST** `/verify-email` - Verify email with token
- **POST** `/logout` - Logout user
- **DELETE** `/me` - Delete user account

### View API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

TBD

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI inspired by [Motion](https://usemotion.com/)
- Agent framework: [agno-agi/agnoframework](https://github.com/agno-agi/agnoframework)

---

**Built with ❤️ to revolutionize software development with AI agents**
