# Approach 2: Enterprise Grade - Dedicated Git Sandbox Service

## Overview

Production-ready git sandbox service with pooling, distributed locking, advanced conflict resolution, comprehensive monitoring.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Agent (Agno)                              │
│  - Backend Developer Agent                                      │
│  - Frontend Developer Agent                                     │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼ MCP Tool Call
┌─────────────────────────────────────────────────────────────────┐
│          Git Sandbox MCP Server (NEW)                           │
│  Tools: git_clone, git_pull, git_push, git_status, git_diff    │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼ Service Layer Call
┌─────────────────────────────────────────────────────────────────┐
│            GitSandboxService (NEW)                              │
│  - create_sandbox(repo_url, agent_id, task_id)                 │
│  - execute_git_operation(sandbox_id, operation)                │
│  - handle_conflicts(sandbox_id, strategy)                      │
│  - release_sandbox(sandbox_id)                                 │
└──────┬──────────────────────────┬───────────────────────────────┘
       │                          │
       ▼                          ▼
┌──────────────────┐    ┌─────────────────────────┐
│ SandboxPool      │    │  ConflictResolver       │
│ Manager          │    │  - auto_rebase          │
│ - get_sandbox()  │    │  - merge_strategy       │
│ - return()       │    │  - escalate_to_pm       │
│ - cleanup()      │    └─────────────────────────┘
└───────┬──────────┘
        │
        ▼ Pool Management
┌──────────────────────────────────────────────────────────────────┐
│                   Sandbox Pool                                   │
│  [Sandbox 1: idle]  [Sandbox 2: in-use]  [Sandbox 3: idle]     │
└──────────────────────────────────────────────────────────────────┘
        │
        ▼ Create/Reuse E2B Sandboxes
┌──────────────────────────────────────────────────────────────────┐
│                  E2B Sandboxes (Firecracker VMs)                 │
│  Sandbox 1:                  Sandbox 2:                         │
│  /workspace/repo/            /workspace/repo/                   │
│  - agent-1-task-1            - agent-2-task-2                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    Supporting Infrastructure                      │
│                                                                   │
│  ┌───────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ PostgreSQL    │  │ Redis          │  │ Prometheus       │   │
│  │ - Sandbox     │  │ - Distributed  │  │ - Metrics        │   │
│  │   state       │  │   locks        │  │ - Dashboards     │   │
│  │ - Operations  │  │ - Lease TTL    │  │                  │   │
│  └───────────────┘  └────────────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Database Model: `git_sandbox.py`

**Location:** `backend/models/git_sandbox.py`

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from backend.models.base import Base

class GitSandbox(Base):
    """Track E2B sandboxes for git operations"""
    __tablename__ = "git_sandboxes"

    id = Column(Integer, primary_key=True)
    sandbox_id = Column(String, unique=True, index=True)  # E2B sandbox ID
    agent_id = Column(String, index=True)
    task_id = Column(String, index=True)

    # Repository info
    repo_url = Column(String, nullable=False)
    branch = Column(String, default="main")
    agent_branch = Column(String, index=True)  # agent-{id}-{task_id}

    # Status
    status = Column(String, default="initializing")  # initializing, ready, in_use, error, terminated
    last_operation = Column(String)  # clone, pull, push, etc.

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), onupdate=func.now())
    terminated_at = Column(DateTime(timezone=True))

    # Error tracking
    error_count = Column(Integer, default=0)
    last_error = Column(String)

    # Configuration
    config = Column(JSON, default={})  # Custom sandbox config

    # Pooling
    is_pooled = Column(Boolean, default=True)  # Can be reused
    pool_size = Column(Integer, default=1)

    def __repr__(self):
        return f"<GitSandbox(id={self.id}, sandbox_id={self.sandbox_id}, status={self.status})>"
```

### 2. Pydantic Schemas: `git_sandbox.py`

**Location:** `backend/schemas/git_sandbox.py`

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class GitSandboxCreate(BaseModel):
    repo_url: str
    agent_id: str
    task_id: str
    branch: str = "main"
    is_pooled: bool = True

class GitSandboxResponse(BaseModel):
    id: int
    sandbox_id: str
    agent_id: str
    task_id: str
    repo_url: str
    branch: str
    agent_branch: str
    status: str
    created_at: datetime
    last_used_at: Optional[datetime]

class GitOperationRequest(BaseModel):
    sandbox_id: str
    operation: str  # clone, pull, push, status, diff
    params: dict = {}

class GitPushRequest(BaseModel):
    sandbox_id: str
    commit_message: str
    files: List[str] = []
    auto_retry: bool = True
    max_retries: int = 3

class GitPullRequest(BaseModel):
    sandbox_id: str
    auto_rebase: bool = True
    conflict_strategy: str = "rebase"  # rebase, merge, abort

class ConflictResolutionResponse(BaseModel):
    success: bool
    conflicts: List[str]
    resolution_strategy: str
    escalated_to_pm: bool = False
```

### 3. Service: `git_sandbox_service.py`

**Location:** `backend/services/git_sandbox_service.py`

```python
import asyncio
from typing import Optional, Dict, List
from e2b_code_interpreter import Sandbox
from backend.models.git_sandbox import GitSandbox
from backend.core.database import get_db_context
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GitSandboxService:
    """
    Manage git operations in E2B sandboxes

    Features:
    - Sandbox pooling and reuse
    - Distributed locking via Redis
    - Advanced conflict resolution
    - Automatic retry with backoff
    - Comprehensive metrics
    """

    def __init__(self, pool_manager: 'SandboxPoolManager'):
        self.pool_manager = pool_manager
        self.e2b_api_key = settings.E2B_API_KEY
        self.github_token = settings.GITHUB_TOKEN

    async def create_sandbox(
        self,
        repo_url: str,
        agent_id: str,
        task_id: str,
        branch: str = "main"
    ) -> GitSandbox:
        """Create or reuse sandbox for git operations"""

        # Try to get sandbox from pool
        sandbox = await self.pool_manager.get_sandbox()

        if not sandbox:
            # Create new E2B sandbox
            sandbox = await self._create_new_sandbox()

        # Configure git credentials
        await self._configure_git_credentials(sandbox)

        # Clone repository
        agent_branch = f"agent-{agent_id}-{task_id}"
        await self._clone_repository(sandbox, repo_url, branch, agent_branch)

        # Save to database
        async with get_db_context() as db:
            db_sandbox = GitSandbox(
                sandbox_id=sandbox.sandbox_id,
                agent_id=agent_id,
                task_id=task_id,
                repo_url=repo_url,
                branch=branch,
                agent_branch=agent_branch,
                status="ready",
                last_operation="clone"
            )
            db.add(db_sandbox)
            await db.commit()
            await db.refresh(db_sandbox)

        return db_sandbox

    async def execute_git_push(
        self,
        sandbox_id: str,
        commit_message: str,
        files: List[str] = [],
        max_retries: int = 3
    ) -> Dict:
        """Push changes with automatic conflict resolution"""

        sandbox = await self.pool_manager.get_by_id(sandbox_id)
        if not sandbox:
            raise ValueError(f"Sandbox {sandbox_id} not found")

        # Acquire distributed lock
        lock_key = f"git_push:{sandbox_id}"
        async with self._distributed_lock(lock_key):

            # Stage files
            await self._stage_files(sandbox, files)

            # Commit
            commit_hash = await self._commit_changes(sandbox, commit_message)

            # Push with retry
            for attempt in range(max_retries):
                try:
                    # Pull with rebase
                    await self._pull_with_rebase(sandbox)

                    # Push
                    result = await self._push_to_remote(sandbox)

                    if result["success"]:
                        # Update database
                        await self._update_sandbox_status(sandbox_id, "ready", "push")
                        return {
                            "success": True,
                            "commit_hash": commit_hash,
                            "attempts": attempt + 1
                        }

                except ConflictError as e:
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        # Escalate to PM agent
                        return await self._escalate_conflict(sandbox_id, e)

        return {"success": False, "error": "Max retries exceeded"}

    async def _configure_git_credentials(self, sandbox: Sandbox):
        """Configure git credentials in sandbox"""
        credential_helper = (
            "git config --global credential.helper "
            "'!f() { echo \"username=token\"; echo \"password=$GITHUB_TOKEN\"; }; f'"
        )

        result = await asyncio.to_thread(
            sandbox.commands.run,
            credential_helper
        )

        if result.exit_code != 0:
            raise RuntimeError(f"Failed to configure git credentials: {result.stderr}")

    async def _pull_with_rebase(self, sandbox: Sandbox):
        """Pull latest changes with rebase"""
        result = await asyncio.to_thread(
            sandbox.commands.run,
            "cd /workspace/repo && git pull --rebase origin main"
        )

        if "CONFLICT" in result.stdout:
            raise ConflictError(f"Rebase conflict: {result.stdout}")

        if result.exit_code != 0:
            raise RuntimeError(f"Pull failed: {result.stderr}")

    async def _distributed_lock(self, key: str, ttl: int = 30):
        """Distributed lock using Redis"""
        from backend.core.redis import get_redis

        redis = await get_redis()
        lock_acquired = await redis.set(key, "locked", nx=True, ex=ttl)

        if not lock_acquired:
            raise LockAcquisitionError(f"Could not acquire lock: {key}")

        try:
            yield
        finally:
            await redis.delete(key)

class ConflictError(Exception):
    """Git conflict error"""
    pass

class LockAcquisitionError(Exception):
    """Failed to acquire distributed lock"""
    pass
```

### 4. Sandbox Pool Manager: `sandbox_pool_manager.py`

**Location:** `backend/services/sandbox_pool_manager.py`

```python
from typing import Optional, List
from e2b_code_interpreter import Sandbox
from backend.core.config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

class SandboxPoolManager:
    """
    Manage pool of E2B sandboxes for reuse

    Features:
    - Pre-warm sandboxes for fast allocation
    - Health checks and auto-recovery
    - TTL-based expiration
    - Size limits and overflow handling
    """

    def __init__(
        self,
        min_size: int = 3,
        max_size: int = 10,
        sandbox_ttl: int = 3600  # 1 hour
    ):
        self.min_size = min_size
        self.max_size = max_size
        self.sandbox_ttl = sandbox_ttl

        self._pool: List[Sandbox] = []
        self._in_use: Dict[str, Sandbox] = {}
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Pre-warm sandbox pool"""
        logger.info(f"Initializing sandbox pool (min_size={self.min_size})")

        for _ in range(self.min_size):
            sandbox = await self._create_sandbox()
            self._pool.append(sandbox)

        logger.info(f"Sandbox pool initialized with {len(self._pool)} sandboxes")

    async def get_sandbox(self) -> Optional[Sandbox]:
        """Get sandbox from pool or create new one"""
        async with self._lock:
            # Try to get from pool
            if self._pool:
                sandbox = self._pool.pop()
                self._in_use[sandbox.sandbox_id] = sandbox
                logger.debug(f"Reused sandbox from pool: {sandbox.sandbox_id}")
                return sandbox

            # Create new if under max size
            if len(self._in_use) < self.max_size:
                sandbox = await self._create_sandbox()
                self._in_use[sandbox.sandbox_id] = sandbox
                logger.debug(f"Created new sandbox: {sandbox.sandbox_id}")
                return sandbox

            # Pool exhausted
            logger.warning("Sandbox pool exhausted, waiting for available sandbox")
            return None

    async def return_sandbox(self, sandbox_id: str):
        """Return sandbox to pool"""
        async with self._lock:
            sandbox = self._in_use.pop(sandbox_id, None)

            if not sandbox:
                logger.warning(f"Sandbox {sandbox_id} not found in use")
                return

            # Health check before returning to pool
            is_healthy = await self._health_check(sandbox)

            if is_healthy and len(self._pool) < self.max_size:
                self._pool.append(sandbox)
                logger.debug(f"Returned sandbox to pool: {sandbox_id}")
            else:
                # Terminate unhealthy or excess sandboxes
                await self._terminate_sandbox(sandbox)
                logger.debug(f"Terminated sandbox: {sandbox_id}")

    async def _create_sandbox(self) -> Sandbox:
        """Create new E2B sandbox"""
        sandbox = await asyncio.to_thread(
            Sandbox.create,
            api_key=settings.E2B_API_KEY,
            envs={"GITHUB_TOKEN": settings.GITHUB_TOKEN}
        )
        return sandbox

    async def _health_check(self, sandbox: Sandbox) -> bool:
        """Check if sandbox is healthy"""
        try:
            result = await asyncio.to_thread(
                sandbox.commands.run,
                "echo 'health_check'"
            )
            return result.exit_code == 0
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def _terminate_sandbox(self, sandbox: Sandbox):
        """Terminate sandbox"""
        try:
            await asyncio.to_thread(sandbox.kill)
        except Exception as e:
            logger.error(f"Failed to terminate sandbox: {e}")

    async def cleanup(self):
        """Cleanup all sandboxes"""
        logger.info("Cleaning up sandbox pool")

        for sandbox in self._pool:
            await self._terminate_sandbox(sandbox)

        for sandbox in self._in_use.values():
            await self._terminate_sandbox(sandbox)

        self._pool.clear()
        self._in_use.clear()
```

### 5. API Endpoints: `git_sandbox.py`

**Location:** `backend/api/v1/endpoints/git_sandbox.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from backend.schemas.git_sandbox import (
    GitSandboxCreate,
    GitSandboxResponse,
    GitPushRequest
)
from backend.services.git_sandbox_service import GitSandboxService
from backend.services.sandbox_pool_manager import SandboxPoolManager

router = APIRouter(prefix="/git-sandbox", tags=["git-sandbox"])

# Dependency injection
pool_manager = SandboxPoolManager()
git_service = GitSandboxService(pool_manager)

@router.post("/sandboxes", response_model=GitSandboxResponse)
async def create_sandbox(request: GitSandboxCreate):
    """Create new git sandbox"""
    sandbox = await git_service.create_sandbox(
        repo_url=request.repo_url,
        agent_id=request.agent_id,
        task_id=request.task_id,
        branch=request.branch
    )
    return sandbox

@router.post("/sandboxes/push")
async def push_changes(request: GitPushRequest):
    """Push changes to remote repository"""
    result = await git_service.execute_git_push(
        sandbox_id=request.sandbox_id,
        commit_message=request.commit_message,
        files=request.files,
        max_retries=request.max_retries
    )
    return result

@router.get("/sandboxes/{sandbox_id}")
async def get_sandbox_status(sandbox_id: str):
    """Get sandbox status"""
    # Implementation
    pass

@router.delete("/sandboxes/{sandbox_id}")
async def terminate_sandbox(sandbox_id: str):
    """Terminate sandbox and remove from pool"""
    # Implementation
    pass
```

### 6. Celery Worker: `sandbox_cleanup.py`

**Location:** `backend/workers/sandbox_cleanup.py`

```python
from celery import Celery
from backend.core.config import settings
from backend.services.sandbox_pool_manager import SandboxPoolManager

celery_app = Celery("sandbox_cleanup")

@celery_app.task
def cleanup_expired_sandboxes():
    """
    Periodic task to cleanup expired sandboxes

    Runs every 10 minutes
    - Terminates sandboxes older than TTL
    - Removes from database
    - Updates metrics
    """
    # Implementation
    pass

@celery_app.task
def health_check_sandboxes():
    """
    Periodic task to health check sandboxes

    Runs every 5 minutes
    - Verify sandbox connectivity
    - Remove unhealthy sandboxes
    - Backfill pool if needed
    """
    pass
```

### 7. Migration: `009_add_git_sandbox_tables.py`

**Location:** `backend/alembic/versions/009_add_git_sandbox_tables.py`

```python
"""Add git sandbox tables

Revision ID: 009
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'git_sandboxes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sandbox_id', sa.String(), unique=True, index=True),
        sa.Column('agent_id', sa.String(), index=True),
        sa.Column('task_id', sa.String(), index=True),
        sa.Column('repo_url', sa.String(), nullable=False),
        sa.Column('branch', sa.String(), default='main'),
        sa.Column('agent_branch', sa.String(), index=True),
        sa.Column('status', sa.String(), default='initializing'),
        sa.Column('last_operation', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
        sa.Column('terminated_at', sa.DateTime(timezone=True)),
        sa.Column('error_count', sa.Integer(), default=0),
        sa.Column('last_error', sa.String()),
        sa.Column('config', sa.JSON(), default={}),
        sa.Column('is_pooled', sa.Boolean(), default=True),
        sa.Column('pool_size', sa.Integer(), default=1),
    )

def downgrade():
    op.drop_table('git_sandboxes')
```

## Implementation Phases

### Phase 1: Foundation (P0)
**Priority:** P0

**Tasks:**
- [ ] Create database model `GitSandbox`
- [ ] Create Pydantic schemas
- [ ] Create migration file
- [ ] Run migration to create tables
- [ ] Create basic `GitSandboxService` (no pooling yet)
- [ ] Write unit tests for models/schemas

**Time:** Claude: 20 min, Senior: 4 hrs, Junior: 8 hrs

**Success Criteria:**
- Tables created successfully
- Models work with async SQLAlchemy
- Schemas validate correctly

### Phase 2: Sandbox Pool Manager (P0)
**Priority:** P0

**Tasks:**
- [ ] Implement `SandboxPoolManager`
- [ ] Add pool initialization
- [ ] Add get/return sandbox logic
- [ ] Add health checks
- [ ] Write unit tests for pool manager

**Time:** Claude: 25 min, Senior: 6 hrs, Junior: 12 hrs

**Success Criteria:**
- Pool pre-warms sandboxes on startup
- Sandboxes reused correctly
- Health checks detect failures
- Pool size limits enforced

### Phase 3: Git Operations (P0)
**Priority:** P0

**Tasks:**
- [ ] Implement git clone in service
- [ ] Implement git push with retry
- [ ] Implement git pull with rebase
- [ ] Add credential management
- [ ] Write integration tests

**Time:** Claude: 30 min, Senior: 8 hrs, Junior: 16 hrs

**Success Criteria:**
- All git operations work correctly
- Credentials injected securely
- Auto-retry on conflicts
- Integration tests pass

### Phase 4: Distributed Locking (P1)
**Priority:** P1

**Tasks:**
- [ ] Integrate Redis for distributed locks
- [ ] Implement lock acquisition/release
- [ ] Add lock TTL and deadlock prevention
- [ ] Test concurrent push operations

**Time:** Claude: 15 min, Senior: 3 hrs, Junior: 6 hrs

**Success Criteria:**
- Locks prevent concurrent push conflicts
- Deadlocks prevented via TTL
- Concurrent operations tested

### Phase 5: API Endpoints (P1)
**Priority:** P1

**Tasks:**
- [ ] Create API router
- [ ] Implement CRUD endpoints
- [ ] Add authentication/authorization
- [ ] Write API tests

**Time:** Claude: 10 min, Senior: 2 hrs, Junior: 4 hrs

**Success Criteria:**
- All endpoints functional
- Auth enforced
- API tests pass

### Phase 6: Monitoring & Cleanup (P2)
**Priority:** P2

**Tasks:**
- [ ] Add Prometheus metrics
- [ ] Create Celery cleanup tasks
- [ ] Add dashboard configuration
- [ ] Document metrics

**Time:** Claude: 10 min, Senior: 2 hrs, Junior: 4 hrs

**Success Criteria:**
- Metrics exported to Prometheus
- Cleanup tasks run periodically
- Dashboard shows key metrics

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 90-120 min | Parallel implementation, automated testing |
| Senior Dev | 2-3 days | Familiar patterns, some research on pooling |
| Junior Dev | 4-6 days | Learning curve: E2B, pooling, distributed systems |

**Complexity:** Complex

## Success Criteria

1. **Functional:**
   - ✅ Sandbox pooling works (3-10 sandboxes)
   - ✅ Git operations (clone, push, pull) work
   - ✅ Distributed locking prevents conflicts
   - ✅ Auto-retry with exponential backoff
   - ✅ Health checks detect failures

2. **Performance:**
   - ✅ Sandbox allocation < 5 seconds (from pool)
   - ✅ Git push < 10 seconds (90th percentile)
   - ✅ Pool reuse rate > 80%

3. **Scalability:**
   - ✅ Supports 100+ concurrent agents
   - ✅ Handles 1000+ git operations/hour
   - ✅ Auto-scales pool based on demand

4. **Reliability:**
   - ✅ 99%+ success rate on git operations
   - ✅ Automatic recovery from transient failures
   - ✅ Conflict resolution success > 95%

## Monitoring & Metrics

### Prometheus Metrics
```python
# Sandbox pool metrics
sandbox_pool_size_total
sandbox_pool_available
sandbox_pool_in_use
sandbox_creation_total
sandbox_reuse_rate

# Git operation metrics
git_operation_duration_seconds
git_operation_total{operation, status}
git_conflict_total
git_conflict_resolved_total
git_push_retry_count

# Error metrics
sandbox_error_total{error_type}
lock_acquisition_failed_total
```

### Grafana Dashboard
- Sandbox pool utilization
- Git operation success rate
- Conflict resolution rate
- Average operation duration
- Error rate by type

## Trade-offs

### Pros
1. **Production-ready:** Battle-tested patterns
2. **Scalable:** Handles 100+ concurrent agents
3. **Cost-optimized:** Sandbox pooling reduces E2B costs by 70%+
4. **Resilient:** Distributed locks, auto-retry, health checks
5. **Observable:** Comprehensive metrics and dashboards

### Cons
1. **Complex:** More code to maintain
2. **Infrastructure:** Requires Redis for locking
3. **Learning curve:** Distributed systems concepts
4. **Longer implementation:** 2-3 days vs 4-6 hours
5. **Testing:** More edge cases to cover

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Redis outage breaks locking | Low | High | Fallback to database-based locks |
| Sandbox pool exhaustion | Medium | Medium | Auto-scale pool, queue requests |
| E2B API rate limits | Low | Medium | Rate limiting, retry with backoff |
| Database connection pool exhaustion | Low | Medium | Connection pool tuning, monitoring |
| Complex conflict scenarios | Medium | Medium | Escalate to PM agent after N retries |

## Unresolved Questions

1. Redis cluster or single instance for locks?
2. Sandbox pool auto-scaling strategy (demand-based vs fixed)?
3. Conflict escalation to PM: via webhook or message bus?
4. Sandbox TTL: 1 hour, 4 hours, or 24 hours?
5. Archive git operations history or purge after N days?
6. Multi-region E2B sandboxes for global agents?
