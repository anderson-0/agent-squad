# Phase 5: Approach 2 Migration Execution (Conditional)

**Phase:** 5 of 5
**Date:** 2025-11-20
**Priority:** P2 (Conditional - Only if migrating)
**Status:** Pending
**Parent Plan:** [Hybrid E2B Git Integration](plan.md)

---

## Context

**CONDITIONAL PHASE:** Execute only if Phase 4 migration plan approved.

Deploy full service layer with sandbox pooling, distributed locking, and advanced conflict resolution. Canary rollout over 3 weeks ensures zero downtime and instant rollback capability.

**Reference:** [Approach 2 Details](../251120-1909-e2b-sandbox-git-integration/approach-02-enterprise-grade.md)

---

## Overview

Implement Approach 2 components:
- Database models (`GitSandbox`)
- Service layer (`GitSandboxService`)
- Sandbox pool manager (`SandboxPoolManager`)
- Distributed locking (Redis)
- API endpoints (FastAPI)
- Monitoring & cleanup (Celery workers)

Migration executed via canary rollout (10% → 50% → 100%) over 3 weeks.

---

## Key Insights

- **Sandbox pooling**: Reduces E2B costs by 70%+ (reuse vs recreate)
- **Distributed locks**: Prevents concurrent push conflicts across agents
- **Advanced retry**: Exponential backoff with conflict resolution engine
- **Health checks**: Auto-recovery from sandbox failures
- **Comprehensive metrics**: Production-grade observability

---

## Requirements

### Functional
- Sandbox pool (min 3, max 10 sandboxes)
- Distributed locking via Redis
- Auto-retry with exponential backoff
- Health checks and auto-recovery
- API endpoints for CRUD operations

### Non-Functional
- Sandbox allocation < 5 seconds (from pool)
- Git push < 10 seconds (P90)
- Pool reuse rate > 80%
- 99%+ success rate on git operations
- Supports 100+ concurrent agents

---

## Architecture Considerations

### Database Schema
```sql
CREATE TABLE git_sandboxes (
    id SERIAL PRIMARY KEY,
    sandbox_id VARCHAR UNIQUE NOT NULL,
    agent_id VARCHAR NOT NULL,
    task_id VARCHAR NOT NULL,
    repo_url VARCHAR NOT NULL,
    branch VARCHAR DEFAULT 'main',
    agent_branch VARCHAR,
    status VARCHAR DEFAULT 'initializing',  -- initializing, ready, in_use, error, terminated
    last_operation VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    terminated_at TIMESTAMPTZ,
    error_count INT DEFAULT 0,
    last_error VARCHAR,
    config JSONB,
    is_pooled BOOLEAN DEFAULT TRUE,
    pool_size INT DEFAULT 1
);
```

### Sandbox Pool Lifecycle
```
Initialize Pool (min=3)
    ↓
Pre-warm 3 sandboxes → [Pool: idle, idle, idle]
    ↓
Agent requests sandbox → [Pool: idle, idle] [In-use: sandbox1]
    ↓
Health check on return → If healthy → [Pool: idle, idle, sandbox1]
                         If unhealthy → Terminate, create new
```

### Distributed Lock Pattern
```python
async def execute_git_push(sandbox_id, commit_msg):
    lock_key = f"git_push:{sandbox_id}"

    # Acquire Redis lock (TTL=30s prevents deadlock)
    async with redis_lock(lock_key, ttl=30):
        # Pull with rebase
        await sandbox.commands.run("git pull --rebase origin main")

        # Push
        result = await sandbox.commands.run("git push")

        if result.exit_code != 0:
            raise PushError(result.stderr)

    # Lock auto-released after block
```

---

## Related Code Files

### New Files (10+ files)
- `backend/models/git_sandbox.py` (SQLAlchemy model)
- `backend/schemas/git_sandbox.py` (Pydantic schemas)
- `backend/services/git_sandbox_service.py` (core service)
- `backend/services/sandbox_pool_manager.py` (pooling logic)
- `backend/api/v1/endpoints/git_sandbox.py` (REST API)
- `backend/workers/sandbox_cleanup.py` (Celery tasks)
- `alembic/versions/009_add_git_sandbox_tables.py` (migration)
- `backend/integrations/mcp/servers/git_sandbox_mcp_server.py` (MCP wrapper)
- `tests/integration/test_git_sandbox_service.py` (integration tests)
- `tests/unit/test_sandbox_pool_manager.py` (unit tests)

### Modified Files
- `backend/core/config.py` (add Redis, pool config)
- `backend/agents/configuration/mcp_tool_mapping.yaml` (route to new MCP server)

---

## Implementation Steps

### Step 1: Database Layer (Foundation)
- Create `backend/models/git_sandbox.py` (SQLAlchemy model)
- Create `backend/schemas/git_sandbox.py` (Pydantic schemas)
- Create Alembic migration `009_add_git_sandbox_tables.py`
- Run migration: `alembic upgrade head`
- Test model CRUD operations

### Step 2: Sandbox Pool Manager
- Create `backend/services/sandbox_pool_manager.py`
- Implement pool initialization (pre-warm 3 sandboxes)
- Implement `get_sandbox()` (reuse from pool or create new)
- Implement `return_sandbox()` (health check before return)
- Implement `cleanup()` (terminate all sandboxes)
- Add pool size limits (min=3, max=10)

### Step 3: Git Sandbox Service
- Create `backend/services/git_sandbox_service.py`
- Implement `create_sandbox()` (clone repo, setup branch)
- Implement `execute_git_push()` (with distributed lock & retry)
- Implement `execute_git_pull()` (with auto-rebase)
- Implement `execute_git_status()` and `execute_git_diff()`
- Add error handling and logging

### Step 4: Distributed Locking (Redis)
- Add Redis config to `backend/core/config.py`
- Implement `_distributed_lock()` context manager
- Set TTL=30s (prevent deadlocks)
- Add lock acquisition timeout (5s)
- Test lock behavior under concurrent load

### Step 5: API Endpoints
- Create `backend/api/v1/endpoints/git_sandbox.py`
- Implement POST `/git-sandbox/sandboxes` (create)
- Implement POST `/git-sandbox/sandboxes/push` (push changes)
- Implement GET `/git-sandbox/sandboxes/{id}` (get status)
- Implement DELETE `/git-sandbox/sandboxes/{id}` (terminate)
- Add authentication/authorization

### Step 6: MCP Server Wrapper
- Create `backend/integrations/mcp/servers/git_sandbox_mcp_server.py`
- Wrap API endpoints as MCP tools
- Route to `GitSandboxService` instead of direct E2B calls
- Update `mcp_tool_mapping.yaml` to use new server
- Test MCP tool calls from agents

### Step 7: Cleanup Workers (Celery)
- Create `backend/workers/sandbox_cleanup.py`
- Implement `cleanup_expired_sandboxes()` task (every 10 mins)
- Implement `health_check_sandboxes()` task (every 5 mins)
- Add task scheduling to Celery config
- Test worker execution

### Step 8: Monitoring & Metrics
- Add Prometheus metrics (from Phase 2)
- Track pool utilization, reuse rate, lock acquisition time
- Create Grafana dashboard for Approach 2
- Configure alerts for pool exhaustion, lock failures

### Step 9: Integration Testing
- Write integration tests (full workflow: clone → commit → push)
- Test concurrent operations (10 agents pushing simultaneously)
- Test pool exhaustion scenario
- Test Redis lock timeouts
- Test health check recovery

### Step 10: Canary Rollout
- **Week 1**: 10% traffic to Approach 2 (feature flag)
- **Week 2**: 50% traffic (monitor error rates)
- **Week 3**: 100% traffic (Approach 1 as hot backup)
- **Week 4**: Decommission Approach 1

---

## Todo List

### P2: Database Foundation
- [ ] Create `backend/models/git_sandbox.py` (SQLAlchemy model)
- [ ] Create `backend/schemas/git_sandbox.py` (Pydantic schemas)
- [ ] Create `alembic/versions/009_add_git_sandbox_tables.py`
- [ ] Run migration: `alembic upgrade head`
- [ ] Test model CRUD (create, read, update, delete)
- [ ] Add indexes on `sandbox_id`, `agent_id`, `task_id`, `agent_branch`

### P2: Sandbox Pool Manager
- [ ] Create `backend/services/sandbox_pool_manager.py`
- [ ] Implement `__init__()` (min_size=3, max_size=10, ttl=3600)
- [ ] Implement `initialize()` (pre-warm pool)
- [ ] Implement `get_sandbox()` (reuse or create)
- [ ] Implement `return_sandbox()` (health check)
- [ ] Implement `_create_sandbox()` (E2B API call)
- [ ] Implement `_health_check()` (verify sandbox connectivity)
- [ ] Implement `_terminate_sandbox()` (cleanup)
- [ ] Implement `cleanup()` (terminate all)
- [ ] Write unit tests for pool manager

### P2: Git Sandbox Service
- [ ] Create `backend/services/git_sandbox_service.py`
- [ ] Implement `create_sandbox()` (clone repo, setup branch)
- [ ] Implement `execute_git_push()` (stage, commit, pull, push with retry)
- [ ] Implement `execute_git_pull()` (pull with rebase, detect conflicts)
- [ ] Implement `execute_git_status()` (parse git status output)
- [ ] Implement `execute_git_diff()` (return diff output)
- [ ] Add `_configure_git_credentials()` helper
- [ ] Add `_pull_with_rebase()` helper
- [ ] Add `_push_to_remote()` helper
- [ ] Add `_update_sandbox_status()` (database update)

### P2: Distributed Locking
- [ ] Add Redis config to `backend/core/config.py`
- [ ] Implement `_distributed_lock()` context manager
- [ ] Set lock TTL=30s (prevent deadlocks)
- [ ] Add lock acquisition timeout=5s
- [ ] Test lock acquisition under concurrent load
- [ ] Test lock release on exception

### P2: API Endpoints
- [ ] Create `backend/api/v1/endpoints/git_sandbox.py`
- [ ] Implement POST `/git-sandbox/sandboxes` (create)
- [ ] Implement POST `/git-sandbox/sandboxes/push` (push)
- [ ] Implement POST `/git-sandbox/sandboxes/pull` (pull)
- [ ] Implement GET `/git-sandbox/sandboxes/{id}` (status)
- [ ] Implement DELETE `/git-sandbox/sandboxes/{id}` (terminate)
- [ ] Add authentication middleware
- [ ] Write API tests

### P2: MCP Server Wrapper
- [ ] Create `backend/integrations/mcp/servers/git_sandbox_mcp_server.py`
- [ ] Define 5 MCP tools (git_clone, push, pull, status, diff)
- [ ] Wrap API calls (route to GitSandboxService)
- [ ] Update `mcp_tool_mapping.yaml` (switch to new server)
- [ ] Test MCP tool calls from agents
- [ ] Verify backward compatibility

### P2: Cleanup Workers
- [ ] Create `backend/workers/sandbox_cleanup.py`
- [ ] Implement `cleanup_expired_sandboxes()` (every 10 mins)
- [ ] Implement `health_check_sandboxes()` (every 5 mins)
- [ ] Add tasks to Celery config
- [ ] Test worker execution
- [ ] Verify cleanup logic (delete old sandboxes)

### P2: Monitoring & Testing
- [ ] Add Prometheus metrics (pool size, reuse rate, lock time)
- [ ] Update Grafana dashboard (Approach 2 panels)
- [ ] Write integration test: full workflow (clone → push)
- [ ] Write integration test: concurrent operations (10 agents)
- [ ] Write integration test: pool exhaustion
- [ ] Write integration test: Redis lock timeout
- [ ] Write integration test: health check recovery

### P2: Canary Rollout (3 Weeks)
- [ ] Week 1: Enable 10% traffic to Approach 2 (feature flag)
- [ ] Week 1: Monitor error rates, latency, pool utilization
- [ ] Week 2: Increase to 50% traffic
- [ ] Week 2: Monitor data consistency (dual-write validation)
- [ ] Week 3: Increase to 100% traffic
- [ ] Week 3: Keep Approach 1 as hot backup (2 weeks)
- [ ] Week 4: Decommission Approach 1 (remove from codebase)

---

## Success Criteria

### Phase 5 Completion
- ✅ All Approach 2 components deployed
- ✅ Sandbox pool operational (min 3 sandboxes)
- ✅ Distributed locks working (Redis)
- ✅ API endpoints functional
- ✅ MCP tools route to service layer
- ✅ Cleanup workers running (Celery)
- ✅ Integration tests pass

### Migration Success
- ✅ Zero-downtime migration (100% uptime)
- ✅ Data consistency > 99.99%
- ✅ Performance parity or better vs Approach 1
- ✅ Pool reuse rate > 80%
- ✅ P90 latency < 10 seconds
- ✅ Error rate < 1%

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Redis outage breaks locking | Low | High | Fallback to database locks, redundant Redis cluster |
| Sandbox pool exhaustion | Medium | Medium | Auto-scale pool, queue requests |
| E2B API rate limits | Low | Medium | Rate limiting, retry with backoff |
| Database connection pool exhaustion | Low | Medium | Tune pool size, add monitoring |
| Complex conflict scenarios | Medium | Medium | Escalate to PM agent after 3 retries |
| Migration introduces regressions | Low | High | Canary rollout, instant rollback via feature flags |

---

## Security Considerations

- **Redis access control**: Password-protected, internal network only
- **GitHub token scope**: Repo write access only (no admin)
- **Lock audit logs**: Track all lock acquisitions/releases
- **Secrets management**: Use Vault or AWS Secrets Manager for tokens
- **Database encryption**: Encrypt `last_error` field (may contain sensitive data)

---

## Next Steps

### Post-Migration
1. Monitor Approach 2 for 2 weeks (Phase 3 metrics)
2. Optimize pool size based on actual usage
3. Tune Redis lock TTL if deadlocks occur
4. Document lessons learned
5. Decommission Approach 1 codebase

### Future Enhancements
- Multi-region E2B sandboxes for global agents
- Auto-scaling pool based on demand
- Advanced conflict resolution strategies (merge vs rebase)
- Webhook notifications to PM agent on conflicts

---

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 90-120 min | Parallel implementation, automated testing |
| Senior Dev | 2-3 days | Familiar patterns, some research on pooling |
| Junior Dev | 4-6 days | Learning curve: E2B, pooling, distributed systems |

**Complexity:** Complex

---

## Unresolved Questions

1. Redis cluster vs single instance? (High availability vs simplicity)
2. Sandbox TTL: 1 hour, 4 hours, or 24 hours?
3. Conflict escalation: via webhook, message bus, or direct PM agent call?
4. Archive git operations history or purge after N days?
5. Multi-region E2B support needed? (Latency optimization)
6. Auto-scale pool: demand-based or fixed size?
