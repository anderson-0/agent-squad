# Agent Squad - Setup Guide

This guide will help you set up the Agent Squad development environment from scratch.

## Prerequisites

Ensure you have the following installed:

- **Docker Desktop** (or Docker Engine + Docker Compose)
- **Node.js** 20+ (for local development without Docker)
- **Python** 3.11+ (for local development without Docker)
- **uv** (Python package manager - for local development)
- **Git**

## Quick Start with Docker (Recommended)

This is the fastest way to get started. Docker Compose will handle all services.

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/agent-squad.git
cd agent-squad
```

### 2. Start All Services

```bash
docker-compose up
```

This will start:
- PostgreSQL database on port 5432
- Redis cache on port 6379
- Backend API on port 8000
- Frontend app on port 3000

**Note**: The first run will take several minutes as Docker builds the images and installs all dependencies.

### 3. Verify Services

Once all services are running, verify them:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 4. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 5. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (will delete database data)
docker-compose down -v
```

## Local Development Setup (Without Docker)

If you prefer to run services locally without Docker:

### 1. Start Database Services

You still need PostgreSQL and Redis. Use Docker for these:

```bash
docker-compose up postgres redis -d
```

### 2. Backend Setup

```bash
cd backend

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with uv (recommended)
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
# Required: DATABASE_URL, REDIS_URL, SECRET_KEY
# Optional: OPENAI_API_KEY, ANTHROPIC_API_KEY, STRIPE_SECRET_KEY, etc.

# Run database migrations
alembic upgrade head

# Start development server
python main.py
```

Backend will be available at http://localhost:8000

### 3. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm ci

# Copy environment file
cp .env.local.example .env.local

# Edit .env.local if needed
# NEXT_PUBLIC_API_URL should point to backend (default: http://localhost:8000)

# Start development server
npm run dev
```

Frontend will be available at http://localhost:3000

## Environment Variables

### Backend (.env)

Required variables:

```env
# Core
ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-min-32-chars

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_squad_dev

# Redis
REDIS_URL=redis://localhost:6379

# API
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

Optional (for full functionality):

```env
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Vector Database
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...
PINECONE_INDEX_NAME=agent-squad

# Payments
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Orchestration
INNGEST_EVENT_KEY=...
INNGEST_SIGNING_KEY=...
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## Database Management

### Create and Run Migrations

```bash
cd backend

# Create a new migration (autogenerate from model changes)
alembic revision --autogenerate -m "your_migration_description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history

# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head
```

### View Database

Use any PostgreSQL client:
- pgAdmin
- DBeaver
- TablePlus
- psql command line

Connection details:
- Host: localhost
- Port: 5432
- Database: agent_squad_dev
- User: postgres
- Password: postgres

### Seed Database (TODO)

```bash
cd backend
python scripts/seed.py
```

## Development Workflow

### Running Tests

Backend:
```bash
cd backend
pytest
pytest --cov=backend --cov-report=html
```

Frontend:
```bash
cd frontend
npm test
npm run test:watch
```

### Code Quality

Backend:
```bash
cd backend

# Format code
black .

# Lint
ruff check .

# Type check
mypy backend/
```

Frontend:
```bash
cd frontend

# Lint
npm run lint

# Type check
npm run type-check

# Format
npm run format
```

### Hot Reload

Both backend and frontend support hot reload:
- **Backend**: Changes to Python files automatically reload the server
- **Frontend**: Changes to React components automatically refresh the browser

## Troubleshooting

### Port Already in Use

If ports 3000, 8000, 5432, or 6379 are already in use:

**Option 1**: Stop the conflicting service

**Option 2**: Change ports in docker-compose.yml:
```yaml
ports:
  - "8001:8000"  # Change host port (left side)
```

### Docker Build Fails

```bash
# Clean up and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Database Connection Issues

Ensure PostgreSQL is running:
```bash
docker-compose ps postgres

# Check logs
docker-compose logs postgres
```

### Migration Errors

```bash
cd backend
# Reset and rerun migrations
alembic downgrade base
alembic upgrade head
```

### Node Modules Issues

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

Once your environment is set up:

1. **Review Documentation**: Check out the [docs](./docs) folder for architecture and design patterns
2. **Explore API**: Visit http://localhost:8000/docs for interactive API documentation
3. **Read Roadmap**: See [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) for development phases
4. **Check Issues**: Look for "good first issue" labels if contributing

## Getting Help

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the [docs](./docs) folder

## Production Deployment

See [docs/deployment.md](./docs/deployment.md) for production deployment instructions (TODO).
