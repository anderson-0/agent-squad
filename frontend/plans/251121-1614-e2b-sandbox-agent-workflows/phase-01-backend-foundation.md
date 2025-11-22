# Phase 01 - Backend Foundation

**Date:** 2025-11-21
**Priority:** P0 (Critical)
**Implementation Status:** Pending
**Review Status:** Not Started

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Dependencies:** None (foundation phase)
- **Related Docs:** [Scout Report](./scout/scout-01-architecture.md)

## Overview

Setup FastAPI backend with PostgreSQL database, authentication, CORS, environment config. Foundation for all E2B and Git operations.

**Why FastAPI:**
- Native Python E2B SDK support
- Async/await for concurrent operations
- Built-in OpenAPI documentation
- High performance (Starlette + Pydantic)

## Key Insights

From research:
- Frontend expects API at `localhost:8000/api/v1`
- Frontend uses axios with auto-refresh on 401
- SSE endpoint needed at `/api/v1/sse`
- HTTP-only cookies for session management

## Requirements

### Functional
- REST API endpoints for agents, tasks, sandboxes
- PostgreSQL schema for metadata persistence
- JWT authentication with refresh tokens
- Environment-based configuration
- CORS for frontend (localhost:3000)
- Health check endpoint

### Non-Functional
- Response time <100ms for API calls
- Database connection pooling
- Graceful shutdown handling
- Structured logging (JSON format)
- OpenAPI docs at /docs

## Architecture

### Tech Stack
```
FastAPI 0.110+
SQLAlchemy 2.0+ (async)
Alembic (migrations)
asyncpg (PostgreSQL driver)
pydantic-settings (config)
python-jose (JWT)
passlib (password hashing)
```

### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance
│   ├── config.py            # Settings (Pydantic)
│   ├── database.py          # SQLAlchemy setup
│   ├── dependencies.py      # Dependency injection
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py    # Main router
│   │   │   ├── agents.py
│   │   │   ├── tasks.py
│   │   │   ├── sandboxes.py
│   │   │   ├── auth.py
│   │   │   └── sse.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── task.py
│   │   ├── sandbox.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── task.py
│   │   ├── sandbox.py
│   │   └── auth.py
│   ├── services/            # Business logic (Phase 02-04)
│   └── utils/
│       ├── __init__.py
│       ├── jwt.py
│       └── logging.py
├── migrations/              # Alembic
├── tests/
├── .env.example
├── .env
├── requirements.txt
├── pyproject.toml
└── README.md
```

### Database Schema

```sql
-- agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'idle',
    current_task_id UUID,
    sandbox_id VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    assigned_agent_id UUID REFERENCES agents(id),
    git_branch VARCHAR(255),
    pull_request_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- sandboxes table
CREATE TABLE sandboxes (
    id VARCHAR(255) PRIMARY KEY,
    agent_id UUID REFERENCES agents(id) NOT NULL,
    task_id UUID REFERENCES tasks(id) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'creating',
    repo_url TEXT,
    branch_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    destroyed_at TIMESTAMP
);

-- git_operations table
CREATE TABLE git_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sandbox_id VARCHAR(255) REFERENCES sandboxes(id),
    operation_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    commit_sha VARCHAR(40),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Related Code Files

### New Files to Create
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/models/*.py` (all models)
- `backend/app/schemas/*.py` (all schemas)
- `backend/app/api/v1/router.py`
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/migrations/env.py` (Alembic)

### Existing Files (No Changes)
- Frontend remains on mock data for this phase

## Implementation Steps

1. **Initialize FastAPI Project**
   - Create backend directory structure
   - Setup pyproject.toml with Poetry or requirements.txt
   - Install dependencies (FastAPI, SQLAlchemy, asyncpg, etc.)

2. **Configuration Management**
   - Create config.py with Pydantic Settings
   - Define env vars: DATABASE_URL, SECRET_KEY, E2B_API_KEY, GITHUB_TOKEN
   - Setup CORS origins from env

3. **Database Setup**
   - Configure SQLAlchemy async engine
   - Create Base model class
   - Setup connection pooling (min=5, max=20)
   - Implement get_db dependency

4. **Create Database Models**
   - Agent model (UUID, name, role, status, sandbox_id)
   - Task model (UUID, title, status, assigned_agent_id, git_branch, pr_url)
   - Sandbox model (id, agent_id, task_id, status, repo_url, branch)
   - GitOperation model (id, sandbox_id, type, status, commit_sha)

5. **Create Pydantic Schemas**
   - AgentCreate, AgentUpdate, AgentResponse
   - TaskCreate, TaskUpdate, TaskResponse
   - SandboxCreate, SandboxResponse
   - Match frontend TypeScript interfaces from scout report

6. **Alembic Migrations**
   - Initialize Alembic: `alembic init migrations`
   - Configure async SQLAlchemy in env.py
   - Create initial migration with all tables
   - Run migration: `alembic upgrade head`

7. **FastAPI App Setup**
   - Create app instance in main.py
   - Add CORS middleware (allow localhost:3000)
   - Add exception handlers (404, 500, validation)
   - Add startup/shutdown events (DB connection)
   - Add health check endpoint: GET /health

8. **API Router Structure**
   - Create v1 router with /api/v1 prefix
   - Mount sub-routers (agents, tasks, sandboxes, auth)
   - Add OpenAPI metadata (title, version, description)

9. **Basic CRUD Endpoints (Stubs)**
   - GET /api/v1/agents (list agents)
   - GET /api/v1/tasks (list tasks)
   - POST /api/v1/agents/{id}/start-task (stub for Phase 02)
   - Return mock data or empty lists for now

10. **Testing Setup**
    - Install pytest, pytest-asyncio, httpx
    - Create conftest.py with test DB fixture
    - Write health check test
    - Write basic CRUD tests

## Todo List

### P0 - Critical

- [ ] Create backend directory structure with all folders
- [ ] Setup requirements.txt with FastAPI, SQLAlchemy, asyncpg, alembic
- [ ] Create config.py with Pydantic Settings for env vars
- [ ] Implement database.py with async SQLAlchemy engine
- [ ] Create all database models (Agent, Task, Sandbox, GitOperation)
- [ ] Create all Pydantic schemas matching frontend types
- [ ] Initialize Alembic and create initial migration
- [ ] Run migration to create tables in PostgreSQL
- [ ] Create main.py with FastAPI app, CORS, exception handlers
- [ ] Implement health check endpoint (GET /health)
- [ ] Create API router structure (/api/v1)
- [ ] Implement stub endpoints for agents and tasks (GET only)
- [ ] Write .env.example with all required variables
- [ ] Test backend starts successfully on localhost:8000
- [ ] Verify OpenAPI docs accessible at /docs

### P1 - Important

- [ ] Add structured JSON logging with request ID
- [ ] Implement database connection pooling config
- [ ] Add graceful shutdown handling
- [ ] Create pytest test suite with fixtures
- [ ] Write tests for health endpoint
- [ ] Document API setup in backend/README.md

### P2 - Nice to Have

- [ ] Add request timing middleware
- [ ] Implement rate limiting (slowapi)
- [ ] Add Prometheus metrics endpoint
- [ ] Setup pre-commit hooks (black, ruff)

## Success Criteria

- [ ] Backend runs on localhost:8000 without errors
- [ ] GET /health returns 200 with {"status": "ok"}
- [ ] GET /api/v1/agents returns empty list or mock data
- [ ] OpenAPI docs visible at /docs with all endpoints
- [ ] Database tables created successfully (verify with psql)
- [ ] CORS allows requests from localhost:3000
- [ ] Environment variables loaded correctly
- [ ] No import errors or dependency issues

## Risk Assessment

**Technical Risks:**
- PostgreSQL connection issues (Docker setup)
- Async SQLAlchemy learning curve
- CORS misconfigurations blocking frontend

**Mitigation:**
- Use docker-compose for PostgreSQL
- Follow FastAPI async patterns documentation
- Test CORS with curl before frontend integration
- Provide .env.example with clear comments

## Security Considerations

- Store SECRET_KEY in env (32+ random bytes)
- Never commit .env to git (add to .gitignore)
- Use password hashing with bcrypt (passlib)
- Validate all input with Pydantic schemas
- Setup HTTPS for production deployment
- Use prepared statements (SQLAlchemy default)

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 30 min | Automated file generation, parallel creation |
| Senior Dev | 3-4 hrs | Familiar with FastAPI, quick setup |
| Junior Dev | 8-10 hrs | Learning FastAPI, SQLAlchemy patterns |

**Complexity:** Medium (standard backend setup)

## Next Steps

After completion:
- [Phase 02 - E2B Sandbox Service](./phase-02-e2b-sandbox-service.md) - Integrate E2B SDK
- [Phase 03 - Git Operations Service](./phase-03-git-operations-service.md) - Git automation
- [Phase 04 - GitHub Integration](./phase-04-github-integration.md) - PR creation

## Unresolved Questions

1. **PostgreSQL hosting:** Local Docker or cloud service (Supabase, Render)?
2. **Authentication:** JWT in headers or HTTP-only cookies?
3. **Secret management:** dotenv only or integrate with vault?
4. **Logging destination:** Stdout only or send to external service (Sentry, LogDNA)?
