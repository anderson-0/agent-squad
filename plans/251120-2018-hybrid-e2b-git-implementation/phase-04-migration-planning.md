# Phase 4: Migration Planning (Conditional)

**Phase:** 4 of 5
**Date:** 2025-11-20
**Priority:** P2 (Conditional - Only if migrating)
**Status:** Pending
**Parent Plan:** [Hybrid E2B Git Integration](plan.md)

---

## Context

**CONDITIONAL PHASE:** Execute only if Phase 3 validation identifies migration need (any threshold exceeded for 2+ weeks).

Create detailed migration plan from Approach 1 (simple MCP) to Approach 2 (service layer with pooling). Zero-downtime migration using feature flags and dual-write strategy.

**Reference:** [Migration Strategies](research/migration-strategies.md)

---

## Overview

Design canary rollout migration:
1. Deploy Approach 2 alongside Approach 1
2. Feature flags route traffic gradually (10% → 50% → 100%)
3. Dual-write ensures data consistency
4. Instant rollback via kill-switch
5. Decommission Approach 1 after 2 weeks stable

---

## Key Insights

- **Shadow mode first**: Route reads to Approach 2, compare responses (no user impact)
- **Dual-write pattern**: Write to both systems during migration
- **Feature flags per operation**: Granular control (clone, push, pull independent)
- **Instant rollback**: Kill-switch tested weekly before migration
- **Validation queries**: Detect data divergence early

---

## Requirements

### Functional
- Feature flag system per operation
- Dual-write to both Approach 1 & 2
- Data consistency validation (async reconciliation)
- Rollback capability tested and verified

### Non-Functional
- Migration total duration: 3 weeks
- Zero user-visible downtime
- Data consistency > 99.99%
- Rollback time < 30 seconds

---

## Architecture Considerations

### Feature Flag Routing
```python
class GitOperationRouter:
    def __init__(self, feature_flags):
        self.flags = feature_flags
        self.approach_1 = SimpleMCPGitServer()
        self.approach_2 = ServiceLayerGitSandbox()

    async def route_operation(self, operation, arguments):
        use_service_layer = self.flags.get(f"git.{operation}.use_service_layer")

        if use_service_layer:
            return await self.approach_2.execute(operation, arguments)
        else:
            return await self.approach_1.execute(operation, arguments)
```

### Dual-Write Pattern (Week 1)
```python
async def dual_write_clone(repo_url, agent_id, task_id):
    # Primary: Approach 1
    result_1 = await approach_1.git_clone(repo_url, agent_id, task_id)

    # Shadow: Approach 2 (async, non-blocking)
    asyncio.create_task(
        approach_2.git_clone(repo_url, agent_id, task_id)
    )

    return result_1  # User sees Approach 1 result
```

### Validation Query (Detect Divergence)
```sql
-- Check for missing sandboxes in Approach 2
SELECT COUNT(*) FROM approach_1.sandboxes
WHERE id NOT IN (SELECT id FROM approach_2.sandboxes);

-- Check for data lag
SELECT AVG(EXTRACT(EPOCH FROM (approach_2.updated_at - approach_1.updated_at)))
FROM approach_1.sandboxes a1
JOIN approach_2.sandboxes a2 ON a1.id = a2.id;
```

---

## Related Code Files

### New Files
- `backend/services/git_operation_router.py` (feature flag routing)
- `backend/core/feature_flags.py` (centralized flag management)
- `backend/services/git_sandbox_service.py` (Approach 2 implementation)
- `backend/services/sandbox_pool_manager.py` (Approach 2 pooling)
- `backend/models/git_sandbox.py` (Approach 2 database model)
- `backend/workers/sandbox_reconciliation.py` (dual-write validation)

### Modified Files
- `backend/integrations/mcp/servers/git_operations_server.py` (add router)
- `backend/core/config.py` (add feature flag config)

### Migration Files
- `alembic/versions/009_add_git_sandbox_tables.py` (Approach 2 schema)
- `scripts/migrate_sandbox_state.py` (data migration script)

---

## Implementation Steps

### Step 1: Feature Flag Setup
- Add feature flag library (`flagsmith`, `launchdarkly`, or custom)
- Define flags: `git.clone.use_service_layer`, `git.push.use_service_layer`, etc.
- Create flag management API/UI
- Test flag toggling (instant effect)

### Step 2: Implement Router Layer
- Create `GitOperationRouter` class
- Add routing logic based on feature flags
- Integrate router into `git_operations_server.py`
- Test routing switches between Approach 1 & 2

### Step 3: Deploy Approach 2 Infrastructure
- Run Alembic migration (add `git_sandboxes` table)
- Deploy `GitSandboxService` and `SandboxPoolManager`
- Initialize sandbox pool (min 3 sandboxes)
- Deploy Redis for distributed locks
- Test Approach 2 independently (dev environment)

### Step 4: Implement Dual-Write
- Modify router to write to both systems
- Add async reconciliation job (every 5 mins)
- Create validation queries (detect divergence)
- Set alert: >0.1% mismatch triggers notification

### Step 5: Test Rollback Mechanism
- Implement kill-switch (instant flag toggle)
- Run chaos test (flip flag on/off every 30s)
- Verify no lock leaks or session issues
- Validate rollback time < 30 seconds

### Step 6: Create Migration Timeline
- Week 1: Shadow mode (10% traffic to Approach 2 read-only)
- Week 2: Dual-write (50% traffic, both systems active)
- Week 3: Cutover (100% Approach 2, Approach 1 hot backup)
- Week 4: Decommission Approach 1

### Step 7: Define Rollback Triggers
- Error rate > 5% in Approach 2
- P95 latency > 2x Approach 1 baseline
- Data consistency < 99.99%
- Any critical incident

### Step 8: Document Migration Plan
- Create migration runbook
- Define go/no-go criteria
- Assign roles (migration lead, on-call, rollback authority)
- Schedule migration windows

---

## Todo List

### P2: Feature Flag Infrastructure
- [ ] Choose feature flag library (flagsmith, launchdarkly, or custom)
- [ ] Add library to `requirements.txt`
- [ ] Create `backend/core/feature_flags.py`
- [ ] Define flags: `git.clone.use_service_layer`, `git.push.use_service_layer`
- [ ] Create flag management API (enable/disable via REST)
- [ ] Test flag toggling (verify instant effect)

### P2: Router Implementation
- [ ] Create `backend/services/git_operation_router.py`
- [ ] Implement `GitOperationRouter` class
- [ ] Add routing logic (if flag=true → Approach 2, else → Approach 1)
- [ ] Integrate router into `git_operations_server.py`
- [ ] Write unit tests for router (flag toggle switches backend)
- [ ] Test router in dev environment

### P2: Approach 2 Deployment
- [ ] Deploy Approach 2 service layer (from Phase 5 plan)
- [ ] Run Alembic migration: `009_add_git_sandbox_tables.py`
- [ ] Initialize sandbox pool (min 3 sandboxes)
- [ ] Deploy Redis for distributed locks
- [ ] Test Approach 2 independently (isolated from Approach 1)
- [ ] Verify Approach 2 git operations work end-to-end

### P2: Dual-Write Implementation
- [ ] Modify router to write to both Approach 1 & 2
- [ ] Add async write to Approach 2 (non-blocking)
- [ ] Create reconciliation job: `backend/workers/sandbox_reconciliation.py`
- [ ] Implement validation queries (detect divergence)
- [ ] Set alert: mismatch rate > 0.1%
- [ ] Test dual-write (verify both systems stay in sync)

### P2: Rollback Mechanism
- [ ] Implement kill-switch (instant flag toggle to Approach 1)
- [ ] Create rollback runbook
- [ ] Run chaos test (flip flag on/off every 30s for 5 mins)
- [ ] Verify no lock leaks or resource issues
- [ ] Measure rollback time (target: < 30 seconds)
- [ ] Document rollback triggers and procedure

### P2: Migration Timeline & Documentation
- [ ] Define migration timeline (Week 1: shadow, Week 2: dual-write, Week 3: cutover)
- [ ] Create go/no-go criteria for each week
- [ ] Assign migration roles (lead, on-call, rollback authority)
- [ ] Schedule migration windows (prefer low-traffic times)
- [ ] Create migration runbook (step-by-step)
- [ ] Review plan with stakeholders

---

## Success Criteria

### Planning Phase
- ✅ Feature flag system operational
- ✅ Router layer tested (switches backends correctly)
- ✅ Approach 2 deployed and validated independently
- ✅ Dual-write tested (data consistency verified)
- ✅ Rollback tested (< 30s recovery time)
- ✅ Migration runbook approved

### Pre-Migration Checklist
- ✅ Approach 2 passes all integration tests
- ✅ Sandbox pool initialized and healthy
- ✅ Redis cluster operational
- ✅ Feature flags tested (no issues)
- ✅ Rollback procedure validated
- ✅ Team trained on migration process

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Lost writes during cutover | Low | High | Dual-write with async validation |
| Lock deadlocks in Approach 2 | Medium | Medium | Weekly chaos tests, timeout configs |
| Schema divergence | Low | Medium | Validation queries, CDC-based sync |
| High latency (pooling overhead) | Medium | Medium | Performance benchmarks before cutover |
| Rollback fails under load | Low | High | Weekly rollback drills, tested on production clone |

---

## Security Considerations

- **Lock state transition**: Ensure in-memory locks (Approach 1) → Redis locks (Approach 2) handled gracefully
- **Credential migration**: Verify GitHub tokens work in Approach 2 sandbox env vars
- **Data consistency**: Reconciliation job must not log sensitive data
- **Feature flag access**: Restrict flag toggling to authorized users only

---

## Next Steps

### If Migration Approved
1. Execute all P2 checklist items (setup flags, deploy Approach 2, test dual-write)
2. Schedule migration window with team
3. Run final pre-migration checklist
4. Proceed to Phase 5: Execute migration

### If Migration Not Needed
1. Skip this phase entirely
2. Close Phase 5 as not applicable
3. Return to quarterly re-evaluation cycle

---

## Time Estimates

| Executor | Time | Notes |
|----------|------|-------|
| Claude | 20-30 min | Automated config generation, script creation |
| Senior Dev | 3-4 hrs | Feature flag setup, router implementation, testing |
| Junior Dev | 6-8 hrs | Learning feature flags, dual-write patterns |

**Complexity:** Medium

---

## Unresolved Questions

1. Feature flag library: Self-hosted or SaaS (flagsmith vs launchdarkly)?
2. Lock reuse during transition: How to handle sandboxes with existing in-memory locks?
3. Redis failure mode: Fall back to in-memory locks or fail fast?
4. Migration window: Weekday evening or weekend?
5. Rollback authority: Who has final say to trigger rollback?
