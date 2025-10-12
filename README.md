# Agent Squad - AI-Powered Software Development SaaS

A revolutionary SaaS platform where users can purchase and manage AI-powered software development squads. Each squad consists of specialized AI agents (developers, testers, project managers, etc.) that collaborate to complete software development tasks.

## 🎯 Vision

Enable companies to scale their development capacity on-demand by providing AI agent squads that can autonomously handle software development tasks, from planning to deployment.

## ✨ Features

- **Customizable Squad Building** - Choose 2-10 members with various roles and tech stacks
- **Multi-Project Management** - Connect to Git repos and ticket systems
- **Intelligent Task Orchestration** - AI-powered task breakdown and delegation
- **Real-time Collaboration Dashboard** - Monitor agent communications in real-time
- **Learning & Feedback System** - Agents improve over time with RAG and feedback

## 🏗️ Tech Stack

**Backend**: Python + FastAPI + Prisma + PostgreSQL + Redis
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

### Start All Services with Docker

```bash
# Clone repository
git clone https://github.com/yourusername/agent-squad.git
cd agent-squad

# Start all services (first run will take a few minutes)
docker-compose up
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Verify Setup

```bash
# Run verification script
./scripts/verify-setup.sh
```

### Manual Setup (Without Docker)

#### Backend

```bash
cd backend

# Install dependencies
poetry install  # or: pip install -r requirements.txt

# Generate Prisma client
prisma generate

# Run migrations
prisma db push

# Start server
python main.py
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📁 Project Structure

```
agent-squad/
├── backend/                 # FastAPI backend
│   ├── api/                # API routes
│   ├── core/               # Core functionality
│   ├── services/           # Business logic
│   ├── agents/             # AI agents
│   ├── workflows/          # Inngest workflows
│   └── prisma/             # Database schema
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

- **[Implementation Roadmap](./IMPLEMENTATION_ROADMAP.md)** - Step-by-step development guide
- **[Architecture Overview](./docs/architecture/overview.md)** - System architecture
- **[Design Principles](./docs/architecture/design-principles.md)** - SOLID, Clean Architecture, DDD
- **[Design Patterns](./docs/architecture/design-patterns.md)** - Patterns used throughout
- **[Scalability](./docs/architecture/scalability.md)** - Scaling strategies
- **[Performance](./docs/architecture/performance.md)** - Optimization techniques

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

### Backend Tests

```bash
cd backend
pytest
pytest --cov=backend --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm test
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
# Open Prisma Studio (visual editor)
cd backend && prisma studio

# Create migration
prisma migrate dev --name migration_name

# Reset database
prisma migrate reset
```

## 📋 Pricing Tiers (Planned)

| Tier | Price | Squad Size | Projects | Features |
|------|-------|------------|----------|----------|
| **Starter** | $99/mo | 2-3 members | 2 | Basic integrations |
| **Pro** | $299/mo | 4-7 members | 5 | All features, priority support |
| **Enterprise** | $799/mo | 8-10 members | Unlimited | Everything + SLA |

## 🛣️ Roadmap

- [x] Phase 1: Foundation & Setup
- [ ] Phase 2: Authentication & Payments
- [ ] Phase 3: Agent Framework Integration
- [ ] Phase 4: MCP Server Integration
- [ ] Phase 5: Workflow Orchestration
- [ ] Phase 6: RAG & Knowledge Management
- [ ] Phase 7: Dashboard UI
- [ ] Phase 8: Testing & Deployment
- [ ] Phase 9: CLI (Optional)

See [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) for detailed timeline.

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
