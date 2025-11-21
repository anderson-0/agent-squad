# Zero-Downtime Migration Strategies: Simple MCP → Full Service Layer

**Date:** 2025-11-20
**Context:** Migrating from simple MCP server (Approach 1) to service-layer with pooling & distributed locks (Approach 2)

---

## 1. Feature Flag Patterns for Gradual Rollout

### Shadow Mode (Read-Only)
- Route read traffic to new system in parallel, compare responses (no user impact)
- Identifies inconsistencies before writing
- Typical timeline: 1-2 weeks, 0.1%-100% user population
- **Source:** AWS Database Modernizer Workshop (Nov 2024)

### Canary Rollout
- Deploy Approach 2 to 5-10% of traffic initially
- Monitor metrics (latency, errors, resource usage) vs Approach 1
- Ramp 10% → 50% → 100% over 2-3 weeks
- Instant rollback via feature flag if issues detected
- **Tool:** LaunchDarkly, DevCycle (Dec 2024 patterns)

### Kill Switch
- Feature flag per sandbox operation (create, read, update, delete)
- Each operation independently switchable: `sandbox.routing.use_service_layer`
- Enables granular rollback (e.g., revert writes, keep reads)

---

## 2. Dual-Write Strategy

### Three-Phase Approach

**Phase 1: Dual Write (Week 1-2)**
```
MCP Server Input
  ↓
Write to Simple MCP (Approach 1) ✓
Write to Service Layer (Approach 2) ✓
  ↓
Read from Simple MCP (Approach 1)
```
- Both systems stay synchronized
- Approach 2 data trails behind slightly (async write)
- Detects write inconsistencies early

**Phase 2: Dual Read (Week 2-3)**
```
MCP Server Input
  ↓
Write to Service Layer (Approach 2) PRIMARY
Write to Simple MCP (Approach 1) SHADOW
  ↓
Read from Service Layer (Approach 2)
Validate against Simple MCP (Approach 1) in background
```
- Approach 2 is primary; Approach 1 is verification only
- Catches read-side inconsistencies before full migration

**Phase 3: Cutover (Week 3)**
```
MCP Server Input
  ↓
Write to Service Layer (Approach 2) ONLY
  ↓
Read from Service Layer (Approach 2) ONLY
(Simple MCP deprecated, kept for 2-4 weeks as cold backup)
```

---

## 3. Data Migration for Sandbox State Tracking

### Pre-Migration Audit
1. Snapshot all sandbox state in Approach 1
2. Validate schema compatibility with Approach 2
3. Identify "dirty" state (inconsistent, orphaned data)
4. Run test migration on 10% sample dataset

### Dual-Write Data Consistency
- All sandbox state written to both systems in real-time
- Async reconciliation job (every 5 mins) detects divergence
- Alert on >0.1% mismatch rate
- **Fallback:** Replay Approach 1 writes to Approach 2 if lag detected

### Validation Queries
```sql
-- Weekly check during Phase 1-2
SELECT COUNT(*) FROM service_layer.sandboxes
WHERE id NOT IN (SELECT id FROM simple_mcp.sandboxes);

-- Identify data age difference
SELECT
  AVG(EXTRACT(EPOCH FROM
    (service_layer.updated_at - simple_mcp.updated_at)))
  as avg_lag_seconds
FROM service_layer.sandboxes s
JOIN simple_mcp.sandboxes m ON s.id = m.id;
```

---

## 4. Backward Compatibility During Migration

### API Contract Stability
- Both Approach 1 & 2 expose identical REST/gRPC APIs
- No client-side code changes needed
- Internal routing layer (feature flags) switches backend

### Distributed Lock Compatibility
- Simple MCP uses memory-based locks (single instance)
- Service Layer uses Redis locks (distributed)
- **Wrapper:** Abstract lock interface, switch on feature flag
  ```python
  lock = get_lock_strategy(use_service_layer_flags):
    if use_service_layer_flags:
      return RedisDistributedLock(sandbox_id)
    else:
      return InMemoryLock(sandbox_id)
  ```

### Schema Versioning
- Approach 2 schema includes version field: `sandbox.schema_version`
- Supports multiple concurrent schema versions during migration
- Old client requests routed to Approach 1 until fully deprecated

---

## 5. Rollback Strategies

### Immediate Rollback (Same-Day Incident)
```
IF error_rate(service_layer) > 5%:
  Set feature_flag: sandbox.routing.use_service_layer = FALSE
  Revert all reads to Approach 1 (within 30 seconds)
  Keep writes to both systems (prevents data loss)
  Alert: "Rolled back to Approach 1"
```
- No user-visible downtime (automatic)
- Data consistency maintained via dual-write fallback

### Partial Rollback (Phase-Specific)
- Revert specific operations without full rollback
  ```
  sandbox.routing.create_sandbox_use_service_layer = FALSE
  sandbox.routing.update_sandbox_use_service_layer = TRUE
  sandbox.routing.delete_sandbox_use_service_layer = FALSE
  ```
- Isolate problematic operations while keeping stable ones

### Data Recovery (Post-Incident)
1. Approach 1 remains source-of-truth during migration
2. Sync Approach 2 from Approach 1 using CDC (Change Data Capture)
3. Validate consistency checks before resuming migration
4. **Timeline:** Recovery < 4 hours

### Kill-Switch Testing
- Weekly chaos test: flip feature flag on/off every 30 seconds
- Ensures no locks, session issues, or resource leaks
- Validates rollback path before production incident

---

## 6. Monitoring & Success Metrics

**Phase 1-2 Thresholds:**
- Dual-write latency delta: < 100ms acceptable
- Data sync lag: < 5 minutes
- Inconsistency rate: < 0.01%

**Phase 3 (Cutover):**
- P99 latency: ≤ previous Approach 1 latency
- Error rate: ≤ 0.1%
- Distributed lock acquisition time: ≤ 50ms

---

## 7. Risk Mitigations

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Lost writes during cutover | Dual-write with async validation | Backend |
| Lock deadlocks (service layer) | Weekly chaos tests, timeout configs | DevOps |
| Schema divergence | Weekly validation queries, CDC-based sync | QA |
| High latency (pooling overhead) | Performance benchmarks before Phase 3 | Backend |
| Clients caching old endpoints | Graceful deprecation window (4 weeks) | API |

---

## Timeline & Rollout

| Phase | Duration | Go/No-Go | Rollback Window |
|-------|----------|----------|-----------------|
| Shadow Mode | 1 week | Data consistency checks | Immediate |
| Dual Write | 1 week | Error rate < 0.5% | Immediate |
| Dual Read | 1 week | P99 latency parity | Immediate |
| Cutover | 1 day | Golden metrics met | 2 weeks (hot backup) |
| Deprecate Approach 1 | 4 weeks | No active clients | N/A |

---

## Key Sources

- **AWS Database Modernizer Workshop** (Nov 2024): Feature flag + dual-write patterns
- **LaunchDarkly / DevCycle** (2024): Gradual rollout, canary deployments, percentage-based flags
- **Nearform / Formidable**: Distributed lock state machines, transaction coordination
- **AWS Architecture Blog**: Real-time data sync, event-driven reconciliation

---

## Unresolved Questions

1. **Lock reuse during phase transitions:** How to handle sandbox IDs with existing in-memory locks switching to distributed locks?
2. **Cascade failure mode:** If Redis fails, does lock acquisition fall back to in-memory or fail fast?
3. **Pool sizing heuristic:** What's the optimal connection pool size for Approach 2 (depends on concurrency model)?

